#!/usr/bin/env python3
"""
Example Formula Student Vehicle Analysis
=================================
Tam FS aracı analizi - kullanıcı dostu çıktı
"""

import sys
sys.path.insert(0, '..')

from chassis import analyze_weight, full_fs_compliance_check, calculate_rollbar_force
from engine import get_engine, calculate_power_to_weight
from engine.constraints import estimate_power_with_restrictor
from suspension import check_camber, check_toe, check_caster, calculate_ackermann, calculate_wheel_rate
from brakes import calculate_brake_bias, estimate_disc_temperature, calculate_brake_energy
from aerodynamics import calculate_downforce, calculate_drag, calculate_lift_to_drag
from tires import check_tire_temperature, check_tire_pressure, calculate_max_lateral_force
from dynamics import calculate_lateral_load_transfer, calculate_understeer_gradient
from scoring import score_acceleration, score_skidpad, score_endurance, get_max_points
from fuel import estimate_endurance_fuel, check_fuel_tank_rule

# =============================================================================
# ÖRNEK ARAÇ SPECS
# =============================================================================

VEHICLE = {
    "name": "FS-2024",
    "category": "Formula Student",
    "engine": "Honda CBR600RR",
    "chassis_type": "spaceframe",
    "chassis_material": "4130 Chromoly",
    
    "dimensions": {
        "length_mm": 1980,
        "width_mm": 1150,
        "wheelbase_mm": 1600,
        "track_mm": 1200,
    },
    
    "weight": {
        "total_kg": 200,
        "front_pct": 45,
        "cog_height_mm": 280,
    },
    
    "suspension": {
        "camber_front": -2.5,
        "camber_rear": -1.5,
        "toe_front": 1.0,
        "caster": 6.0,
        "spring_rate": 20,
        "motion_ratio": 0.75,
    },
    
    "brakes": {
        "bias": 65,
        "disc_dia": 220,
    },
    
    "aero": {
        "CL_total": 2.0,
        "area": 1.2,
        "CD": 1.5,
    },
    
    "tires": {
        "compound": "medium",
        "pressure_front": 1.4,
        "pressure_rear": 1.2,
    },
}

# =============================================================================
# RENKLER
# =============================================================================

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def ok(msg): return f"{Colors.GREEN}✓{Colors.END} {msg}"
def fail(msg): return f"{Colors.RED}✗{Colors.END} {msg}"
def warn(msg): return f"{Colors.YELLOW}!{Colors.END} {msg}"
def info(msg): return f"{Colors.CYAN}›{Colors.END} {msg}"

# =============================================================================
# ANALİZ FONKSİYONLARI
# =============================================================================

def header(title):
    print(f"\n{Colors.BOLD}{'='*50}{Colors.END}")
    print(f"{Colors.BOLD}  {title}{Colors.END}")
    print(f"{Colors.BOLD}{'='*50}{Colors.END}")

def subheader(title):
    print(f"\n{Colors.BLUE}▶ {title}{Colors.END}")

def result(label, value, status=None):
    if status is True:
        print(f"  {ok(label)}: {value}")
    elif status is False:
        print(f"  {fail(label)}: {value}")
    elif status == "warn":
        print(f"  {warn(label)}: {value}")
    else:
        print(f"  {label}: {value}")

def section(title):
    subheader(title)
    print("-" * 40)

# =============================================================================
# ANALİZLER
# =============================================================================

def analyze_chassis(v):
    section("ŞASI")
    
    tubes = [(25.4, 1.6, 5000), (25.4, 1.6, 3000), (22.2, 1.6, 2000)]
    w = analyze_weight(tubes, "4130")
    result("Malzeme", v["chassis_material"])
    result("Ağırlık", f"{w['total_weight']:.2f} kg")
    result("Uzunluk", f"{w['total_length']:.0f} mm")
    
    rf = calculate_rollbar_force(v["weight"]["total_kg"], 2.5)
    result("Rollbar kuvveti", f"{rf:.0f} N")

