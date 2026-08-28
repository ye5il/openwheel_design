"""Suspansiyon sekmesi — Ackermann geometrisi ve rol merkezi analizi."""

from ..base_tab import BaseTab, COLORS

from openwheel_design.modules.suspension.geometry import calculate_ackermann
from openwheel_design.modules.suspension.kinematics import (
    calculate_roll_center, calculate_instant_center,
)
from openwheel_design.modules.suspension.arb import optimize_arb


class SuspensionTab(BaseTab):
    tab_title = "Suspansiyon"

    def build_form(self):
        s = self.profile.get("suspension", {})
        self.add_double("track_width", "Iz Genisligi", s.get("track_width_mm", 1200.0),
                         lo=800.0, hi=2000.0, step=10.0, decimals=0, suffix="mm")
        self.add_double("wheelbase", "Dingil Mesafesi", s.get("wheelbase_mm", 1550.0),
                         lo=1000.0, hi=3000.0, step=10.0, decimals=0, suffix="mm")
        self.add_double("turn_radius", "Donus Yaricapi", s.get("turn_radius_mm", 4500.0),
                         lo=1000.0, hi=20000.0, step=100.0, decimals=0, suffix="mm")
        self.add_double("front_rs", "On Rol Rijitligi", s.get("front_roll_stiffness", 60.0),
                         lo=0.0, hi=100.0, step=1.0, decimals=1, suffix="%")
        self.add_double("rear_rs", "Arka Rol Rijitligi", s.get("rear_roll_stiffness", 40.0),
                         lo=0.0, hi=100.0, step=1.0, decimals=1, suffix="%")

    def run_analysis(self):
        track = self.val("track_width")
        wheelbase = self.val("wheelbase")
        turn_radius = self.val("turn_radius")
        front_rs = self.val("front_rs")
        rear_rs = self.val("rear_rs")

        ackermann = calculate_ackermann(wheelbase, track, turn_radius)

        # Varsayilan on suspansiyon (cift enine kol) noktalari, iz genisligine gore olceklenir.
        half_track = track / 2.0
        upper_inner = (200.0, 260.0)
        upper_outer = (half_track - 25.0, 300.0)
        lower_inner = (200.0, 100.0)
        lower_outer = (half_track - 25.0, 100.0)

        roll_center = calculate_roll_center(upper_inner, upper_outer,
                                             lower_inner, lower_outer, track)
        ic = calculate_instant_center(upper_inner, upper_outer,
                                       lower_inner, lower_outer)

        arb_balance = optimize_arb(front_rs, rear_rs)

        # --- Ackermann geometrisi cizimi (kus bakisi) ---
        self.clear_chart()
        ax = self.new_axes()

        center = (-turn_radius, 0.0)
        left_pivot = (-half_track, wheelbase)
        right_pivot = (half_track, wheelbase)

        ax.plot([-half_track, half_track], [0, 0], color=COLORS[2], linewidth=3,
                label="Arka Aks")
        ax.plot([-half_track, half_track], [wheelbase, wheelbase], color=COLORS[0],
                linewidth=3, label="On Aks")
        ax.plot([0, 0], [0, wheelbase], color="#585b70", linestyle="--", linewidth=1)

        ax.plot([center[0], left_pivot[0]], [center[1], left_pivot[1]],
                color=COLORS[1], linewidth=1.5, label="Ic Teker Yonu")
        ax.plot([center[0], right_pivot[0]], [center[1], right_pivot[1]],
                color=COLORS[3], linewidth=1.5, label="Dis Teker Yonu")
        ax.scatter(*center, color=COLORS[4], zorder=5, label="Donus Merkezi")

        ax.set_xlabel("mm (yanal)")
        ax.set_ylabel("mm (boyuna)")
        ax.set_title(f"Ackermann — Ic: {ackermann['inner_angle_deg']} deg, "
                     f"Dis: {ackermann['outer_angle_deg']} deg")
        ax.legend(fontsize=7, loc="upper left")
        ax.set_aspect("equal", adjustable="datalim")
        self.refresh_canvas()

        text = (
            f"SUSPANSIYON ANALIZI\n"
            f"{'=' * 40}\n"
            f"Iz Genisligi: {track:.0f} mm, Dingil Mesafesi: {wheelbase:.0f} mm, "
            f"Donus Yaricapi: {turn_radius:.0f} mm\n\n"
            f"ACKERMANN GEOMETRISI\n"
            f"  Ic Teker Acisi: {ackermann['inner_angle_deg']} deg\n"
            f"  Dis Teker Acisi: {ackermann['outer_angle_deg']} deg\n"
            f"  Ackermann Yuzdesi: %{ackermann['ackermann_percent']}\n"
            f"  Degerlendirme: {'IDEAL' if ackermann['ideal'] else 'IDEAL DEGIL'}\n\n"
            f"ROL MERKEZI (on, varsayilan enine kol geometrisi)\n"
            f"  Yukseklik: {roll_center['roll_center_height_mm']} mm\n"
            f"  Ani Merkez (IC): x={ic['ic_x_mm']} mm, z={ic['ic_z_mm']} mm\n"
            f"  Yorum: {roll_center.get('interpretation', '-')}\n\n"
            f"ROL RIJITLIGI DAGILIMI\n"
            f"  Mevcut On Pay: %{arb_balance['current_front_pct']}\n"
            f"  Hedef On Pay: %{arb_balance['target_front_pct']}\n"
            f"  Oneri: {arb_balance['recommendation']}\n"
        )
        self.show_results(text)
