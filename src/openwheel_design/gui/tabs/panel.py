"""Kanat Profili sekmesi — 2D panel yontemi ile NACA profil analizi."""

from openwheel_design.simulation.panel_2d import analyze_airfoil, estimate_drag_friction

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


class PanelTab(BaseTab):
    tab_title = "Kanat Profili"

    def build_form(self):
        defaults = self.profile.get("aerodynamics", {})

        codes = ["0012", "2412", "4415", "6412"]
        default_code = str(defaults.get("naca_code", "2412"))
        current = codes.index(default_code) if default_code in codes else 1
        self.add_combo("naca_code", "NACA kodu", codes, current=current)

        self.add_double(
            "alpha_deg", "Hucum acisi (alpha)", defaults.get("alpha_deg", 5.0),
            lo=-10.0, hi=20.0, step=0.5, decimals=1, suffix="derece",
        )
        self.add_int(
            "n_panels", "Panel sayisi", int(defaults.get("n_panels", 100)),
            lo=20, hi=300,
        )
        self.add_double(
            "Re", "Reynolds sayisi", 500000.0,
            lo=10000.0, hi=10000000.0, step=10000.0, decimals=0,
        )

    def run_analysis(self):
        naca_code = self.val("naca_code")
        alpha_deg = self.val("alpha_deg")
        n_panels = int(self.val("n_panels"))
        Re = self.val("Re")

        result = analyze_airfoil(naca_code, alpha_deg=alpha_deg, n_panels=n_panels)
        drag = estimate_drag_friction(result["coords"], alpha_deg, Re)

        self.clear_chart()
        ax1 = self.figure.add_subplot(211)
        ax2 = self.figure.add_subplot(212)
        _style_axes(ax1)
        _style_axes(ax2)

        # ---- ust grafik: basinc katsayisi dagilimi ----
        cp_upper = [-c for c in result["Cp_upper"]]
        cp_lower = [-c for c in result["Cp_lower"]]
        ax1.plot(result["x_upper"], cp_upper, color=COLORS[0], label="Ust yuzey")
        ax1.plot(result["x_lower"], cp_lower, color=COLORS[1], label="Alt yuzey")
        ax1.set_xlabel("x/c")
        ax1.set_ylabel("-Cp")
        ax1.set_title(f"NACA {naca_code} — Basinc Katsayisi (alpha={alpha_deg}°)")
        ax1.legend(
            loc="best", fontsize=8,
            facecolor=MPL_STYLE["legend.facecolor"],
            edgecolor=MPL_STYLE["legend.edgecolor"],
            labelcolor=MPL_STYLE["axes.labelcolor"],
        )

        # ---- alt grafik: kanat profili sekli ----
        coords = result["coords"]
        ax2.plot(coords[:, 0], coords[:, 1], color=COLORS[2])
        ax2.set_xlabel("x/c")
        ax2.set_ylabel("y/c")
        ax2.set_title("Profil Sekli")
        ax2.set_aspect("equal", adjustable="box")

        self.refresh_canvas()

        cd_friction = drag["Cd_friction"]
        l_over_d = result["CL"] / cd_friction if cd_friction > 1e-12 else float("inf")

        lines = [
            f"CL: {result['CL']}",
            f"Cm (c/4): {result['Cm_c4']}",
            f"CL_alpha: {result['CL_alpha_per_deg']} / derece "
            f"({result['CL_alpha_per_rad']} / rad)",
            f"Cd (surtunme): {cd_friction}",
            f"L/D (surtunmeye gore): {round(l_over_d, 2)}",
            f"Gecis noktasi (ust/alt): {drag['transition_x_upper']} / "
            f"{drag['transition_x_lower']} (x/c)",
        ]
        self.show_results("\n".join(lines))