def analyze_engine(v):
    section("MOTOR")
    
    eng = get_engine(v["engine"])
    result("Motor", eng["name"])
    result("Hacim", f"{eng['displacement_cc']} cc")
    result("Güç", f"{eng['power_hp']} HP")
    result("Tork", f"{eng['torque_Nm']} Nm")
    result("Ağırlık", f"{eng['weight_kg']} kg")
    
    restricted = estimate_power_with_restrictor(v["engine"], 20)
    result("FS restrictor", f"{restricted['estimated_power_hp']:.0f} HP ({restricted['power_lost_percent']:.0f}% kayıp)")
    
    ptw = calculate_power_to_weight(v["engine"], v["weight"]["total_kg"])
    result("Güç/Ağırlık", f"{ptw['power_to_weight_kW_per_kg']:.3f} kW/kg")

def analyze_fs_compliance(v):
    section("FS KURALLARI")
    
    r = full_fs_compliance_check({
        "weight": v["weight"]["total_kg"],
        "length": v["dimensions"]["length_mm"],
        "width": v["dimensions"]["width_mm"],
        "displacement": 600,
        "restrictor": 20,
        "fuel_tank": 8,
        "rollbar_od": 25.4,
        "rollbar_wall": 2.4,
        "cockpit_width": 350,
        "cockpit_height": 550,
    })
    
    passed = ok("Uyumlu") if r["passed"] else fail("Uyumsuz")
    result("Tüm kontroller", passed)
    
    for check, data in r["checks"].items():
        if isinstance(data, dict):
            p = data.get("passed", data.get("compliant", False))
            result(check, "", p)

def analyze_suspension(v):
    section("SÜSPANSİYON")
    
    susp = v["suspension"]
    dims = v["dimensions"]
    
    camber = check_camber(susp["camber_front"], "front")
    result("Ön camber", f"{susp['camber_front']}°", camber["in_typical_range"])
    result("Arka camber", f"{susp['camber_rear']}°")
    
    toe = check_toe(susp["toe_front"], "front")
    result("Ön toe", f"{susp['toe_front']} mm")
    
    caster = check_caster(susp["caster"])
    result("Caster", f"{susp['caster']}°", caster["in_typical_range"])
    
    ack = calculate_ackermann(dims["wheelbase_mm"], dims["track_mm"], 5000)
    result("Ackermann", f"{ack['inner_angle_deg']}° / {ack['outer_angle_deg']}°")
    
    wr = calculate_wheel_rate(susp["spring_rate"], susp["motion_ratio"])
    result("Wheel rate", f"{wr['wheel_rate_N_mm']:.1f} N/mm")

def analyze_brakes(v):
    section("FREN")
    
    brakes = v["brakes"]
    w = v["weight"]
    dims = v["dimensions"]
    
    front_N = w["total_kg"] * 9.81 * (w["front_pct"] / 100)
    rear_N = w["total_kg"] * 9.81 * ((100 - w["front_pct"]) / 100)
    bias = calculate_brake_bias(front_N, rear_N, 1.2, w["cog_height_mm"], dims["wheelbase_mm"])
    result("On/Arka bias", f"{bias['ideal_front_bias_pct']:.1f}%")
    result("Disk çapı", f"{brakes['disc_dia']} mm")
    
    energy = calculate_brake_energy(w["total_kg"], 100, 0)
    temp = estimate_disc_temperature(energy["kinetic_energy_J"], 1.5, 2)
    result("Disk sıcaklık", f"{temp['final_temp_C']:.0f}°C", temp["final_temp_C"] < 600)

def analyze_aero(v):
    section("AERODİNAMİK")
    
    aero = v["aero"]
    
    print(f"  Hız        Downforce    Drag    L/D")
    print(f"  " + "-" * 35)
    
    for speed in [50, 80, 100, 120]:
        df = calculate_downforce(aero["CL_total"], aero["area"], speed)
        dr = calculate_drag(aero["CD"], aero["area"], speed)
        ld = calculate_lift_to_drag(aero["CL_total"], aero["CD"])
        print(f"  {speed:>3} km/h   {df:>7.0f} N   {dr:>5.0f} N   {ld:.2f}")
    
    result("Downforce", f"{calculate_downforce(aero['CL_total'], aero['area'], 80):.0f} N @ 80 km/h")

