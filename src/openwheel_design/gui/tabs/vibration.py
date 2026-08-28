"""Titresim sekmesi — ceyrek arac (quarter-car) 2-DOF suspansiyon modeli."""

from openwheel_design.simulation.quarter_car import (
    QuarterCarParams,
    compute_natural_frequencies,
    compute_damping_ratios,
    simulate_time_response,
    compute_frequency_response,
    bump_input,
)

from ..base_tab import BaseTab, MPL_STYLE, COLORS


def _style_axes(ax):
    ax.set_facecolor(MPL_STYLE["axes.facecolor"])
    ax.tick_params(colors=MPL_STYLE["xtick.color"])
    ax.xaxis.label.set_color(MPL_STYLE["axes.labelcolor"])
    ax.yaxis.label.set_color(MPL_STYLE["axes.labelcolor"])
    ax.title.set_color(MPL_STYLE["text.color"])
    for spine in ax.spines.values():
        spine.set_color(MPL_STYLE["axes.edgecolor"])
    ax.grid(True, color=MPL_STYLE["grid.color"], alpha=float(MPL_STYLE["grid.alpha"]))


class VibrationTab(BaseTab):
    tab_title = "Titresim"

    def build_form(self):
        defaults = self.profile.get("vibration", {})

        self.add_double(
            "sprung_mass_kg", "Yaylanmis kutle", defaults.get("sprung_mass_kg", 60.0),
            lo=1.0, hi=500.0, step=1.0, decimals=1, suffix="kg",
        )
        self.add_double(
            "unsprung_mass_kg", "Yaylanmamis kutle",
            defaults.get("unsprung_mass_kg", 15.0),
            lo=1.0, hi=200.0, step=0.5, decimals=1, suffix="kg",
        )
        self.add_double(
            "spring_rate_N_mm", "Yay sertligi",
            defaults.get("spring_rate_N_mm", 25.0),
            lo=1.0, hi=500.0, step=1.0, decimals=2, suffix="N/mm",
        )
        self.add_double(
            "tire_rate_N_mm", "Lastik sertligi",
            defaults.get("tire_rate_N_mm", 150.0),
            lo=1.0, hi=1000.0, step=5.0, decimals=2, suffix="N/mm",
        )
        self.add_double(
            "damping_Ns_mm", "Amortisor sonumleme",
            defaults.get("damping_Ns_mm", 1.5),
            lo=0.0, hi=50.0, step=0.1, decimals=2, suffix="Ns/mm",
        )
        self.add_double(
            "bump_height_mm", "Tumsek yuksekligi",
            defaults.get("bump_height_mm", 25.0),
            lo=1.0, hi=200.0, step=1.0, decimals=1, suffix="mm",
        )

    def run_analysis(self):
        params = QuarterCarParams(
            sprung_mass_kg=self.val("sprung_mass_kg"),
            unsprung_mass_kg=self.val("unsprung_mass_kg"),
            spring_rate_N_per_m=self.val("spring_rate_N_mm") * 1000.0,
            damping_Ns_per_m=self.val("damping_Ns_mm") * 1000.0,
            tire_rate_N_per_m=self.val("tire_rate_N_mm") * 1000.0,
        )
        bump_height_m = self.val("bump_height_mm") / 1000.0

        nat_freq = compute_natural_frequencies(params)
        damping = compute_damping_ratios(params)

        road_func = bump_input(height_m=bump_height_m, width_m=0.3, speed_ms=10.0)
        time_resp = simulate_time_response(params, road_func, t_span=(0.0, 2.0), dt=0.001)
        freq_resp = compute_frequency_response(params)

        road_mm = [road_func(t) * 1000.0 for t in time_resp["time_s"]]

        self.clear_chart()
        ax1 = self.figure.add_subplot(211)
        ax2 = self.figure.add_subplot(212)
        _style_axes(ax1)
        _style_axes(ax2)

        # ---- ust grafik: frekans tepkisi ----
        ax1.plot(
            freq_resp["frequency_hz"], freq_resp["displacement_gain"],
            color=COLORS[0],
        )
        ax1.set_xscale("log")
        ax1.axvline(
            freq_resp["body_resonance_hz"], color=COLORS[3], linestyle="--",
            label=f"Govde rezonansi: {freq_resp['body_resonance_hz']} Hz",
        )
        ax1.axvline(
            freq_resp["wheel_resonance_hz"], color=COLORS[4], linestyle="--",
            label=f"Teker rezonansi: {freq_resp['wheel_resonance_hz']} Hz",
        )
        ax1.set_xlabel("Frekans (Hz)")
        ax1.set_ylabel("Yer degistirme kazanci")
        ax1.set_title("Frekans Tepkisi")
        ax1.legend(
            loc="best", fontsize=8,
            facecolor=MPL_STYLE["legend.facecolor"],
            edgecolor=MPL_STYLE["legend.edgecolor"],
            labelcolor=MPL_STYLE["axes.labelcolor"],
        )

        # ---- alt grafik: zaman tepkisi (tumsek gecisi) ----
        ax2.plot(
            time_resp["time_s"], time_resp["sprung_disp_mm"],
            color=COLORS[0], label="Govde (yaylanmis)",
        )
        ax2.plot(
            time_resp["time_s"], time_resp["unsprung_disp_mm"],
            color=COLORS[1], label="Teker (yaylanmamis)",
        )
        ax2.plot(
            time_resp["time_s"], road_mm,
            color=COLORS[2], linestyle=":", label="Yol profili",
        )
        ax2.set_xlabel("Zaman (s)")
        ax2.set_ylabel("Yer degistirme (mm)")
        ax2.set_title("Tumsek Gecisi — Zaman Tepkisi")
        ax2.legend(
            loc="best", fontsize=8,
            facecolor=MPL_STYLE["legend.facecolor"],
            edgecolor=MPL_STYLE["legend.edgecolor"],
            labelcolor=MPL_STYLE["axes.labelcolor"],
        )

        self.refresh_canvas()

        lines = [
            f"Govde modu (body mode): {nat_freq['body_mode_hz']} Hz",
            f"Teker sekmesi (wheel hop): {nat_freq['wheel_hop_hz']} Hz",
            f"Frekans orani: {nat_freq['frequency_ratio']}",
            f"Govde sonumleme orani (zeta): {damping['body_damping_ratio']}",
            f"Teker sonumleme orani (zeta): {damping['wheel_damping_ratio']}",
            f"Kritik sonumlu mu: {'Evet' if damping['body_critically_damped'] else 'Hayir'}",
            f"Degerlendirme: {damping['recommendation']}",
        ]
        self.show_results("\n".join(lines))
