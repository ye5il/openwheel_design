# Openwheel Design Assistant — Proje Rehberi
> Formula Student odaklı Python mühendislik hesap kütüphanesi
> Durum: v1.0 analiz + geliştirme yol haritası

---
## İÇİNDEKİLER
1. Proje Yapısı (Mevcut)
2. Mevcut Modül Analizi
3. Bug ve Hata Tespitleri
4. Yeni Modüller — Tam Spesifikasyon
5. FS Kuralları — Mevcut vs Eksik Kapsam
6. CLI Genişletme
7. Öncelik ve Yol Haritası

---
## 1. PROJE YAPISI (MEVCUT)

```
openwheel/
├── __init__.py              # Ana paket; chassis + engine export
├── cli.py                   # Komut satırı arayüzü
│
├── chassis/
│   ├── __init__.py
│   ├── analyses.py          # analyze_weight, reverse_engineer, optimize_weight, analyze_stress
│   ├── constraints.py       # check_fs_compliance, FS_CONSTRAINTS
│   ├── geometry.py          # Tüp boyutları, monocoque kalınlıkları, FS boyut kontrolü
│   ├── materials.py         # Malzeme DB (4130, al7075, carbon_fiber), tüp ağırlık hesabı
│   └── safety.py            # Rollbar kuvveti, harness kuvveti, firewall specs
│
├── engine/
│   ├── __init__.py
│   ├── analyses.py          # analyze_engine, optimize_engine_choice, analyze_performance
│   ├── constraints.py       # check_displacement, check_restrictor, restricted_power
│   ├── cooling.py           # Isı reddi, radyatör boyutu, su pompası akışı
│   └── database.py          # 5 motor (hepsi 600cc motosiklet)
│
└── utils/
    ├── __init__.py
    ├── constants.py         # Fizik sabitleri, malzeme özellikleri, FS limitleri
    └── units.py             # Birim dönüşümleri (mm↔m, kg↔lb, hp↔kW, bar↔psi...)
```

### Mevcut Fonksiyon Envanteri

| Modül | Fonksiyon | Açıklama |
|---|---|---|
| chassis.analyses | `analyze_weight(tubes, material)` | Tüp listesinden toplam ağırlık |
| chassis.analyses | `reverse_engineer_weight(target_kg, material, od)` | Hedef ağırlık → tüp konfigürasyonları |
| chassis.analyses | `reverse_engineer_target(target_kg, material, category)` | Geniş arama; tüm OD+wall kombinasyonları |
| chassis.analyses | `analyze_stress(force_N, area_mm2)` | Basit gerilme analizi |
| chassis.analyses | `optimize_weight(target_kg)` | Çoklu malzeme optimizasyonu |
| chassis.constraints | `check_fs_compliance(weight, length, width, ...)` | FS kural uyum kontrolü |
| chassis.materials | `get_material(name)` | Malzeme özellik sözlüğü |
| chassis.materials | `calculate_tube_weight(od, wall, length, mat)` | Tek tüp ağırlık hesabı |
| chassis.safety | `calculate_rollbar_force(weight_kg, sf)` | Rollbar kuvveti (N) |
| chassis.safety | `calculate_harness_force(weight_kg, accel_g)` | Emniyet kemeri kuvveti |
| engine.database | `get_engine(name)` | Motor özellik sözlüğü |
| engine.database | `list_engines(common_only)` | Motor listesi |
| engine.database | `calculate_power_to_weight(engine, vehicle_kg)` | Güç/ağırlık oranı |
| engine.analyses | `analyze_engine(name, vehicle_kg)` | Motor analizi |
| engine.analyses | `optimize_engine_choice(vehicle_kg, target)` | Motor optimizasyonu |
| engine.analyses | `analyze_performance(name, kg, restrictor, ...)` | Performans + soğutma analizi |
| engine.analyses | `calculate_0_100_estimation(name, kg)` | 0-100 km/h tahmini (HATALI) |
| engine.cooling | `check_cooling_system(name, power_hp)` | Soğutma sistem özeti |
| engine.constraints | `estimate_power_with_restrictor(name, mm)` | Kısıtlayıcılı güç tahmini |

---
## 2. MEVCUT MODÜL ANALİZİ

### 2.1 chassis/

**Güçlü yönler:**
- Tüp ağırlık hesabı doğru; geometrik kesit alanı formülü tam
- Malzeme DB genişletilebilir yapıda
- FS kural kontrolü modüler; yeni kural eklemek kolay

**Zayıf yönler:**
- Süspansiyon, fren, aerodinamik, lastik — tamamen yok
- `analyze_stress` tek eksenli basit gerilme; çok eksenli yük yok
- `optimize_cost` fonksiyonu stub; çalışmıyor

### 2.2 engine/

**Güçlü yönler:**
- Soğutma sistemi hesabı iyi yapılandırılmış (UA değeri, radyatör alanı)
- Restrictor power loss modeli var

**Zayıf yönler:**
- Sadece 5 motor, hepsi 600cc, sadece motosiklet
- Formula Vee motoru (VW 1200cc) yok
- 1000cc sınıfı (R1, ZX10R, S1000RR) yok
- Elektrikli FS motoru/akü modeli yok
- `calculate_0_100_estimation` fizik formülü yanlış

### 2.3 utils/

**Güçlü yönler:**
- Birim dönüşümleri eksiksiz
- Sabitler merkezi; değiştirmek kolay

**Zayıf yönler:**
- `utils/__init__.py`'de `'4130_YIELD'` string olarak export edilmiş ama Python değişken adı rakamla başlayamaz — bu satır import sırasında `SyntaxError` verir
- Hiçbir constant için kaynak referansı yok

---
## 3. BUG VE HATA TESPİTLERİ

### Bug 1 — `calculate_0_100_estimation` (engine/analyses.py:70) 🔴 KRİTİK
```python
# MEVCUT (yanlış):
force_n = wheel_torque / 0.3          # sabit yarıçap; vitessiz
accel_ms2 = force_n / mass_kg
time_sec = 100 / (0.5 * accel_ms2) ** 0.5 / 3.6  # bu formül anlamlı değil

# DOĞRU yaklaşım — numerik integrasyon:
def calculate_0_100_estimation(engine_name, vehicle_weight_kg, gear_ratios=None):
    eng = get_engine(engine_name)
    v_target = 100 / 3.6   # m/s
    dt = 0.01              # zaman adımı
    v, t = 0, 0
    while v < v_target:
        rpm = v * 60 / (2 * pi * 0.254)   # R=254mm tekerlek
        torque = interpolate_torque(eng, rpm)
        F = torque / 0.254 * 0.85         # %85 aktarma verimi
        a = F / vehicle_weight_kg
        v += a * dt
        t += dt
    return round(t, 2)
```

