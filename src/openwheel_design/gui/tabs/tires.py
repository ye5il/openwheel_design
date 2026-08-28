"""Lastik sekmesi — soguk basinc tahmini ve traksiyon cemberi."""

import math

from openwheel_design.modules.tires.thermal_model import estimate_cold_pressure
from openwheel_design.modules.tires.force_model import (
    calculate_max_lateral_force, calculate_traction_circle,
)

from ..base_tab import BaseTab, COLORS


class TiresTab(BaseTab):
    tab_title = "Lastik"

    def build_form(self):
        tires = self.profile.get("tires", {})
        engine = self.profile.get("engine", {})
        self.add_double("hot_pressure_bar", "Sicak Basinc",
                         tires.get("hot_pressure_bar", 0.83), 0.3, 2.5, 0.01, 2, "bar")
        self.add_double("hot_temp_c", "Sicak Sicaklik",
                         tires.get("hot_temp_c", 80.0), 20, 150, 1, 1, "C")
        self.add_double("cold_temp_c", "Soguk (Ortam) Sicaklik",
                         tires.get("cold_temp_c", 20.0), -10, 50, 1, 1, "C")
        self.add_double("mu", "Surtunme Katsayisi (mu)", 1.5, 0.5, 2.5, 0.05, 2)
        self.add_double("tire_radius_m", "Lastik Yaricapi",
                         engine.get("tire_radius_m", 0.26), 0.15, 0.4, 0.01, 3, "m")
        self.add_double("load_N", "Dusey Yuk", 1500.0, 100, 5000, 50, 0, "N")

    def run_analysis(self):
        hot_bar = self.val("hot_pressure_bar")
        hot_c = self.val("hot_temp_c")
        cold_c = self.val("cold_temp_c")
        mu = self.val("mu")
        radius = self.val("tire_radius_m")
        load_N = self.val("load_N")

        cold_pressure_bar = estimate_cold_pressure(hot_bar, cold_c, hot_c)
        max_N = calculate_max_lateral_force(load_N, mu)
        max_torque_Nm = round(max_N * radius, 1)

        sample_long = round(max_N * 0.7, 1)
        sample_lat = round(max_N * 0.7, 1)
        circle_check = calculate_traction_circle(sample_lat, sample_long, max_N)

        self.clear_chart()
        ax = self.new_axes()
        theta = [i * 2 * math.pi / 200 for i in range(201)]
        xs = [max_N * math.cos(t) for t in theta]
        ys = [max_N * math.sin(t) for t in theta]
        ax.plot(xs, ys, color=COLORS[0], label=f"Traksiyon Siniri (mu={mu})")
        ax.scatter([sample_long], [sample_lat], color=COLORS[3], zorder=5,
                   label="Ornek Calisma Noktasi")
        ax.axhline(0, color="#1e4976", linewidth=0.8)
        ax.axvline(0, color="#1e4976", linewidth=0.8)
        ax.set_xlabel("Boyuna Kuvvet (N)")
        ax.set_ylabel("Yanal Kuvvet (N)")
        ax.set_title("Traksiyon Cemberi")
        ax.set_aspect("equal", adjustable="box")
        ax.legend()
        self.refresh_canvas()

        lines = [
            f"Soguk basinc tahmini: {cold_pressure_bar:.2f} bar "
            f"(sicak: {hot_bar:.2f} bar @ {hot_c:.0f} C)",
            f"Maksimum kuvvet (mu x yuk): {max_N:.0f} N",
            f"Maksimum tahmini tork kapasitesi: {max_torque_Nm:.1f} Nm "
            f"(yaricap {radius:.3f} m)",
            "",
            f"Ornek calisma noktasi -> boyuna: {sample_long:.0f} N, "
            f"yanal: {sample_lat:.0f} N",
            f"  Bilesik kuvvet: {circle_check['combined_force_N']:.0f} N",
            f"  Kullanim orani: {circle_check['utilization_pct']:.1f}%",
            f"  Sinir icinde: {'Evet' if circle_check['within_limit'] else 'Hayir'}",
        ]
        self.show_results("\n".join(lines))
