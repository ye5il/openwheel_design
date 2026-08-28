"""Puanlama sekmesi — dinamik etkinlik puanlarinin tahmini."""

from openwheel_design.modules.scoring.events import (
    score_acceleration,
    score_skidpad,
    score_autocross,
    score_endurance,
    MAX_POINTS,
)

from ..base_tab import BaseTab, COLORS


class ScoringTab(BaseTab):
    tab_title = "Puanlama"

    def build_form(self):
        self.add_double("accel_time_s", "Ivmelenme Suresi (s)", 4.5,
                         lo=2.0, hi=15.0, step=0.1, decimals=2)
        self.add_double("skidpad_time_s", "Skidpad Suresi (s)", 5.5,
                         lo=3.0, hi=15.0, step=0.1, decimals=2)
        self.add_double("autocross_time_s", "Autocross Suresi (s)", 60.0,
                         lo=30.0, hi=150.0, step=0.5, decimals=2)
        self.add_double("endurance_time_s", "Dayanikilik Suresi (s)", 1500.0,
                         lo=600.0, hi=3000.0, step=5.0, decimals=1)
        self.add_double("best_accel_s", "En Iyi Ivmelenme (s)", 3.5,
                         lo=2.0, hi=15.0, step=0.1, decimals=2)
        self.add_double("best_skidpad_s", "En Iyi Skidpad (s)", 4.8,
                         lo=3.0, hi=15.0, step=0.1, decimals=2)
        self.add_double("best_autocross_s", "En Iyi Autocross (s)", 50.0,
                         lo=30.0, hi=150.0, step=0.5, decimals=2)
        self.add_double("best_endurance_s", "En Iyi Dayanikilik (s)", 1350.0,
                         lo=600.0, hi=3000.0, step=5.0, decimals=1)

    def run_analysis(self):
        accel_t = self.val("accel_time_s")
        skidpad_t = self.val("skidpad_time_s")
        autocross_t = self.val("autocross_time_s")
        endurance_t = self.val("endurance_time_s")

        best_accel = self.val("best_accel_s")
        best_skidpad = self.val("best_skidpad_s")
        best_autocross = self.val("best_autocross_s")
        best_endurance = self.val("best_endurance_s")

        accel_pts = score_acceleration(accel_t, best_accel)
        skidpad_pts = score_skidpad(skidpad_t, best_skidpad, skidpad_t * 1.45)
        autocross_pts = score_autocross(autocross_t, best_autocross)
        endurance_pts = score_endurance(endurance_t, best_endurance)

        events = ["Ivmelenme", "Skidpad", "Autocross", "Dayanikilik"]
        points = [accel_pts, skidpad_pts, autocross_pts, endurance_pts]
        max_points = [
            MAX_POINTS["acceleration"],
            MAX_POINTS["skidpad"],
            MAX_POINTS["autocross"],
            MAX_POINTS["endurance"],
        ]

        dynamic_total = sum(points)
        dynamic_max = sum(max_points)

        # ---- chart: horizontal bar, points vs max ----
        self.clear_chart()
        ax = self.new_axes()
        y_pos = list(range(len(events)))
        ax.barh(y_pos, max_points, color="#132f4c", label="Maksimum puan")
        ax.barh(y_pos, points, color=COLORS[0], label="Alinan puan")
        for i, (pts, mx) in enumerate(zip(points, max_points)):
            ax.text(mx + dynamic_max * 0.01, i, f"{pts:.1f}/{mx}",
                    va="center", fontsize=8, color="#d6e4f0")
        ax.set_yticks(y_pos)
        ax.set_yticklabels(events)
        ax.invert_yaxis()
        ax.set_xlabel("Puan")
        ax.set_title("Dinamik Etkinlik Puanlari")
        ax.legend(loc="lower right", fontsize=8)
        self.refresh_canvas()

        # ---- results ----
        lines = []
        lines.append("=== ETKINLIK PUANLARI ===")
        lines.append(f"Ivmelenme:    {accel_pts:6.1f} / {MAX_POINTS['acceleration']}")
        lines.append(f"Skidpad:      {skidpad_pts:6.1f} / {MAX_POINTS['skidpad']}")
        lines.append(f"Autocross:    {autocross_pts:6.1f} / {MAX_POINTS['autocross']}")
        lines.append(f"Dayanikilik:  {endurance_pts:6.1f} / {MAX_POINTS['endurance']}")
        lines.append("")
        lines.append(f"Dinamik toplam: {dynamic_total:.1f} / {dynamic_max}")
        lines.append(f"Dinamik puanlarin yuzdesi: %{dynamic_total / dynamic_max * 100:.1f}")
        lines.append("")
        lines.append("Not: Statik puanlar (verimlilik, maliyet, tasarim, sunum) bu")
        lines.append("hesaba dahil degildir; toplam FS puani 1000 uzerindendir.")

        self.show_results("\n".join(lines))