### Bug 2 — `parse_tube_spec` length desteği yok (chassis/analyses.py:27) 🔴 KRİTİK
```python
# MEVCUT:
parsed = parse_tube_spec(tube_spec)
length = parsed.get("length", 1000)   # parse_tube_spec hiç length döndürmüyor!

# DÜZELTME — parse_tube_spec güncellenmeli:
def parse_tube_spec(spec):
    if isinstance(spec, tuple):
        od = spec[0]
        wall = spec[1]
        length = spec[2] if len(spec) > 2 else 1000   # ← ekle
    else:
        parts = spec.lower().replace("x", " ").split()
        od = float(parts[0])
        wall = float(parts[1]) if len(parts) > 1 else 1.6
        length = float(parts[2]) if len(parts) > 2 else 1000   # ← ekle
    return {"od": od, "wall": wall, "length": length}
```

### Bug 3 — Restrictor modeli çok kaba (engine/constraints.py:37) 🟡 ORTA
```python
# MEVCUT (basit oran):
const = (restrictor_mm / 20) ** 2
restricted = stock_power_hp * const

# DAHA DOĞRU — Orifice / Bernoulli denklemi:
# Q = Cd * A * sqrt(2 * dP / rho)
# A_restrictor = pi * (d/2)^2
# A_throttle_body = pi * (throttle_d/2)^2
# flow_ratio = (A_restrictor / A_throttle_body)^2
# power_ratio yaklaşımı:
def calculate_restricted_power(restrictor_mm, stock_power_hp, throttle_body_mm=44):
    import math
    Cd = 0.82   # discharge coefficient; tipik değer
    A_r = math.pi * (restrictor_mm / 2000) ** 2   # m²
    A_t = math.pi * (throttle_body_mm / 2000) ** 2
    flow_ratio = (Cd * A_r) / A_t
    # Güç ~ hava kütlesi akışı ile orantılı
    power_ratio = min(flow_ratio, 1.0)
    return stock_power_hp * power_ratio
```

### Bug 4 — `utils/__init__.py` geçersiz değişken adı export 🟡 ORTA
```python
# MEVCUT (çalışmaz):
__all__ = [..., '4130_YIELD', '4130_ULTIMATE', ...]

# DÜZELTME — constants.py'de rename et:
CHROMOLY_4130_YIELD = 560      # eski: CHROMOLY_YIELD (zaten var, ama export adı farklı)
CHROMOLY_4130_ULTIMATE = 620

# utils/__init__.py:
__all__ = [..., 'CHROMOLY_4130_YIELD', 'CHROMOLY_4130_ULTIMATE', ...]
```

### Bug 5 — `optimize_cost` stub; hiç çalışmıyor (chassis/analyses.py) 🟢 DÜŞÜK
```python
# MEVCUT — sabit string döndürüyor; parametre bağımsız:
def optimize_cost(target_performance, budget):
    return {"recommendation": "Use 4130 Chromeoly..."}

# YAPILMALI: malzeme fiyat DB ekle, bütçeye göre filtrele
```

---
## 4. YENİ MODÜLLER — TAM SPESİFİKASYON

### 4.1 `suspension/` — Süspansiyon Sistemi 🔴 KRİTİK

**Dosya yapısı:**
```
suspension/
├── __init__.py
├── geometry.py       # Camber, toe, caster, kingpin, Ackermann
├── kinematics.py     # Wishbone uzunlukları, IC noktası, roll center
├── spring_damper.py  # Wheel rate, motion ratio, yay seçimi
└── arb.py            # Anti-roll bar sertlik hesabı
```

**geometry.py — fonksiyonlar:**
```python
def check_camber(camber_deg):
    """
    Camber açısı FS pratiği kontrolü.
    Negatif = içe yatık (viraj tutunması için).
    Tipik: ön -2.0 ile -3.5°, arka -1.0 ile -2.0°
    """
    return {
        "value_deg": camber_deg,
        "sign": "negative (correct)" if camber_deg < 0 else "positive (unusual)",
        "in_typical_range": -3.5 <= camber_deg <= -1.0,
        "effect": "cornering grip ↑" if camber_deg < 0 else "straight grip ↑"
    }

def check_toe(toe_mm, axle="front"):
    """
    Toe-in (+) = stabilite ↑, hız ↓
    Toe-out (-) = çeviklik ↑, stabilite ↓
    Tipik FS ön: +0.5 ile +2mm, arka: 0 ile +2mm
    """

def check_caster(caster_deg):
    """
    Caster açısı = direksiyon dönüş ekseni eğimi.
    Yüksek caster → daha fazla geri bildirim + stabilite.
    Tipik FS: 3-8°
    """

def calculate_ackermann(wheelbase_mm, track_width_mm, turn_radius_mm):
    """
    İdeal Ackermann açısı: arctan(L/R)
    İç tekerlek farklı açı alır → sürtünme azalır
    """
    import math
    inner_angle = math.degrees(math.atan(wheelbase_mm / turn_radius_mm))
    outer_angle = math.degrees(math.atan(wheelbase_mm / (turn_radius_mm + track_width_mm)))
    return {
        "inner_angle_deg": round(inner_angle, 2),
        "outer_angle_deg": round(outer_angle, 2),
        "ackermann_percent": round((inner_angle - outer_angle) / inner_angle * 100, 1)
    }

def calculate_scrub_radius(kingpin_inclination_deg, caster_deg, wheel_offset_mm):
    """Dönüş ekseninin lastik temas noktasına yatay uzaklığı"""

def check_fs_suspension_geometry(camber, toe, caster, ride_height_mm):
    """Tüm geometri parametrelerini tek seferde kontrol et"""
```

**kinematics.py — fonksiyonlar:**
```python
def calculate_roll_center(upper_wishbone_length, lower_wishbone_length,
                          upper_angle_deg, lower_angle_deg, track_width_mm):
    """
    Anlık dönüş merkezi (IC) ve roll center yüksekliği hesabı.
    Yüksek RC → az yatış momentı, fazla camber değişimi.
    Düşük RC → daha fazla yatış, az camber değişimi.
    """

def calculate_camber_gain(upper_len, lower_len, ride_height_change_mm):
    """
    Süspansiyon sıkıştıkça camber değişimi (deg/mm).
    Negatif camber gain → viraj sıkışmasında camber kötüleşir.
    """

def calculate_instant_center(upper_wishbone, lower_wishbone):
    """Çizgisel kesişim noktası hesabı"""

def calculate_anti_dive(front_geometry, brake_bias_front):
    """
    Anti-dive % = Frenlemede ön çökme direnci.
    100% anti-dive = hiç çökmez (sürücü rahatsızlığı).
    Tipik FS: 20-40%
    """

def calculate_anti_squat(rear_geometry, weight_distribution_rear):
    """İvmelenmede arka kalkma direnci"""
```

