#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
from gi.repository import GObject
from gi.repository import GLib
import sys

def _(message): return GLib.dgettext(None, message)

class TextureTools (Gimp.PlugIn):
    def do_query_procedures(self):
        return [ 
            "texture-normal-map", 
            "texture-ambient-occlusion", 
            "texture-metallic-map"
        ]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run, None)
        procedure.set_image_types("RGB*, GRAY*")
        procedure.set_sensitivity_mask (Gimp.ProcedureSensitivityMask.DRAWABLE)
        
        titles = {
            "texture-normal-map": _("Normal Mapa (PBR)"),
            "texture-ambient-occlusion": _("Ambient Occlusion (PBR)"),
            "texture-metallic-map": _("Metallic Mapa (PBR)")
        }
        
        procedure.set_menu_label(titles.get(name, _("Tekstury")))
        procedure.add_menu_path('<Image>/Filters/Tekstury/')

        # sila: 10.0 to dobra baza dla detali beczki
        procedure.add_double_argument("sila", _("Natężenie"), _("Moc efektu"), 0.0, 100.0, 10.0, GObject.ParamFlags.READWRITE)
        procedure.add_boolean_argument("invert-y", _("Odwróć efekt / Y"), _("Normal: DirectX. AO/Metal: Inwersja"), False, GObject.ParamFlags.READWRITE)

        return procedure

    def run(self, procedure, run_mode, image, drawables, config, run_data):
        if len(drawables) != 1:
            return procedure.new_return_values(Gimp.PDBStatusType.CALLING_ERROR, GLib.Error())
        
        drawable = drawables[0]

        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init(procedure.get_name())
            dialog = GimpUi.ProcedureDialog.new(procedure, config, _("Generator Tekstur PBR"))
            dialog.get_widget("sila", GimpUi.ScaleEntry) 
            dialog.fill(None)
            if not dialog.run():
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())

        sila = config.get_property("sila")
        invert_y = config.get_property("invert-y")
        proc_name = procedure.get_name()

        Gegl.init(None)
        shadow_buffer = drawable.get_shadow_buffer()
        graph = Gegl.Node()
        
        source = graph.create_child("gegl:buffer-source")
        source.set_property("buffer", drawable.get_buffer())
        last_node = source

        # --- LOGIKA NORMAL MAPY ---
        if proc_name == "texture-normal-map":
            # Definiujemy początek potoku
            current_node = last_node

            if invert_y:
                # Zamieniamy miejscami czarny i biały punkt na wejściowej teksturze (negatyw wysokości)
                # To podejście jest w 100% stabilne w GIMP 3.2 i nie wysypie potoku
                height_invert = graph.create_child("gegl:levels")
                height_invert.set_property("in-low", 0.0)
                height_invert.set_property("in-high", 1.0)
                height_invert.set_property("out-low", 1.0)  # Czarny staje się biały (wklęsłe staje się wypukłe)
                height_invert.set_property("out-high", 0.0) # Biały staje się czarny
                
                current_node.link(height_invert)
                current_node = height_invert

            # Teraz bezpiecznie nakładamy rozmycie na (opcjonalnie odwróconą) mapę wysokości
            blur = graph.create_child("gegl:gaussian-blur")
            blur.set_property("std-dev", 1.5)
            
            # Generujemy końcową normalkę. Dostanie ona perfekcyjnie przygotowany sygnał.
            norm = graph.create_child("gegl:normal-map")
            norm.set_property("scale", sila)
            
            current_node.link(blur)
            blur.link(norm)
            
            # Przekazujemy gotową, błękitną mapę normalnych do zapisu
            last_node = norm

        # --- LOGIKA AMBIENT OCCLUSION ---
        elif proc_name == "texture-ambient-occlusion":
            mono = graph.create_child("gegl:mono-mixer")
            ao = graph.create_child("gegl:high-pass")
            ao.set_property("std-dev", sila)
            
            levels = graph.create_child("gegl:levels")
            
            if not invert_y:
                levels.set_property("out-low", -2.0 + (sila / 10.0))
                levels.set_property("out-high", 1.0)
            else:
                # Naprawa błędu wartości: wartości niskie i wysokie muszą zachować strukturę tonalną
                levels.set_property("out-low", 1.0)
                levels.set_property("out-high", Mathf.Clamp(-2.0 + (sila / 10.0), -2.0, 0.9))

            last_node.link(mono)
            mono.link(ao)
            ao.link(levels)
            last_node = levels

        # --- LOGIKA METALLIC ---
        elif proc_name == "texture-metallic-map":
            mono = graph.create_child("gegl:mono-mixer")
            contrast = graph.create_child("gegl:exposure")
            contrast.set_property("exposure", sila / 5.0)
            contrast.set_property("black-level", 0.4)
            
            last_node.link(mono)
            mono.link(contrast)
            last_node = contrast
            
            if invert_y:
                # Zamiast gegl:invert-gamma, który blokuje bufor przy braku zdefiniowanego profilu ICC,
                # stosujemy niezawodny, czysty matematycznie linear-invert
                inv = graph.create_child("gegl:invert-linear")
                last_node.link(inv)
                last_node = inv

        # --- WYPROWADZENIE WYNIKU ---
        output = graph.create_child("gegl:write-buffer")
        output.set_property("buffer", shadow_buffer)
        last_node.link(output)
        output.process()

        shadow_buffer.flush()
        drawable.merge_shadow(True)
        drawable.update(0, 0, drawable.get_width(), drawable.get_height())
        Gimp.displays_flush()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

Gimp.main(TextureTools.__gtype__, sys.argv)