def analyze_tires(v):
    section("LASTİK")
    
    tires = v["tires"]
    
    temp = check_tire_temperature(95, tires["compound"])
    result("Sıcaklık (95°C)", temp['status'], temp['status'] == 'optimal')
    
    pf = check_tire_pressure(tires["pressure_front"], "front")
    result("Ön basınç", f"{tires['pressure_front']} bar", pf['in_range'])
    
    pr = check_tire_pressure(tires["pressure_rear"], "rear")
    result("Arka basınç", f"{tires['pressure_rear']} bar", pr['in_range'])
    
    lat = calculate_max_lateral_force(v["weight"]["total_kg"] * 9.81, 1.5)
    result("Max lateral", f"{lat:.0f} N (µ=1.5)")

def analyze_dynamics(v):
    section("DİNAMİK")
    
    w = v["weight"]
    dims = v["dimensions"]
    
    ltr = calculate_lateral_load_transfer(w["total_kg"], 1.8, w["cog_height_mm"], dims["track_mm"])
    result("Yük transferi", f"{ltr['load_transfer_N']:.0f} N @ 1.8g")
    
    ust = calculate_understeer_gradient(800, 950, w["total_kg"]*9.81*0.45, w["total_kg"]*9.81*0.55)
    result("Karakter", ust['character'])
    result("CoG yüksekliği", f"{w['cog_height_mm']} mm")

def analyze_scoring(v):
    section("FS PUANLAMA")
    
    max_pts = get_max_points()
    print(f"  Max puanlar:")
    for k, p in max_pts.items():
        if k != "total":
            print(f"    {k}: {p}")
    
    accel = score_acceleration(4.2, 3.8, 5.0)
    skid = score_skidpad(5.5, 5.0, 6.5)
    end = score_endurance(1450, 1380)
    
    print(f"\n  Tahmini skorlar:")
    print(f"    Acceleration: {accel:.1f} / 75")
    print(f"    Skidpad: {skid:.1f} / 75")
    print(f"    Endurance: {end:.1f} / 275")

def analyze_fuel(v):
    section("YAKIT")
    
    fuel = estimate_endurance_fuel(v["engine"], 75, 22)
    tank = check_fuel_tank_rule(fuel["estimated_fuel_L"])
    
    result("Yakıt tüketimi", f"{fuel['estimated_fuel_L']:.2f} L (22 tur)", tank['compliant'])
    result("Tank", f"max {tank['max_allowed_L']} L")

# =============================================================================
# ÖZET
# =============================================================================

def summary(v):
    header("ÖZET")
    
    eng = get_engine(v["engine"])
    ptw = calculate_power_to_weight(v["engine"], v["weight"]["total_kg"])
    
    print(f"  Araç: {v['name']}")
    print(f"  Motor: {v['engine']} ({eng['power_hp']} HP)")
    print(f"  Ağırlık: {v['weight']['total_kg']} kg")
    print(f"  Güç/Ağırlık: {ptw['power_to_weight_kW_per_kg']:.3f} kW/kg")
    print(f"  Boyut: {v['dimensions']['length_mm']} x {v['dimensions']['width_mm']} mm")
    print(f"  Kategori: {v['category']}")

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print(f"\n{Colors.BOLD}🔧 FORMULA STUDENT ARAÇ ANALİZİ 🔧{Colors.END}")
    print(f"{Colors.BOLD}   {VEHICLE['name']} - {VEHICLE['category']}{Colors.END}\n")
    
    analyze_chassis(VEHICLE)
    analyze_engine(VEHICLE)
    analyze_fs_compliance(VEHICLE)
    analyze_suspension(VEHICLE)
    analyze_brakes(VEHICLE)
    analyze_aero(VEHICLE)
    analyze_tires(VEHICLE)
    analyze_dynamics(VEHICLE)
    analyze_scoring(VEHICLE)
    analyze_fuel(VEHICLE)
    
    summary(VEHICLE)
    
    print(f"\n{Colors.GREEN}{'='*50}")
    print(f"  ✓ ANALİZ TAMAMLANDI")
    print(f"{'='*50}{Colors.END}\n")