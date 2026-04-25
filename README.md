# 🚗 Openwheel Design

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/Version-1.0.0-orange?style=for-the-badge" alt="Version">
</p>

> Formula Student araç tasarım ve analiz kütüphanesi

---

## 📊 Proje İstatistikleri

| | |
|:---:|:---:|
| **📦 Modüller** | 15 |
| **⚡ Fonksiyonlar** | 250+ |
| **🧪 Testler** | 30+ |
| **📝 Satır Kod** | 8,500+ |
| **🐍 Python Versiyon** | 3.8+ |
| **📁 Paket Boyutu** | ~90 KB |

---

## 🚀 Hızlı Başlangıç

### Kurulum

```bash
pip install git+https://github.com/ye5il/openwheel_design.git
```

### Python ile Kullanım

```python
import sys
sys.path.insert(0, '/path/to/openwheel_design/src')

from openwheel_design.modules.chassis import analyze_weight
from openwheel_design.modules.aerodynamics import calculate_downforce
from openwheel_design.modules.engine import get_engine
from openwheel_design.modules.tires import check_tire_temperature

# Şasi ağırlık analizi
result = analyze_weight([(25.4, 1.6, 5000)], material="4130")
print(f"Ağırlık: {result['total_weight']:.2f} kg")  # Output: 4.70 kg

# Motor seçimi
engine = get_engine("Honda CBR600RR")
print(f"Motor: {engine['name']} ({engine['power_hp']} HP)")

# Downforce hesabı
downforce = calculate_downforce(CL=2.0, area_m2=1.2, speed_kmh=80)
print(f"Downforce: {downforce:.0f} N")  # Output: 726 N

# Lastik sıcaklık kontrolü
result = check_tire_temperature(95, "medium")
print(f"Lastik durumu: {result['status']}")  # Output: optimal
```

### CLI ile Kullanım

```bash
# Şasi analizi
python -m openwheel_design chassis analyze --tube-od 25.4 --wall 1.6 --length 5000

# Motor listesi
python -m openwheel_design engine list --common

# Aero analiz
python -m openwheel_design aero downforce --CL 2.0 --speed 80

# FS uyumluluk kontrolü
python -m openwheel_design fs-check --weight 200 --length 2000 --width 1150
```

---

## 📦 Mevcut Modüller

| Modül | Fonksiyonlar | Açıklama |
|-------|-------------|----------|
| `chassis` | 30+ | Şasi tasarım, ağırlık, malzeme analizi |
| `engine` | 25+ | Motor veritabanı (8 motor), performans |
| `suspension` | 20 | Camber, toe, Ackermann, ARB |
| `brakes` | 14 | Bias, termal, boyutlandırma |
| `aerodynamics` | 16 | Downforce, drag, kanat |
| `tires` | 12 | Sıcaklık, basınç, slip angle |
| `dynamics` | 10 | Yük transferi, understeer/oversteer |
| `transmission` | 12 | Vites oranları, diferansiyel |
| `scoring` | 12 | FSAE puanlama sistemi |
| `fuel` | 8 | Yakıt tüketimi |
| `data_log` | 20+ | Telemetri, CAN parsing |
| `lap_sim` | 15 | Enerji hesabı, lap simülasyonu |
| `reporting` | 15 | Raporlama |
| `ev_system` | 12 | Elektrikli motor, batarya |

---

## 🔬 Örnek Hesaplamalar

### Aerodinamik
```python
# Downforce: L = ½ρv²ACl
# 80 km/h → 726 N, 120 km/h → 1633 N
```

### Süspansiyon
```python
# Wheel rate: WR = SR × MR²
# 20 N/mm × 0.75² = 11.2 N/mm
```

### Dinamik
```python
# Yük transferi: LTR = m·a·h/T
# 200 kg × 1.8g × 280mm / 1200mm = 824 N
```

---

## 🏁 Formula Student Desteği

- ✅ FS weight limit kontrolü (min 180 kg)
- ✅ FS boyut kontrolü (max 2100×1200 mm)
- ✅ Motor deplasman limiti (max 710 cc)
- ✅ Intake restrictor (max 20 mm)
- ✅ Yakıt tankı (max 10 L)
- ✅ Rollbar spec
- ✅ Cockpit opening
- ✅ Puanlama sistemi

---

## 📋 Gereksinimler

- Python 3.8+
- No external dependencies (pure Python)

---

## 📄 Lisans

MIT License - Detaylı bilgi için [LICENSE](LICENSE) dosyasına bakınız.

---

## 🤝 Katkıda Bulunma

GitHub Issues veya Pull Request ile katkıda bulunabilirsiniz.

---

<p align="center">
  <a href="https://github.com/ye5il/openwheel_design">
    <img src="https://img.shields.io/github/stars/ye5il/openwheel_design?style=social" alt="Stars">
  </a>
  <a href="https://github.com/ye5il/openwheel_design">
    <img src="https://img.shields.io/github/forks/ye5il/openwheel_design?style=social" alt="Forks">
  </a>
  <a href="https://github.com/ye5il/openwheel_design/issues">
    <img src="https://img.shields.io/github/issues/ye5il/openwheel_design?style=social" alt="Issues">
  </a>
</p>