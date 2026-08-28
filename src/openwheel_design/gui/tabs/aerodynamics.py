"""Aerodinamik sekmesi — downforce/drag hesabi ve hiz taramasi."""

from openwheel_design.modules.aerodynamics.forces import (
    calculate_downforce, calculate_drag, calculate_lift_to_drag,
)
from openwheel_design.modules.aerodynamics.drag_budget import compare_configs

from ..base_tab import BaseTab, COLORS


class AerodynamicsTab(BaseTab):
    tab_title = "Aerodinamik"

    def build_form(self):
        aero = self.profile.get("aerodynamics", {})
        self.add_double("wing_area_m2", "Kanat Alani (m^2)",
                         aero.get("wing_area_m2", 0.5), 0.05, 5.0, 0.05, 2)
        self.add_double("speed_kmh", "Hiz", aero.get("speed_kmh", 80.0),
                         10, 300, 5, 1, "km/h")
        self.add_double("CL", "Downforce Katsayisi (CL)", 2.5, 0.1, 6.0, 0.1, 2)
        self.add_double("CD", "Surukleme Katsayisi (CD)", 1.2, 0.1, 4.0, 0.1, 2)
        self.add_double("air_density", "Hava Yogunlugu", 1.225,
                         0.8, 1.5, 0.005, 3, "kg/m^3")

    def run_analysis(self):
        area = self.val("wing_area_m2")
        speed = self.val("speed_kmh")
        CL = self.val("CL")
        CD = self.val("CD")
        rho = self.val("air_density")

        downforce_N = calculate_downforce(CL, area, speed, rho)
        drag_N = calculate_drag(CD, area, speed, rho)
        ld = calculate_lift_to_drag(CL, CD)

        speeds = list(range(20, 151, 5))
        downforces = [calculate_downforce(CL, area, v, rho) for v in speeds]
        drags = [calculate_drag(CD, area, v, rho) for v in speeds]

        self.clear_chart()
        ax = self.new_axes()
        ax.plot(speeds, downforces, color=COLORS[0], label="Downforce (N)")
        ax.plot(speeds, drags, color=COLORS[3], label="Surukleme (N)")
        ax.axvline(speed, color=COLORS[2], linestyle="--", alpha=0.7)
        ax.set_xlabel("Hiz (km/h)")
        ax.set_ylabel("Kuvvet (N)")
        ax.set_title("Hiza Gore Aerodinamik Kuvvetler")
        ax.legend()
        self.refresh_canvas()

        alt_CD = round(CD * 0.8, 2)
        cmp = compare_configs(alt_CD, CD, speed, area)

        lines = [
            f"Hiz: {speed:.0f} km/h",
            f"Downforce: {downforce_N:.0f} N",
            f"Surukleme (Drag): {drag_N:.0f} N",
            f"L/D orani: {ld:.3f}",
            "",
            "Alternatif konfigurasyon karsilastirmasi (CD %20 dusuk):",
            f"  Alternatif CD={cmp['config_a_CD']}: {cmp['config_a_drag_N']:.1f} N surukleme",
            f"  Mevcut CD={cmp['config_b_CD']}: {cmp['config_b_drag_N']:.1f} N surukleme",
            f"  Potansiyel guc tasarrufu: {cmp['power_savings_kW']:.2f} kW",
        ]
        self.show_results("\n".join(lines))
