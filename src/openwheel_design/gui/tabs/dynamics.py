"""Dinamik sekmesi — yuk transferi, kose yukleri ve agirlik dagilimi."""

from openwheel_design.modules.dynamics.load_transfer import (
    calculate_lateral_load_transfer, calculate_longitudinal_load_transfer,
    calculate_wheel_loads,
)
from openwheel_design.modules.dynamics.weight_dist import calculate_weight_distribution

from ..base_tab import BaseTab, COLORS


class DynamicsTab(BaseTab):
    tab_title = "Dinamik"

    def build_form(self):
        dyn = self.profile.get("dynamics", {})
        susp = self.profile.get("suspension", {})
        self.add_double("mass_kg", "Arac Kutlesi",
                         dyn.get("mass_kg", 300.0), 100, 500, 5, 1, "kg")
        self.add_double("cog_height_mm", "Agirlik Merkezi Yuksekligi",
                         dyn.get("cog_height_mm", 300.0), 150, 600, 5, 1, "mm")
        self.add_double("wheelbase_mm", "Dingil Mesafesi",
                         susp.get("wheelbase_mm", 1550.0), 1200, 1900, 10, 0, "mm")
        self.add_double("track_width_mm", "Iz Genisligi",
                         susp.get("track_width_mm", 1200.0), 900, 1500, 10, 0, "mm")
        front_pct_default = round(dyn.get("front_weight_pct", 0.48) * 100, 1)
        self.add_double("front_weight_pct", "On Agirlik Orani",
                         front_pct_default, 30, 70, 0.5, 1, "%")
        self.add_double("lateral_g", "Yanal Ivme", 1.5, 0.0, 3.0, 0.1, 2, "g")
        self.add_double("longitudinal_g", "Boyuna Ivme", 1.0, 0.0, 3.0, 0.1, 2, "g")
        self.add_double("front_roll_stiffness_pct", "On Rulman Sertligi Orani",
                         susp.get("front_roll_stiffness", 60.0), 0, 100, 1, 0, "%")

    def run_analysis(self):
        mass = self.val("mass_kg")
        cog = self.val("cog_height_mm")
        wheelbase = self.val("wheelbase_mm")
        track = self.val("track_width_mm")
        front_pct = self.val("front_weight_pct")
        lat_g = self.val("lateral_g")
        long_g = self.val("longitudinal_g")
        front_roll_pct = self.val("front_roll_stiffness_pct")

        lat_transfer = calculate_lateral_load_transfer(mass, lat_g, cog, track)
        long_transfer = calculate_longitudinal_load_transfer(mass, long_g, cog, wheelbase)
        wheel_loads = calculate_wheel_loads(
            mass, front_pct, cog, track, wheelbase,
            lat_g=lat_g, long_g=long_g,
            front_roll_stiffness_pct=front_roll_pct,
        )

        front_mass = mass * front_pct / 100
        rear_mass = mass - front_mass
        dist = calculate_weight_distribution(
            [front_mass, rear_mass], [0, wheelbase], wheelbase
        )

        self.clear_chart()
        ax = self.new_axes()
        labels = ["FL", "FR", "RL", "RR"]
        values = [wheel_loads["FL_N"], wheel_loads["FR_N"],
                  wheel_loads["RL_N"], wheel_loads["RR_N"]]
        bar_colors = [COLORS[0], COLORS[1], COLORS[2], COLORS[3]]
        ax.bar(labels, values, color=bar_colors)
        ax.set_ylabel("Tekerlek Yuku (N)")
        ax.set_title("Kose Yukleri")
        self.refresh_canvas()

        lines = [
            f"Yanal yuk transferi: {lat_transfer['load_transfer_N']:.0f} N ({lat_g:.2f} g)",
            f"Boyuna yuk transferi: {long_transfer['load_transfer_N']:.0f} N ({long_g:.2f} g)",
            "",
            "Kose yukleri:",
            f"  On-Sol (FL): {wheel_loads['FL_N']:.0f} N",
            f"  On-Sag (FR): {wheel_loads['FR_N']:.0f} N",
            f"  Arka-Sol (RL): {wheel_loads['RL_N']:.0f} N",
            f"  Arka-Sag (RR): {wheel_loads['RR_N']:.0f} N",
            "",
            f"Agirlik dagilimi: on %{dist['front_pct']:.1f} / arka %{dist['rear_pct']:.1f}",
        ]
        self.show_results("\n".join(lines))