**spring_damper.py — fonksiyonlar:**
```python
def calculate_motion_ratio(rocker_arm_length_in, rocker_arm_length_out):
    """
    MR = amortisör hareketi / tekerlek hareketi
    Tipik push-rod FS: 0.6 - 0.85
    """
    return rocker_arm_length_in / rocker_arm_length_out

def calculate_wheel_rate(spring_rate_N_mm, motion_ratio):
    """
    WR = SR × MR²
    Tekerlek oranı ≠ yay oranı!
    """
    return spring_rate_N_mm * (motion_ratio ** 2)

def calculate_natural_frequency(wheel_rate_N_mm, sprung_mass_kg):
    """
    fn = (1/2π) × √(WR/m)
    Tipik FS: ön 2-3 Hz, arka 2.5-3.5 Hz
    """
    import math
    wn = math.sqrt((wheel_rate_N_mm * 1000) / sprung_mass_kg)
    return wn / (2 * math.pi)

def calculate_critical_damping(wheel_rate_N_mm, sprung_mass_kg):
    """Cc = 2 × √(k × m)"""
    import math
    return 2 * math.sqrt(wheel_rate_N_mm * 1000 * sprung_mass_kg)

def select_spring(target_wheel_rate, motion_ratio, available_springs):
    """
    Hedef wheel rate'den gereken yay oranını hesapla:
    SR = WR / MR²
    """
    required_spring_rate = target_wheel_rate / (motion_ratio ** 2)
    return {
        "required_spring_rate_N_mm": round(required_spring_rate, 1),
        "motion_ratio": motion_ratio,
        "target_wheel_rate": target_wheel_rate
    }

def check_ride_height_range(min_travel_mm, max_travel_mm, ride_height_mm):
    """Süspansiyon seyahat aralığı vs ride height kontrolü"""
```

**arb.py — fonksiyonlar:**
```python
def calculate_arb_stiffness(bar_diameter_mm, bar_length_mm, arm_length_mm, material="steel"):
    """
    K_arb = G × J / (L × arm²)
    G = kayma modülü, J = polar atalet momenti
    """
    import math
    G = 80000 if material == "steel" else 27000   # MPa
    J = math.pi * (bar_diameter_mm ** 4) / 32    # mm⁴
    K = (G * J) / (bar_length_mm * arm_length_mm ** 2)
    return {
        "stiffness_N_mm_per_deg": round(K, 2),
        "bar_diameter_mm": bar_diameter_mm,
        "material": material
    }

def calculate_roll_stiffness(arb_stiffness, spring_stiffness, track_width_mm):
    """Toplam yatış sertliği = yay + ARB katkısı"""

def calculate_roll_gradient(total_roll_stiffness, sprung_weight_N, cog_height_mm, track_mm):
    """
    Roll gradient = derece / g (viraj yükü başına gövde açısı)
    Tipik FS hedef: < 1.5°/g
    """

def optimize_arb(front_roll_stiffness, rear_roll_stiffness, target_balance=0.55):
    """
    Ön/arka yatış sertliği dağılımı.
    target_balance = ön oranı (0.55 = %55 ön → hafif understeer)
    """
```

---

### 4.2 `brakes/` — Fren Sistemi 🔴 KRİTİK

**Dosya yapısı:**
```
brakes/
├── __init__.py
├── system.py     # Bias, ana silindir, pedal oranı
├── thermal.py    # Disk sıcaklık tahmini, soğutma
└── sizing.py     # Disk çapı, kalibri, balata alanı
```

**system.py — fonksiyonlar:**
```python
def calculate_brake_bias(front_weight_N, rear_weight_N,
                         decel_g, cog_height_mm, wheelbase_mm):
    """
    Dinamik yük transferinde gereken ön/arka fren oranı.
    Bias = ön fren kuvveti / toplam fren kuvveti
    Tipik FS: ön %60-70
    """
    weight_transfer = (decel_g * (front_weight_N + rear_weight_N) * cog_height_mm) / wheelbase_mm
    dynamic_front = front_weight_N + weight_transfer
    dynamic_rear = rear_weight_N - weight_transfer
    ideal_bias = dynamic_front / (dynamic_front + dynamic_rear)
    return {
        "ideal_front_bias": round(ideal_bias * 100, 1),
        "dynamic_front_N": round(dynamic_front, 0),
        "dynamic_rear_N": round(dynamic_rear, 0),
        "weight_transfer_N": round(weight_transfer, 0)
    }

def calculate_master_cylinder_size(caliper_piston_area_mm2, pedal_ratio,
                                   desired_pressure_bar, max_pedal_force_N=500):
    """
    P = F × pedal_ratio / MC_area
    MC_area = F × pedal_ratio / P
    Tipik MC çapı: 15.9mm (5/8") veya 19mm (3/4")
    """
    required_force = desired_pressure_bar * 100000 * caliper_piston_area_mm2 / 1e6
    mc_force = max_pedal_force_N * pedal_ratio
    pressure_bar = mc_force / (caliper_piston_area_mm2 / 1e6) / 100000
    return {
        "pressure_achievable_bar": round(pressure_bar, 1),
        "pedal_ratio": pedal_ratio,
        "max_pedal_force_N": max_pedal_force_N
    }

def calculate_brake_force(pressure_bar, caliper_piston_area_mm2,
                          friction_coeff, rotor_radius_mm, wheel_radius_mm):
    """
    F_brake = P × A_piston × μ_pad × (r_rotor / r_wheel)
    """
    piston_force = pressure_bar * 1e5 * caliper_piston_area_mm2 / 1e6
    clamp_force = piston_force * 2   # çift taraflı kalibri
    brake_torque = clamp_force * friction_coeff * (rotor_radius_mm / 1000)
    brake_force = brake_torque / (wheel_radius_mm / 1000)
    return {
        "brake_force_N": round(brake_force, 0),
        "brake_torque_Nm": round(brake_torque, 1),
        "decel_g_per_axle": round(brake_force / 2000, 3)   # 200kg araç varsayım
    }

def check_pedal_travel(mc_bore_mm, caliper_bore_mm, pad_clearance_mm=0.15):
    """Pedal seyahati ve sıvı hacmi kontrolü"""

def check_fs_brake_rules(has_two_independent_circuits, has_brake_light):
    """FS T11 fren kuralları: çift bağımsız devre zorunlu"""
```

