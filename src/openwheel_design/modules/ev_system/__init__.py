EV_MOTORS = {
    "EMRAX_228": {"name": "EMRAX 228", "type": "AXIAL", "max_power_kW": 150, "max_torque_Nm": 250, "max_rpm": 6000, "weight_kg": 18},
    "EMRAX_268": {"name": "EMRAX 268", "type": "AXIAL", "max_power_kW": 220, "max_torque_Nm": 350, "max_rpm": 5000, "weight_kg": 28},
    "PMSM_100kW": {"name": "Generic PMSM 100kW", "type": "RADIAL", "max_power_kW": 100, "max_torque_Nm": 200, "max_rpm": 8000, "weight_kg": 15},
}

BATTERY_PACKS = {
    "LFP_600V_15kWh": {"chemistry": "LiFePO4", "voltage_V": 600, "capacity_Ah": 25, "modules": 200, "weight_kg": 120},
    "LFP_600V_10kWh": {"chemistry": "LiFePO4", "voltage_V": 600, "capacity_Ah": 17, "modules": 200, "weight_kg": 85},
    "NMC_400V_20kWh": {"chemistry": "NMC", "voltage_V": 400, "capacity_Ah": 50, "modules": 108, "weight_kg": 100},
}

def get_ev_motor(name):
    return EV_MOTORS.get(name)

def get_battery(name):
    return BATTERY_PACKS.get(name)

def list_ev_motors():
    return {k: v["name"] for k, v in EV_MOTORS.items()}

def list_batteries():
    return {k: v["chemistry"] + " " + str(v["voltage_V"]) + "V" for k, v in BATTERY_PACKS.items()}

def calculate_range(battery_kWh, avg_power_kW, speed_kmh):
    hours = battery_kWh / avg_power_kW
    return round(hours * speed_kmh, 1)

def calculate_power_consumption(speed_kmh, drag_CD, area_m2, mass_kg):
    import math
    v = speed_kmh / 3.6
    rho = 1.225
    drag = 0.5 * rho * v**2 * drag_CD * area_m2
    roll = mass_kg * 9.81 * 0.015
    return round((drag + roll) / 1000, 2)

def check_ev_safety(voltage_V, isolation_ohm_per_V):
    return {
        "voltage_V": voltage_V,
        "isolation_ok": isolation_ohm_per_V >= 500,
        "compliant": voltage_V <= 600 and isolation_ohm_per_V >= 500,
        "rule": "EV4.1 max 600V"
    }

__all__ = ['EV_MOTORS', 'BATTERY_PACKS', 'get_ev_motor', 'get_battery', 
           'list_ev_motors', 'list_batteries', 'calculate_range',
           'calculate_power_consumption', 'check_ev_safety']