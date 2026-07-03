# GIMP_Texture_plugin
Texture plugin for GIMP 3.2+
# PBR Texture Tools for GIMP 3.2+

Zestaw profesjonalnych, zautomatyzowanych narzędzi deweloperskich (wtyczek) dla programu **GIMP 3.2+** napisanych w Pythonie 3 z wykorzystaniem natywnego silnika graficznego **GEGL**. Wtyczki pozwalają na błyskawiczne generowanie podstawowych map tekstur proceduralnych na potrzeby potoków PBR (Physically Based Rendering) bezpośrednio z map albedo (Base Color).

Projekt powstał z myślą o niezależnych twórcach gier (m.in. do projektów w silniku Unity 3D) oraz grafikach 3D szukających darmowej i szybkiej alternatywy dla ciężkiego oprogramowania teksturującego.

## 🚀 Funkcje zestawu

Wtyczka rejestruje w menu GIMPa trzy niezależne procedury przetwarzania obrazu:

1. **Normal Mapa (PBR)** – Generuje mapę wektorów normalnych z automatycznym filtrowaniem szumów za pomocą rozmycia Gaussa. Posiada kluczową opcję **Invert Y** (Inwersja wysokości) realizowaną na poziomie potoku tonalnego (Heightmap), co pozwala na płynną zmianę polaryzacji rzeźby terenu (wgłębienia stają się wypukłościami i na odwrót). Zapobiega to powstawaniu błędów przesunięcia kanałów RGB w przestrzeni wektorowej.
2. **Ambient Occlusion (PBR)** – Wylicza mapę zacienienia szczelinowego na podstawie mikrokontrastu (filtr High-Pass), dając głębię detali w zagłębieniach struktur.
3. **Metallic Mapa (PBR)** – Izoluje i wzmacnia skrajne wartości luminancji, przygotowując czystą mapę metaliczności z opcjonalną, bezwzględną inwersją liniową.

## 🛠️ Architektura i Bezpieczeństwo (GIMP 3.2)

Skrypt został w pełni dostosowany do rygorystycznych wymagań **GIMP 3.2** oraz architektury **GEGL 0.4**:
* **Brak przestarzałych węzłów:** Kod całkowicie rezygnuje z wyciętego w wersji 3.2 węzła `gegl:math` oraz kapryśnych struktur `Gegl.Matrix3`, które potrafiły bezgłośnie zrywać potok przetwarzania danych barwnych w Pythonie.
* **Pancerne przetwarzanie potokowe:** Operacja inwersji wysokości w Normal Mapie została przeniesiona na sam koniec grafu (przed narodzinami wektorów), dzięki czemu tło zachowuje idealny błękitny profil PBR ($R=0.5, G=0.5, B=1.0$), a modyfikowana jest wyłącznie interpretacja rzeźby.

## ⚙️ Instalacja

Wtyczka wymaga zainstalowanego programu GIMP w wersji **3.2** lub nowszej, wspierającej środowisko Python 3 (PyGObject).

Wtyczka musi zostać wklejona do folderu:

Linux:
```bash
mkdir -p ~/.config/GIMP/3.2/plug-ins/texture_tools && \
cp texture_tools.py ~/.config/GIMP/3.2/plug-ins/texture_tools/texture_tools.py && \
chmod +x ~/.config/GIMP/3.2/plug-ins/texture_tools/texture_tools.py
```
Windows:
C:\Users\<Twoja_Nazwa_Użytkownika>\AppData\Roaming\GIMP\3.2\plug-ins\
...\GIMP\3.2\plug-ins\texture_tools\texture_tools.py

Struktura plików:
~/.config/GIMP/3.2/plug-ins/
└── texture_tools/
    └── texture_tools.py