**thermal.py — fonksiyonlar:**
```python
def estimate_disc_temperature(kinetic_energy_J, disc_mass_kg, num_discs=2,
                              specific_heat=500, initial_temp_C=20):
    """
    Q = m × c × ΔT → ΔT = Q / (m × c)
    Tüm kinetik enerji ısıya dönüşür varsayımı.
    Tipik FS fren noktasında: 200-400°C
    """
    heat_per_disc = kinetic_energy_J / num_discs
    delta_T = heat_per_disc / (disc_mass_kg * specific_heat)
    final_temp = initial_temp_C + delta_T
    return {
        "final_temp_C": round(final_temp, 0),
        "delta_T": round(delta_T, 0),
        "warning": final_temp > 700
    }

def calculate_cooling_airflow(disc_temp_C, ambient_temp_C, disc_area_m2,
                              convection_coeff=50):
    """Q = h × A × ΔT — konveksiyon soğutma gücü"""

def check_thermal_limit(disc_temp_C, disc_material="cast_iron"):
    """
    Malzeme sınırları:
    - Döküm demir: max 700°C
    - Karbon-seramik: max 1000°C
    """
    limits = {"cast_iron": 700, "carbon_ceramic": 1000, "steel": 650}
    limit = limits.get(disc_material, 700)
    return {
        "temp_C": disc_temp_C,
        "limit_C": limit,
        "safe": disc_temp_C < limit,
        "margin_C": limit - disc_temp_C
    }

def calculate_brake_energy(vehicle_mass_kg, speed_kmh, target_speed_kmh=0):
    """KE = ½mv² — frenlemede emilmesi gereken kinetik enerji"""
    v1 = speed_kmh / 3.6
    v2 = target_speed_kmh / 3.6
    return 0.5 * vehicle_mass_kg * (v1**2 - v2**2)
```

**sizing.py — fonksiyonlar:**
```python
def size_rotor(vehicle_mass_kg, max_decel_g, max_speed_kmh,
               wheel_diameter_mm=508):
    """
    Minimum rotor çapı önerisi.
    Tipik FS: ∅200-280mm
    """

def select_caliper(required_clamp_force_N, available_calipers=None):
    """
    Gerekli sıkma kuvvetine göre kalibri seçimi.
    Ön: 4-6 piston, arka: 2-4 piston
    """

def calculate_pad_area(required_brake_force_N, max_pad_pressure_MPa=10):
    """Gereken balata temas alanı (mm²)"""

COMMON_CALIPERS_FS = {
    "Wilwood_Dynalite": {"pistons": 4, "piston_area_mm2": 1520, "weight_kg": 0.45},
    "AP_Racing_CP5555": {"pistons": 4, "piston_area_mm2": 1780, "weight_kg": 0.52},
    "Brembo_P2_34":     {"pistons": 2, "piston_area_mm2": 908,  "weight_kg": 0.30},
}
```

---

### 4.3 `aerodynamics/` — Aerodinamik 🔴 KRİTİK

**Dosya yapısı:**
```
aerodynamics/
├── __init__.py
├── forces.py        # Temel L, D hesabı
├── wings.py         # Kanat açısı → CL/CD tahmini
├── ground_effect.py # Zemin yüksekliği etkisi
└── drag_budget.py   # Sürükleme bütçesi dağılımı
```

**forces.py — fonksiyonlar:**
```python
# Sabitler
RHO_SEA_LEVEL = 1.225   # kg/m³ deniz seviyesi hava yoğunluğu

def calculate_downforce(CL, reference_area_m2, speed_kmh, air_density=RHO_SEA_LEVEL):
    """
    L = ½ × ρ × v² × A × CL
    CL tipik FS araçları: 1.5 - 3.5 (kanat + difüzör)
    """
    v = speed_kmh / 3.6
    return 0.5 * air_density * v**2 * reference_area_m2 * CL

def calculate_drag(CD, reference_area_m2, speed_kmh, air_density=RHO_SEA_LEVEL):
    """
    D = ½ × ρ × v² × A × CD
    CD tipik FS: 1.2 - 2.0
    """
    v = speed_kmh / 3.6
    return 0.5 * air_density * v**2 * reference_area_m2 * CD

def calculate_aero_balance(front_downforce_N, rear_downforce_N):
    """
    Ön/arka downforce dağılımı.
    Tipik FS hedef: %40-45 ön
    """
    total = front_downforce_N + rear_downforce_N
    front_pct = front_downforce_N / total * 100
    return {
        "front_pct": round(front_pct, 1),
        "rear_pct": round(100 - front_pct, 1),
        "balanced": 38 <= front_pct <= 48
    }

def calculate_lift_to_drag(CL, CD):
    """L/D oranı; yüksek = verimli aero"""
    return round(CL / CD, 3)

def calculate_aero_at_speeds(CL, CD, area_m2, speeds_kmh=None):
    """Farklı hızlarda downforce ve drag tablosu"""
    if speeds_kmh is None:
        speeds_kmh = [30, 50, 70, 90, 110]
    results = []
    for v in speeds_kmh:
        df = calculate_downforce(CL, area_m2, v)
        dr = calculate_drag(CD, area_m2, v)
        results.append({"speed_kmh": v, "downforce_N": round(df), "drag_N": round(dr)})
    return results

def estimate_cornering_speed(mechanical_grip_N, aero_downforce_N,
                             corner_radius_m, vehicle_mass_kg):
    """
    Toplam grip = mekanik + aerodinamik
    v_corner = √(μ × (W + DF) × r / m)
    """
    import math
    total_grip = mechanical_grip_N + aero_downforce_N
    mu = 1.5   # slick lastik tipik
    v = math.sqrt(mu * total_grip * corner_radius_m / vehicle_mass_kg)
    return round(v * 3.6, 1)   # km/h
```

