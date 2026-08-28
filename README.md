# Openwheel Design

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/Version-1.0.0-orange?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/Tests-112%20passed-brightgreen?style=for-the-badge" alt="Tests">
</p>

> Formula Student arac tasarim ve analiz kutuphanesi — CLI, Python API ve PySide6 masaustu arayuzu

---

## Proje Istatistikleri

| | |
|:---|:---|
| **Moduller** | 15 analiz + 4 simulasyon |
| **Fonksiyonlar** | 340 |
| **Testler** | 112 |
| **Kaynak Kodu** | ~7,700 satir |
| **Python** | 3.8+ |

---

## Hizli Baslangic

### Kurulum

```bash
pip install git+https://github.com/ye5il/openwheel_design.git
```

Simulasyon motorlari (panel metodu, FEM, titresim) icin:

```bash
pip install "openwheel_design[sim] @ git+https://github.com/ye5il/openwheel_design.git"
```

Masaustu arayuzu icin:

```bash
pip install "openwheel_design[gui,sim] @ git+https://github.com/ye5il/openwheel_design.git"
```

### Masaustu Arayuzu (GUI)

Blueprint temali, Office tarzinda Ribbon bar navigasyonlu PySide6 masaustu uygulamasi.
12 analiz sekmesi: Ozet Panosu, Sasi, Motor, Suspansiyon, Aerodinamik, Lastik, Dinamik, Fren, Puanlama, Sasi FEM, Kanat Profili, Titresim.

```bash
openwheel-gui
```

veya:

```bash
python -m openwheel_design.gui.main_window
```

Windows'ta depo kokunden:

```
run_gui.bat
```

Arayuz ozellikleri:
- Her sekme icin girdi formu + canli grafik + sonuc paneli
- Arac profili JSON olarak kaydet/yukle — sekmeler arasi paylasimli
- Blueprint + Material Dark tema (koyu lacivert, teknik cizim estetiginde)
- matplotlib gomulu grafikler

### Python ile Kullanim

```python
from openwheel_design.modules.chassis import analyze_weight
from openwheel_design.modules.aerodynamics import calculate_downforce
from openwheel_design.modules.engine import get_engine

# Sasi agirlik analizi
result = analyze_weight([(25.4, 1.6, 5000)], material="4130")
print(f"Agirlik: {result['total_weight']:.2f} kg")

# Motor secimi
engine = get_engine("Honda_CBR600RR")
print(f"Motor: {engine['name']} ({engine['power_hp']} HP)")

# Downforce hesabi
downforce = calculate_downforce(CL=2.0, area_m2=1.2, speed_kmh=80)
print(f"Downforce: {downforce:.0f} N")
```

### CLI ile Kullanim

```bash
# Sasi analizi
openwheel chassis analyze --tube-od 25.4 --wall 1.6 --length 5000

# Motor listesi
openwheel engine list --common

# Aero analiz
openwheel aero downforce --CL 2.0 --speed 80

# FS uyumluluk kontrolu
openwheel fs-check --weight 200 --length 2000 --width 1150
```

---

## Analiz Modulleri

| Modul | Aciklama |
|-------|----------|
| `chassis` | Boru govde analizi, malzeme secimi, agirlik, kesit modulu, FS kural uygunlugu |
| `engine` | Motor veritabani (8 motor), restriktor analizi, guc/agirlik, 0-100 tahmini |
| `suspension` | Ackermann geometrisi, rol merkezi, anlik merkez, camber/toe, ARB |
| `brakes` | Fren kuvveti, pedal seyri, on/arka dagilim, termal analiz |
| `aerodynamics` | Downforce, drag, kanat analizi, konfigurasyon karsilastirmasi |
| `tires` | Soguk basinc tahmini, traksiyon cemberi, Pacejka modeli |
| `dynamics` | Yuk transferi (yanal/boyuna), kose yukleri, agirlik dagilimi, understeer |
| `scoring` | FSAE dinamik etkinlik puanlama (ivmelenme, skidpad, otokros, dayaniklilik) |
| `transmission` | Vites oranlari, diferansiyel, tahrik mili |
| `fuel` | Yakit tuketimi analizi |
| `data_log` | Telemetri, CAN mesaj ayristirma, sensor verisi |
| `lap_sim` | Enerji tuketimi, tur simulasyonu |
| `reporting` | Rapor olusturma |
| `ev_system` | Elektrikli tahrik, batarya boyutlandirma |

## Simulasyon Motorlari

`numpy` ve `scipy` gerektiren dort ozel simulasyon modulu:

| Motor | Dosya | Aciklama |
|-------|-------|----------|
| **2D Panel Metodu** | `simulation/panel_2d.py` | Hess-Smith panel metodu ile NACA profil analizi. CL, Cp dagilimi, surtunme suruklemesi (Thwaites). |
| **Sasi FEM** | `simulation/frame_fem.py` | 3D kiris elemani direkt rijitlik yontemi. Burulma rijitligi (Nm/derece), gerilme analizi. |
| **Ceyrek-Arac** | `simulation/quarter_car.py` | 2-DOF yay-kutle-sonumleyici. Frekans tepkisi, zaman domeni, dogal frekanslar. |
| **QSS Tur Sim** | `simulation/lap_qss.py` | Quasi-steady-state tur simulasyonu. GG-V zarfi, hiz profili, sektor sureleri. |

---

## Formula Student Destegi

- Motor deplasman limiti (maks 710 cc)
- Intake restrictor (maks 20 mm) — tikali akis modeli
- Yakit tanki (maks 10 L)
- EV voltaj limitleri (maks 600 V)
- Rollbar mukavemet kontrolu
- Cockpit opening kontrolu
- Resmi FSAE puanlama formuleri

---

## Gelistirme

```bash
git clone https://github.com/ye5il/openwheel_design.git
cd openwheel_design
pip install -e ".[dev,sim,gui]"
```

Testleri calistirmak icin:

```bash
python -m pytest tests -q
```

---

## Lisans

MIT License
