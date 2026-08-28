# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Ne olduğu

Formula Student araç tasarım/analiz kütüphanesi. Saf Python, harici bağımlılık yok. Proje dili Türkçe (README, docstring'ler), kod ve API isimleri İngilizce.

## Kritik: depo iki kopya içeriyor

15 modülün tamamı (`chassis/`, `engine/`, `utils/`, …) depoda **iki yerde, byte-identical** duruyor:

- `src/openwheel_design/modules/<modül>/` — paketlenen kopya (`pyproject.toml`: `packages.find where=["src"]`)
- `<modül>/` — depo kökündeki kopya (54 dosya)

`cli.py` de hem kökte hem `src/openwheel_design/cli.py` olarak duruyor, ikisi aynı.

**Bir modülü düzenlerken iki kopyayı da güncelle, yoksa kopyalar birbirinden ayrışır.** Yeni kod yazarken `src/` altındakini kaynak kabul et.

Depo kökünde ayrıca bir `__init__.py` var — kök kopyalardan (`chassis`, `engine`) import edip kökteki `openwheel_design` adını `src/` dışında bir ikinci paket gibi kullanıma açıyor. Bu dosya `src/openwheel_design/__init__.py`'den farklı; ikisi ayrı `__all__` listesi taşıyor.

## Kritik: import şeması paketi bozuyor

`src/openwheel_design/modules/**` içindeki dosyalar göreli import yerine top-level mutlak import kullanıyor (41 satır):

```python
from utils.constants import GRAVITY          # chassis/materials.py:1
from chassis.materials import get_material   # chassis/analyses.py:1
```

Bu isimler kurulu pakette yok. Sonuç:

- `pip install .` sonrası `import openwheel_design` → `ModuleNotFoundError: No module named 'utils'`
- `openwheel` konsol komutu ve `python -m openwheel_design` kurulumdan sonra aynı şekilde patlıyor

Kod **yalnızca depo kökü `sys.path`'te iken** çalışıyor; `utils` o zaman kökteki kopyadan çözülüyor. Yani "çalışıyor" görüntüsü tamamen kök kopyaya bağlı.

Bu düzeltilirse (`from ..utils.constants import GRAVITY`, `from .materials import ...`) kök kopyalar silinebilir ve paket gerçekten kurulabilir hale gelir.

## Komutlar

Hepsi depo kökünden çalıştırılır ve `PYTHONPATH`'te hem `.` hem `src` gerektirir.

### PowerShell (Windows — bu deponun birincil ortamı)

```powershell
# CLI
$env:PYTHONPATH=".;src"; python -m openwheel_design chassis analyze --tube-od 25.4 --wall 1.6 --length 5000
$env:PYTHONPATH=".;src"; python -m openwheel_design engine list --common
$env:PYTHONPATH=".;src"; python -m openwheel_design fs-check --weight 200 --length 2000 --width 1150
```

```powershell
# Tüm testler (pytest kurulu değil; önce: pip install pytest)
$env:PYTHONPATH=".;src"; python -m pytest tests -q
```

```powershell
# Tek test
$env:PYTHONPATH=".;src"; python -m pytest tests/test_modules.py::test_chassis -q
```

### Bash / Git Bash

```bash
PYTHONPATH=".;src" python -m openwheel_design chassis analyze --tube-od 25.4 --wall 1.6 --length 5000
PYTHONPATH=".;src" python -m pytest tests -q
PYTHONPATH=".;src" python -m pytest tests/test_modules.py::test_chassis -q
```

### Örnek tam araç analizi

```bash
python example_vehicle/analyze.py
```

Bu script `sys.path.insert(0, '..')` ile kök kopyaya bağımlı; `example_vehicle/` dizininden çalıştırılmalı.

`pyproject.toml` `black` ve `ruff`'ı (line-length 88, py38) opsiyonel `dev` bağımlılığı olarak tanımlıyor ama ikisi de kurulu değil ve CI yok.

## Testler

Tek test dosyası: `tests/test_modules.py` — 6 smoke test (import, chassis, engine, aerodynamics, tires, dynamics). Sadece temel fonksiyon çağrısı ve çıktı varlığı kontrol ediliyor; edge case, hata yolu veya hesap doğruluğu testi yok. Testler de `src/` altından import ediyor (`from openwheel_design.modules.chassis import ...`), çalışması `PYTHONPATH`'e bağlı.

## Mimari

### Modül düzeni

Her modül bir paket: alt dosyalar konuya göre bölünmüş, `__init__.py` hepsini tek düzeye re-export ediyor. Tipik biçim:

```
chassis/
  __init__.py       # materials/geometry/constraints/analyses/safety'den re-export
  materials.py      # malzeme tablosu + ağırlık
  geometry.py       # boru spec parse, boyut kontrolü
  constraints.py    # FS kural limitleri
  analyses.py       # yukarıdakileri birleştiren üst seviye analizler
  safety.py
```

`ev_system` bu düzenin tek istisnası: alt dosyaları yok, her şey tek `__init__.py` içinde.

Üst seviye `src/openwheel_design/__init__.py` her modülden seçili birkaç fonksiyonu paket köküne çıkarıyor (`analyze_weight`, `calculate_downforce`, `get_engine` …) ve `__all__` ile listeliyor.

### Fonksiyon sözleşmesi

Kod tabanı boyunca tutarlı, ama hiçbir yerde yazılı değil:

- Fonksiyonlar **dict döndürür**, anahtar isimlerinde birim son eki taşır: `load_transfer_N`, `cog_height_mm`, `power_to_weight_kW_per_kg`, `stiffness_N_mm_per_deg`
- Değerler dönüşte `round()` edilir
- Kural/limit kontrolleri `compliant` veya `passed` boolean'ı taşır; birleşik kontroller `{"passed": bool, "checks": {...}}` döndürür
- Yorum niteliğindeki alanlar serbest metin: `interpretation`, `effect`, `recommendation`, `note`
- **Docstring yok, type hint yok** (modüllerde sıfır). `pyproject.toml` `py.typed` beyan ediyor ama dosya mevcut değil.

### Birim konvansiyonu

Girdi/çıktıda mm, km/h, bar, hp, kg, N kullanılır; hesap içinde SI'ya çevrilir (`speed_kmh / 3.6`, `mm / 1000`). Dönüşüm yardımcıları `utils/units.py` içinde (`hp_to_kW`, `bar_to_psi`, …) ama modüller çoğunlukla bunları kullanmayıp dönüşümü satır içi yapıyor.

Fiziksel sabitler ve FS kural limitleri `utils/constants.py` içinde tek noktada (`GRAVITY`, `AIR_DENSITY`, malzeme dayanımları, `FS_MIN_WEIGHT`, `FS_MAX_DISPLACEMENT`, `FS_RESTRICTOR`). Yeni sabit eklerken buraya ekle, modül içine gömme.

### CLI

`cli.py` argparse ile `<modül> <komut>` alt-komut yapısı kuruyor (`chassis analyze`, `engine list`, `aero downforce`, `fs-check`). Her komut için `cmd_<modül>_<eylem>(args)` biçiminde bir handler var; handler modül fonksiyonunu çağırıp sonucu `print` ediyor — dönüş değeri yok, formatlama handler içinde elle yapılıyor.

## Bilinen hatalı hesaplar

Bu fonksiyonlar sessizce yanlış sayı üretiyor. Bunlara dayanan yeni kod yazmadan veya çıktılarını doğru varsaymadan önce düzelt:

| Konum | Sorun |
|---|---|
| `aerodynamics/wings.py` | `calculate_wing_downforce` → `NameError`; `calculate_downforce`/`calculate_drag` import edilmemiş |
| `chassis/analyses.py` `calculate_section_modulus` | `pi/32` (polar moment) kullanılmış, eğilme için `pi/64` olmalı → sonuç 2× büyük |
| `chassis/analyses.py` `analyze_stress` | Malzemeden bağımsız hep `CHROMOLY_YIELD` (560 MPa); Al7075 için 2× iyimser |
| `dynamics/load_transfer.py` `calculate_wheel_loads` | Köşe yükleri toplamı araç ağırlığının 2 katı; yanal transfer akslara bölünmüyor |
| `scoring/events.py` | Skidpad formülü ters (en hızlı 3.5, en yavaş 75 puan); endurance formülü resmî değil; `MAX_POINTS` toplamı 975 (resmî 1000) |
| `engine/analyses.py` `calculate_0_100_estimation` | Vites oranı yok, motor torkunu doğrudan tekerlekte kullanıyor → 26 s; ayrıca `return`'den sonra ulaşılamaz kod bloğu |
| `engine/constraints.py` `calculate_restricted_power` | 20 mm restriktör için 119 hp → 20 hp (%83 kayıp); gerçekçi değer ~%40 |
| `engine/cooling.py` `estimate_heat_rejection` | Isıyı mil gücünün %25'i alıyor; soğutucuya atılan ısı ≈ mil gücü mertebesinde |
| `lap_sim/simulation.py` | `estimate_energy_consumption` kW toplayıp kWh döndürüyor; `simulate_lap` içinde `lap_time = 60` sabit |
| `suspension/kinematics.py` | `calculate_camber_gain` / `calculate_instant_center` boyutsal olarak anlamsız; `calculate_roll_center` `track_width_mm`'i kullanmıyor |
| `suspension/geometry.py` `calculate_ackermann` | `R` ve `R+track` kullanıyor, `R∓track/2` olmalı |
| `tires/thermal_model.py` `estimate_cold_pressure` | Gauge basınca mutlak-sıcaklık yasası uygulanmış; +1.013 bar eklenmeli |

Ayrıca hesap yapıyormuş gibi görünüp yapmayan stub'lar var: `calculate_anti_dive`, `calculate_anti_squat`, `optimize_gear_ratios`, `parse_can_message`, `export_to_csv`, `check_pedal_travel`, `optimize_cost`, `RacingLineOptimizer.*`.

`engine/database.py` içinde `"Suzuki_S1000RR"` kaydı hatalı — S1000RR bir BMW motorudur.