**wings.py — fonksiyonlar:**
```python
WING_PROFILES = {
    "NACA_0012": {"CL_per_deg": 0.095, "CD_base": 0.008, "stall_deg": 16},
    "NACA_2412": {"CL_per_deg": 0.100, "CD_base": 0.009, "stall_deg": 14},
    "NACA_4412": {"CL_per_deg": 0.105, "CD_base": 0.010, "stall_deg": 13},
    "custom_high_df": {"CL_per_deg": 0.120, "CD_base": 0.015, "stall_deg": 11},
}

def estimate_wing_CL(profile, angle_of_attack_deg):
    """Kanat profili + açıdan CL tahmini (lineer bölge)"""

def estimate_wing_CD(profile, angle_of_attack_deg):
    """CD = CD_base + k × CL²  (indüktif drag)"""

def calculate_wing_downforce(profile, aoa_deg, span_mm, chord_mm, speed_kmh):
    """Tek kanat için downforce ve drag"""

def check_wing_stall(profile, aoa_deg):
    """Durma açısı kontrolü"""

def optimize_wing_angle(target_downforce_N, span_mm, chord_mm, speed_kmh, profile="NACA_2412"):
    """Hedef downforce için gereken kanat açısı"""

def calculate_multi_element_wing(elements, speed_kmh):
    """
    Çok elemanlı kanat (FS arka kanat tipik 2-3 eleman).
    Her element için CL/CD; toplam katkı.
    """
```

**ground_effect.py — fonksiyonlar:**
```python
def estimate_ground_effect_factor(ride_height_mm, reference_height_mm=150):
    """
    Zemin etkisi; ride height düştükçe downforce artar.
    Basit model: GE_factor = (reference / ride_height) ^ 0.5
    """
    import math
    factor = (reference_height_mm / max(ride_height_mm, 10)) ** 0.5
    return round(min(factor, 3.0), 3)   # max 3x güvenlik sınırı

def calculate_diffuser_downforce(diffuser_angle_deg, diffuser_area_m2, speed_kmh):
    """
    Difüzör: Venturi etkisi; araç altı hava hızlanması → basınç düşer → downforce
    """

def check_ride_height_aero(ride_height_mm):
    """
    Minimum ride height önerisi (pist kaplayıcı riski vs ground effect dengesi)
    FS tipik: 25-40mm
    """
    return {
        "ride_height_mm": ride_height_mm,
        "ground_effect_strong": ride_height_mm < 30,
        "bottoming_risk": ride_height_mm < 20,
        "recommendation": "25-35mm FS için optimal"
    }
```

**drag_budget.py — fonksiyonlar:**
```python
DRAG_COMPONENTS_TYPICAL_FS = {
    "front_wing": 0.15,      # toplam CD'nin %15'i
    "rear_wing": 0.25,
    "open_wheels": 0.35,     # en büyük kaynak!
    "body_cockpit": 0.15,
    "cooling_inlets": 0.05,
    "suspension_exposed": 0.05,
}

def calculate_drag_budget(CD_total, components=None):
    """
    Sürükleme bütçesi dağılımı.
    Her komponentin CD katkısını göster.
    """

def estimate_power_loss_from_drag(drag_N, speed_kmh):
    """
    P_drag = F_drag × v
    Bu kadar güç salt havayı itmek için harcanıyor.
    """
    v = speed_kmh / 3.6
    return round(drag_N * v / 1000, 2)   # kW

def compare_aero_configs(config_a, config_b, speed_kmh, vehicle_mass_kg):
    """İki aero konfigürasyonunu lap time etkisi açısından karşılaştır"""
```

---

### 4.4 `tires/` — Lastik Sistemi 🟡 ÖNEMLİ

**Dosya yapısı:**
```
tires/
├── __init__.py
├── force_model.py    # Traksiyon çemberi, slip angle, Pacejka basit
├── thermal_model.py  # Sıcaklık penceresi, basınç-sıcaklık
└── selection.py      # Lastik seçimi, bileşim karşılaştırma
```

**force_model.py — fonksiyonlar:**
```python
def calculate_max_lateral_force(normal_force_N, mu=1.5):
    """
    Fmax = μ × N
    Slick lastik tipik: μ = 1.4 - 1.8 (sıcaklığa bağlı)
    """
    return normal_force_N * mu

def calculate_traction_circle(lateral_force_N, longitudinal_force_N, max_force_N):
    """
    Traksiyon çemberi: F_lat² + F_long² ≤ F_max²
    Kullanım yüzdesi = toplam kuvvet / max kuvvet
    """
    import math
    combined = math.sqrt(lateral_force_N**2 + longitudinal_force_N**2)
    utilization = combined / max_force_N
    return {
        "combined_force_N": round(combined),
        "max_force_N": max_force_N,
        "utilization_pct": round(utilization * 100, 1),
        "within_limit": utilization <= 1.0
    }

def estimate_slip_angle_peak(compound="medium"):
    """
    Maksimum tutunmanın yaşandığı slip angle.
    FS slick tipik: 8-14°
    """
    peaks = {"soft": 8, "medium": 10, "hard": 13}
    return peaks.get(compound, 10)

def simple_pacejka(slip_angle_deg, Fz_N, B=10, C=1.9, D=1.5, E=0.97):
    """
    Pacejka Magic Formula basit lateral kuvvet modeli:
    Fy = D × sin(C × arctan(B × α - E × (B × α - arctan(B × α))))
    """
    import math
    alpha = math.radians(slip_angle_deg)
    Fy = Fz_N * D * math.sin(C * math.atan(B * alpha - E * (B * alpha - math.atan(B * alpha))))
    return round(Fy, 1)

def calculate_load_sensitivity(Fz_N, mu_ref=1.6, sensitivity=0.05):
    """
    Lastik yük hassasiyeti: yük arttıkça mu azalır.
    μ_eff = μ_ref - sensitivity × (Fz / Fz_ref - 1)
    """
```

**thermal_model.py — fonksiyonlar:**
```python
TIRE_OPTIMAL_TEMP = {
    "soft":   {"min": 75, "peak": 90,  "max": 105},
    "medium": {"min": 80, "peak": 100, "max": 115},
    "hard":   {"min": 85, "peak": 105, "max": 120},
}

def check_tire_temperature(temp_C, compound="medium"):
    """
    Çalışma sıcaklığı kontrolü.
    Optimal pencere: compound'a göre.
    """
    window = TIRE_OPTIMAL_TEMP[compound]
    if temp_C < window["min"]:
        status = "too_cold"
    elif temp_C > window["max"]:
        status = "overheating"
    else:
        status = "optimal"
    return {"temp_C": temp_C, "status": status, "window": window}

def estimate_cold_pressure(hot_pressure_bar, ambient_temp_C=20, operating_temp_C=90):
    """
    Sıcaklık farkından dolayı basınç değişimi (Gay-Lussac).
    P_cold = P_hot × (T_cold / T_hot)   [Kelvin]
    """
    T_cold = ambient_temp_C + 273.15
    T_hot = operating_temp_C + 273.15
    return round(hot_pressure_bar * T_cold / T_hot, 2)

def check_tire_pressure(pressure_bar, axle="front"):
    """Tipik FS lastik basıncı kontrolü"""
    ranges = {"front": (1.1, 1.8), "rear": (0.9, 1.6)}
    lo, hi = ranges[axle]
    return {"pressure_bar": pressure_bar, "in_range": lo <= pressure_bar <= hi,
            "recommended_range": f"{lo}-{hi} bar"}
```

