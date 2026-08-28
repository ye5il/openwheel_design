"""Fren sekmesi — fren kuvveti, pedal seyri ve on/arka dagilim analizi."""

import math

from openwheel_design.modules.brakes.system import (
    calculate_brake_force,
    calculate_brake_bias,
    check_pedal_travel,
)
from openwheel_design.modules.utils.constants import GRAVITY

from ..base_tab import BaseTab, COLORS


class BrakesTab(BaseTab):
    tab_title = "Fren"

    def build_form(self):
        eng = self.profile.get("engine", {})
        default_wheel_r = round(eng.get("tire_radius_m", 0.26) * 1000, 1)

        self.add_double("mc_bore_mm", "Ana Silindir Capi (mm)", 15.875,
                         lo=8.0, hi=40.0, step=0.1, decimals=3)
        self.add_double("caliper_bore_mm", "Kaliper Piston Capi (mm)", 30.0,
                         lo=10.0, hi=60.0, step=0.5, decimals=2)
        self.add_int("caliper_pistons", "Kaliper Piston Sayisi", 2, lo=1, hi=8)
        self.add_double("pad_area_mm2", "Balata Temas Alani (mm2)", 1200.0,
                         lo=100.0, hi=5000.0, step=10.0, decimals=1)
        self.add_double("rotor_diameter_mm", "Disk Capi (mm)", 220.0,
                         lo=150.0, hi=350.0, step=1.0, decimals=1)
        self.add_double("wheel_radius_mm", "Tekerlek Yaricapi (mm)", default_wheel_r,
                         lo=150.0, hi=400.0, step=1.0, decimals=1)
        self.add_double("pedal_ratio", "Pedal Orani", 5.0,
                         lo=1.0, hi=10.0, step=0.1, decimals=2)
        self.add_double("line_pressure_bar", "Hat Basinci (bar)", 50.0,
                         lo=5.0, hi=150.0, step=1.0, decimals=1)
        self.add_double("mu_pad", "Balata Surtunme Katsayisi", 0.45,
                         lo=0.2, hi=0.8, step=0.01, decimals=2)
        self.add_double("decel_g", "Frenleme Ivmesi (g)", 1.3,
                         lo=0.5, hi=2.5, step=0.1, decimals=2)

    def run_analysis(self):
        mc_bore = self.val("mc_bore_mm")
        caliper_bore = self.val("caliper_bore_mm")
        n_pistons = int(self.val("caliper_pistons"))
        pad_area = self.val("pad_area_mm2")
        rotor_d = self.val("rotor_diameter_mm")
        wheel_r = self.val("wheel_radius_mm")
        pedal_ratio = self.val("pedal_ratio")
        line_pressure = self.val("line_pressure_bar")
        mu_pad = self.val("mu_pad")
        decel_g = self.val("decel_g")

        rotor_radius_mm = rotor_d * 0.42
        piston_area_total = math.pi * (caliper_bore / 2) ** 2 * n_pistons

        force_result = calculate_brake_force(
            line_pressure, piston_area_total, mu_pad, rotor_radius_mm, wheel_r
        )

        travel_result = check_pedal_travel(
            mc_bore_mm=mc_bore,
            caliper_bore_mm=caliper_bore,
            n_pistons=n_pistons,
            n_calipers=4,
            pedal_ratio=pedal_ratio,
        )

        dyn = self.profile.get("dynamics", {})
        susp = self.profile.get("suspension", {})
        mass_kg = dyn.get("mass_kg", 300.0)
        front_pct = dyn.get("front_weight_pct", 0.48)
        cog_height = dyn.get("cog_height_mm", 300.0)
        wheelbase = susp.get("wheelbase_mm", 1550.0)

        front_weight_N = mass_kg * front_pct * GRAVITY
        rear_weight_N = mass_kg * (1 - front_pct) * GRAVITY

        bias_result = calculate_brake_bias(
            front_weight_N, rear_weight_N, decel_g, cog_height, wheelbase
        )

        pad_pressure_MPa = force_result["clamp_force_N"] / pad_area

        # ---- chart: brake force vs line pressure ----
        self.clear_chart()
        ax = self.new_axes()
        pressures = list(range(10, 101, 5))
        forces = [
            calculate_brake_force(p, piston_area_total, mu_pad, rotor_radius_mm, wheel_r)["brake_force_N"]
            for p in pressures
        ]
        ax.plot(pressures, forces, color=COLORS[0], marker="o", markersize=3)
        ax.axvline(line_pressure, color=COLORS[3], linestyle="--", linewidth=1.2,
                    label=f"Secili basinc: {line_pressure:.0f} bar")
        ax.set_xlabel("Hat Basinci (bar)")
        ax.set_ylabel("Fren Kuvveti (N)")
        ax.set_title("Fren Kuvveti - Hat Basinci")
        ax.legend()
        self.refresh_canvas()

        # ---- results ----
        lines = []
        lines.append("=== FREN KUVVETI ===")
        lines.append(f"Piston toplam alani: {piston_area_total:.1f} mm2")
        lines.append(f"Etkin disk yaricapi: {rotor_radius_mm:.1f} mm")
        lines.append(f"Kenetleme kuvveti: {force_result['clamp_force_N']:.0f} N")
        lines.append(f"Fren torku: {force_result['brake_torque_Nm']:.1f} Nm")
        lines.append(f"Tekerlekte fren kuvveti: {force_result['brake_force_N']:.0f} N")
        lines.append(f"Balata temas basinci (yaklasik): {pad_pressure_MPa:.2f} MPa")
        lines.append("")
        lines.append("=== PEDAL SEYRI ===")
        lines.append(f"Ana silindir hacmi: {travel_result['mc_volume_mm3']:.0f} mm3")
        lines.append(f"Kaliper toplam hacim ihtiyaci: {travel_result['total_caliper_volume_mm3']:.0f} mm3")
        lines.append(f"Pedal seyri: {travel_result['pedal_travel_mm']:.1f} mm")
        lines.append(f"Hacim yeterli mi: {'Evet' if travel_result['volume_sufficient'] else 'Hayir'}")
        lines.append(f"Not: {travel_result['note']}")
        lines.append("")
        lines.append("=== ON/ARKA DAGILIM ===")
        lines.append(f"Statik on agirlik: {front_weight_N:.0f} N, arka: {rear_weight_N:.0f} N")
        lines.append(f"Frenleme sirasinda dinamik on: {bias_result['dynamic_front_N']:.0f} N")
        lines.append(f"Frenleme sirasinda dinamik arka: {bias_result['dynamic_rear_N']:.0f} N")
        lines.append(f"Agirlik transferi: {bias_result['weight_transfer_N']:.0f} N")
        lines.append(f"Ideal on fren dagilimi: %{bias_result['ideal_front_bias_pct']:.1f}")
        if "warning" in bias_result:
            lines.append(f"UYARI: {bias_result['warning']}")

        self.show_results("\n".join(lines))