---

### 4.5 `dynamics/` — Araç Dinamiği 🟡 ÖNEMLİ

**Dosya yapısı:**
```
dynamics/
├── __init__.py
├── load_transfer.py   # LTR formülü, dinamik yük
├── balance.py         # Understeer/oversteer gradyanı
└── weight_dist.py     # CoG hesabı, polar atalet tahmini
```

**load_transfer.py — fonksiyonlar:**
```python
def calculate_lateral_load_transfer(vehicle_mass_kg, lateral_accel_g,
                                    cog_height_mm, track_width_mm):
    """
    LTR = m × ay × h / T
    Virajda dış tekerleğe yük transferi (N)
    """
    ay = lateral_accel_g * 9.81
    ltr = vehicle_mass_kg * ay * (cog_height_mm / 1000) / (track_width_mm / 1000)
    return {
        "load_transfer_N": round(ltr, 0),
        "lateral_accel_g": lateral_accel_g,
        "cog_height_mm": cog_height_mm
    }

def calculate_longitudinal_load_transfer(vehicle_mass_kg, accel_g,
                                         cog_height_mm, wheelbase_mm):
    """Hızlanma/frenleme yük transferi (ön/arka)"""

def calculate_wheel_loads(vehicle_mass_kg, front_weight_pct,
                          cog_height_mm, track_mm, wheelbase_mm,
                          lateral_g=0, longitudinal_g=0):
    """
    4 tekerlekte dinamik yük hesabı.
    Statik + lateral transfer + longitudinal transfer
    """
```

**balance.py — fonksiyonlar:**
```python
def calculate_understeer_gradient(front_cornering_stiffness, rear_cornering_stiffness,
                                  front_weight_N, rear_weight_N):
    """
    K_us = (a₁/C_αf) - (a₂/C_αr)
    K_us > 0 → understeer
    K_us < 0 → oversteer
    K_us = 0 → neutral steer
    """
    a1 = front_weight_N / front_cornering_stiffness
    a2 = rear_weight_N / rear_cornering_stiffness
    K_us = a1 - a2
    return {
        "understeer_gradient": round(K_us, 4),
        "character": "understeer" if K_us > 0 else ("oversteer" if K_us < 0 else "neutral"),
        "front_slip_deg_per_g": round(a1, 3),
        "rear_slip_deg_per_g": round(a2, 3)
    }

def estimate_roll_angle(lateral_accel_g, roll_gradient_deg_per_g):
    """Virajda gövde yatış açısı tahmini"""

def check_balance_sensitivity(front_arb_stiffness, rear_arb_stiffness,
                              front_spring_rate, rear_spring_rate):
    """ARB ve yay ayarının balance üzerindeki etkisi"""
```

**weight_dist.py — fonksiyonlar:**
```python
def calculate_cog_height(component_masses, component_heights):
    """
    Bileşen bazlı CoG yüksekliği hesabı.
    CoG_h = Σ(m_i × h_i) / Σm_i
    """
    total_mass = sum(component_masses)
    weighted_h = sum(m * h for m, h in zip(component_masses, component_heights))
    return round(weighted_h / total_mass, 1)

def calculate_weight_distribution(component_masses, component_x_positions, wheelbase_mm):
    """Ön/arka ağırlık dağılımı % hesabı"""

def estimate_polar_moment(component_masses, component_distances_from_cog):
    """
    Iz = Σ(m_i × r_i²)
    Küçük Iz → çevik; büyük Iz → stabil
    FS hedefi: Iz < 80 kg·m²
    """
    return round(sum(m * (r/1000)**2 for m, r in zip(component_masses, component_distances_from_cog)), 2)
```

---

### 4.6 `transmission/` — Aktarma Organları 🟡 ÖNEMLİ

**Dosya yapısı:**
```
transmission/
├── __init__.py
├── gearbox.py       # Vites oranı, devre analizi
├── differential.py  # LSD, kilitleme etkisi
└── driveshaft.py    # Burulma dayanımı, kritik hız
```

**gearbox.py — fonksiyonlar:**
```python
def calculate_gear_ratios(engine_max_rpm, wheel_radius_mm,
                          max_speed_kmh, num_gears=6):
    """
    Son vites oranı = (engine_max_rpm / max_speed_rad_s)
    Her vites geometrik dizi ile hesaplanır.
    """
    import math
    v_max = max_speed_kmh / 3.6
    omega_wheel = v_max / (wheel_radius_mm / 1000)
    top_gear_ratio = engine_max_rpm / (omega_wheel * 60 / (2 * math.pi))
    
    # Geometrik dizi; FS tipik spread: 3.5-4.5x
    ratio_spread = 3.8
    ratios = []
    for i in range(num_gears):
        r = top_gear_ratio * (ratio_spread ** ((num_gears - 1 - i) / (num_gears - 1)))
        ratios.append(round(r, 2))
    return ratios

def calculate_speed_at_rpm(gear_ratio, final_drive_ratio, wheel_radius_mm, rpm):
    """Verilen vites + devir → araç hızı"""
    omega_engine = rpm * 2 * 3.14159 / 60
    omega_wheel = omega_engine / (gear_ratio * final_drive_ratio)
    v = omega_wheel * (wheel_radius_mm / 1000)
    return round(v * 3.6, 1)

def calculate_rpm_at_speed(speed_kmh, gear_ratio, final_drive_ratio, wheel_radius_mm):
    """Araç hızı + vites → motor devri"""

def optimize_gear_ratios(engine_torque_curve, track_top_speed_kmh,
                         corner_exit_speed_kmh, wheel_radius_mm):
    """
    Pist bazlı vites oranı optimizasyonu.
    Hedef: her viraj çıkışında motor peak torque bandında olsun.
    """

def check_rpm_drop_between_gears(ratios, engine_peak_torque_rpm, engine_peak_power_rpm):
    """Vites değiştirirken devir düşüşünün torque bandı içinde kalması kontrolü"""
```

---

### 4.7 `scoring/` — FSAE Puanlama Sistemi 🟢 FS ÖZGÜNü

**Dosya yapısı:**
```
scoring/
├── __init__.py
├── events.py     # Her event puanlama formülü
├── formulas.py   # SAE resmi formüller
└── optimizer.py  # Hangi event için ne optimize edilmeli
```

**events.py — fonksiyonlar:**
```python
# FSAE 2024 puanlama sistemi
MAX_POINTS = {
    "acceleration":  75,
    "skidpad":       75,
    "autocross":    125,
    "endurance":    275,
    "efficiency":   100,
    "cost":         100,
    "design":       150,
    "business":      75,
    "total":        975
}

def score_acceleration(your_time_s, best_time_s, worst_time_s=None):
    """
    Score = 95.5 × [(T_max² / T_yours²) - 1] / [(T_max² / T_min²) - 1] + 4.5
    T_max = en yavaş kabul edilen süre
    """

def score_skidpad(your_time_s, best_time_s):
    """
    Score = 71.5 × [(T_min/T_yours)² - 1] / [(T_min/T_max)² - 1] + 3.5
    """

def score_autocross(your_time_s, best_time_s):
    """Autocross puanı — acceleration ile aynı formül yapısı"""

def score_endurance(your_time_s, best_time_s, dnf=False):
    """Endurance: en yüksek değerli dinamik event (275 puan)"""

def score_efficiency(your_fuel_L, best_fuel_L, endurance_points):
    """Efficiency = endurance puanı × (en iyi yakıt / senin yakıtın)"""

def calculate_total_score(acceleration, skidpad, autocross, endurance,
                          efficiency, cost, design, business):
    """Toplam puan ve kategori dağılımı"""

def estimate_championship_position(your_score, field_scores):
    """Tahmini sıralama"""
```

**optimizer.py — fonksiyonlar:**
```python
def identify_weak_events(scores_dict):
    """Hangi event'te en fazla gelişme potansiyeli var?"""

def calculate_point_sensitivity(vehicle_params, event="endurance"):
    """
    Bir parametreyi %1 değiştirmek kaç puan kazandırır?
    Örn: 1 kg hafifletme → endurance +X puan
    """

def suggest_priorities(team_resources, current_scores):
    """
    Sınırlı kaynak ile maksimum puan artışı.
    Hangi sistemde çalışmak en fazla katkıyı sağlar?
    """
```

---

### 4.8 `fuel/` — Yakıt Sistemi 🟢 DEĞER KATAR

```python
# fuel/consumption.py
def estimate_endurance_fuel(engine_name, lap_time_s, num_laps=22, track_length_km=1.0):
    """
    Endurance: 22km. Motor yakıt tüketimi + emniyet payı.
    FS yakıt limiti: 10 litre
    """
    # BSFC (Brake Specific Fuel Consumption) bazlı hesap
    # BSFC tipik motosiklet motoru: 280-320 g/kWh

def check_fuel_tank_rule(tank_volume_liters):
    """FS kuralı: maksimum 10 litre yakıt"""
    return {
        "volume_liters": tank_volume_liters,
        "compliant": tank_volume_liters <= 10,
        "rule": "FS T7.1: Max 10L"
    }

def calculate_fuel_weight_cog_effect(fuel_liters, tank_position_x_mm,
                                     tank_position_z_mm, vehicle_mass_kg):
    """Yakıt azaldıkça CoG ve ağırlık dağılımı değişimi"""
```

---
## 5. FS KURALLARI — MEVCUT vs EKSİK KAPSAM

### Mevcut (utils/constants.py + chassis/constraints.py)
| Kural | Değer | Durum |
|---|---|---|
| Min araç ağırlığı | 180 kg (sürücü dahil) | ✅ |
| Max uzunluk | 2100 mm | ✅ |
| Max genişlik | 1200 mm | ✅ |
| Max deplasman | 710 cc | ✅ |
| Intake restrictor | 20 mm (IC) / 19 mm (EV yok) | ✅ |
| Rollbar min yükseklik | Sürücü + 50mm | ✅ |
| Firewall kalınlık | Alüm 1.5mm, çelik 1.0mm | ✅ |

### Eksik FS Kuralları (eklenmeli)

```python
# utils/constants.py'e eklenecek
FS_FUEL_TANK_MAX_LITERS = 10          # T7.1
FS_ROLLBAR_MIN_OD_MM = 25.4           # T3.21.1: min ∅25.4mm
FS_ROLLBAR_MIN_WALL_MM = 2.4          # T3.21.1: min 2.4mm duvar
FS_SOUND_LIMIT_DB = 110               # EV5.1 / IC3.1: max 110 dB @ 0.5m
FS_COCKPIT_OPENING_MIN_WIDTH_MM = 330  # T4.3: kokpit açıklığı min genişlik
FS_COCKPIT_OPENING_MIN_HEIGHT_MM = 550 # T4.3
FS_HARNESS_MIN_POINTS = 6             # T8.2: 6 noktalı emniyet kemeri
FS_NOSE_DEFORMATION_MIN_TRAVEL_MM = 25 # T3.14: ön koni deformasyon seyahati
FS_BRAKE_CIRCUIT_INDEPENDENT = True   # T11.1: çift bağımsız devre
FS_BRAKE_LIGHT_REQUIRED = True        # T11.9: fren lambası zorunlu
FS_EV_ISOLATION_MIN_V = 500           # EV4.2: HV izolasyon (elektrikli FS)
FS_EV_MAX_DC_VOLTAGE = 600            # EV4.1
FS_DRIVER_MIN_AGE = 17                # A3.3
```

```python
# chassis/constraints.py'e eklenecek fonksiyonlar
def check_rollbar_spec(od_mm, wall_mm):
    """T3.21.1 rollbar minimum malzeme spec kontrolü"""
    return {
        "od_ok": od_mm >= FS_ROLLBAR_MIN_OD_MM,
        "wall_ok": wall_mm >= FS_ROLLBAR_MIN_WALL_MM,
        "compliant": od_mm >= FS_ROLLBAR_MIN_OD_MM and wall_mm >= FS_ROLLBAR_MIN_WALL_MM
    }

def check_cockpit_opening(width_mm, height_mm):
    """T4.3 sürücü giriş açıklığı"""

def check_fuel_system(tank_liters, fuel_type="gasoline"):
    """T7 yakıt sistemi kuralları"""

def check_sound_limit(measured_db, test_rpm_pct=50):
    """IC3.1 / EV5.1 ses limiti"""

def check_ev_safety(max_voltage, isolation_resistance_ohm_per_volt):
    """EV4 elektrik güvenlik kuralları (elektrikli FS takımları için)"""

def full_fs_compliance_check(vehicle_params):
    """
    Tüm FS kurallarını tek seferde kontrol et.
    Geçmeyen kuralları açıklamalı listele.
    """
```

---
## 6. CLI GENİŞLETME

### Mevcut CLI Komutları
```bash
python cli.py chassis analyze --tube-od 25.4 --wall 1.6 --length 1000
python cli.py chassis reverse --target-weight 20
python cli.py chassis optimize --target-weight 20
python cli.py engine list --common
python cli.py engine info Yamaha_YZF_R6
python cli.py engine analyze Yamaha_YZF_R6 --weight 200 --restrictor 20
python cli.py fs-check --weight 185 --length 2050 --width 1180
```

### Eklenecek CLI Komutları
```bash
# Süspansiyon
python cli.py suspension geometry --camber -2.5 --toe 1.5 --caster 7
python cli.py suspension spring --wheel-rate 20 --motion-ratio 0.75
python cli.py suspension arb --diameter 16 --length 400 --arm 80

# Fren
python cli.py brakes bias --front-weight 800 --rear-weight 900 --decel 1.5 --cog 280 --wb 1600
python cli.py brakes thermal --mass 200 --speed 90 --num-discs 4

# Aerodinamik
python cli.py aero downforce --CL 2.0 --area 1.2 --speed 80
python cli.py aero drag-budget --CD 1.5 --area 1.2 --speed 80
python cli.py aero balance --front-df 250 --rear-df 400

# Lastik
python cli.py tires check-temp --temp 95 --compound medium
python cli.py tires pressure --hot-bar 1.4 --ambient 20

# Dinamik
python cli.py dynamics load-transfer --mass 200 --lateral-g 1.8 --cog 280 --track 1200
python cli.py dynamics balance --front-cs 800 --rear-cs 950 --front-w 900 --rear-w 1000

# FSAE Puanlama
python cli.py scoring acceleration --your-time 4.2 --best-time 3.8
python cli.py scoring endurance --your-time 1450 --best-time 1380
python cli.py scoring total --accel 60 --skidpad 58 --autocross 110 --endurance 240 --efficiency 85

# Tam FS Kontrolü (genişletilmiş)
python cli.py fs-check-full --weight 185 --length 2050 --width 1180 \
  --rollbar-od 25.4 --rollbar-wall 2.5 \
  --fuel-tank 8.5 --brake-circuits 2
```

---
## 7. ÖNCELİK VE YOL HARİTASI

### Faz 1 — Kritik Altyapı (hemen)
```
1. Bug fix'ler (2-4 saat):
   - parse_tube_spec: length tuple desteği
   - calculate_0_100_estimation: numerik integrasyon
   - restrictor model: Bernoulli denklemi
   - utils/__init__.py: geçersiz export isimleri

2. suspension/ modülü (3-5 gün):
   - geometry.py: camber/toe/caster/Ackermann
   - kinematics.py: IC, roll center, camber gain
   - spring_damper.py: wheel rate, natural frequency
   - arb.py: torsion bar sertliği

3. brakes/ modülü (2-3 gün):
   - system.py: bias hesabı, MC boyutu
   - thermal.py: disk sıcaklık, soğutma
   - sizing.py: rotor/kalibri seçimi
```

### Faz 2 — Performans Analizi (1-2 hafta)
```
4. aerodynamics/ modülü
5. tires/ modülü
6. dynamics/ modülü
7. Engine DB genişletme (1000cc sınıfı)
8. Eksik FS kural sabitleri + kontrol fonksiyonları
```

### Faz 3 — FS Özgün Özellikler (2-3 hafta)
```
9. transmission/ modülü (vites oranı optimizasyonu)
10. scoring/ modülü (FSAE puanlama sistemi)
11. fuel/ modülü (endurance yakıt planlaması)
12. CLI'ya tüm yeni komutlar
13. Entegrasyon testi: tüm sistem birlikte çalışıyor mu?
```

### Faz 4 — İleri Özellikler (opsiyonel)
```
14. data_log/ modülü (telemetri şema ve parser)
15. Elektrikli FS desteği (EV motor/akü modeli)
16. Basit lap time simülasyonu (enerji bazlı)
17. Raporlama: tüm analizleri PDF/MD olarak export
```

### Parametre Referans Tablosu — Tipik FS Değerleri

| Parametre | Tipik FS Değeri | Birim | Kaynak |
|---|---|---|---|
| Toplam ağırlık | 190-230 | kg | Takım verileri |
| Güç/ağırlık | 0.5-0.9 | kW/kg | Motor + araç |
| Wheelbase | 1500-1700 | mm | FS araç ortalaması |
| Track genişliği | 1100-1200 | mm | FS araç ortalaması |
| CoG yüksekliği | 270-320 | mm | Telemetri verisi |
| Ön ağırlık % | 42-48 | % | Denge hedefi |
| Ride height ön | 25-40 | mm | Aero vs klearans |
| Ride height arka | 30-45 | mm | Aero vs klearans |
| Ön camber | -2.0 ila -3.5 | ° | Setup hedefi |
| Arka camber | -1.0 ila -2.0 | ° | Setup hedefi |
| Ön toe | +0.5 ila +2 | mm | Setup hedefi |
| Yay oranı ön | 15-25 | N/mm (wheel) | Frekans hedefi |
| Yay oranı arka | 20-35 | N/mm (wheel) | Frekans hedefi |
| Natural freq ön | 2.0-3.0 | Hz | Sürüş konforu/grip |
| Natural freq arka | 2.5-3.5 | Hz | |
| Downforce (80 km/h) | 300-800 | N | Aero konfigürasyon |
| Drag (80 km/h) | 150-400 | N | Aero konfigürasyon |
| CL (toplam) | 1.5-3.5 | — | Kanatlı araç |
| CD (toplam) | 1.2-2.0 | — | Kanatlı araç |
| Fren bias ön | 60-70 | % | Bias ayarı |
| Disk çapı ön | 200-280 | mm | Termal kapsite |
| Lastik çalışma sıc. | 80-110 | °C | Optimal pencere |
| Lastik basınç ön | 1.2-1.8 | bar | Sicak çalışma |
| Endurance fuel | 4.5-7.0 | L | 22km tüketim |
| 0-100 km/h | 3.5-5.0 | s | Performans hedefi |
| Skidpad çap | 15.25m | m | FSAE standart |
| Accel mesafe | 75m | m | FSAE standart |

---
*Tüm değerler Formula SAE Electric ve Formula SAE Combustion 2024 kuralları referans alınarak hazırlanmıştır.*
*Kural değişiklikleri için: fsaeonline.com/page.aspx?pageid=c6b89b83-2b1c-4c9f-a77a-c83dcf0bd0f0*