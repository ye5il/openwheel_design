"""Ozet Panosu — tum modullerden hizli bir arac ozeti."""

import math

from PySide6.QtWidgets import QLabel

from openwheel_design.modules.chassis.analyses import analyze_weight
from openwheel_design.modules.engine.database import get_engine
from openwheel_design.modules.engine.constraints import calculate_restricted_power
from openwheel_design.modules.engine.analyses import calculate_0_100_estimation
from openwheel_design.modules.aerodynamics.forces import calculate_downforce
from openwheel_design.modules.scoring.events import (
    score_acceleration,
    score_skidpad,
    score_autocross,
    score_endurance,
    MAX_POINTS,
)
from openwheel_design.modules.utils.constants import FS_MIN_WEIGHT

from ..base_tab import BaseTab, COLORS

# Ozet panosunda kullanilan varsayimlar (profilde karsiligi olmayan degerler)
ASSUMED_CL = 2.5           # kanat takimi kaldirma katsayisi tahmini
DYNAMIC_MAX = (
    MAX_POINTS["acceleration"] + MAX_POINTS["skidpad"]
    + MAX_POINTS["autocross"] + MAX_POINTS["endurance"]
)

# vehicle_profile.py varsayilan malzeme anahtarlari (orn. "4130_steel") ile
# chassis.materials.get_material()'in tanidigi anahtarlar birebir eslesmiyor;
# burada guvenli bir eslestirme yapiyoruz.
_MATERIAL_MAP = {
    "4130_steel": "4130",
    "4130": "4130",
    "chromoly": "4130",
    "al7075": "al7075",
    "aluminum": "al7075",
    "7075": "al7075",
    "carbon_fiber": "carbon_fiber",
    "carbon": "carbon_fiber",
}


def _normalize_material(material_key: str) -> str:
    return _MATERIAL_MAP.get(material_key, "4130")


class SummaryTab(BaseTab):
    tab_title = "Ozet Panosu"

    def build_form(self):
        p = self.profile
        chassis = p.get("chassis", {})
        engine = p.get("engine", {})
        dynamics = p.get("dynamics", {})
        suspension = p.get("suspension", {})
        aero = p.get("aerodynamics", {})

        self.form_layout.addRow(QLabel("<b>Arac Profili (ozet)</b>"))
        self.form_layout.addRow("Takim / Model:",
                                 QLabel(str(p.get("meta", {}).get("name", "-"))))
        self.form_layout.addRow("Motor:", QLabel(str(engine.get("engine_key", "-"))))
        self.form_layout.addRow("Restriktor:",
                                 QLabel(f"{engine.get('restrictor_mm', '-')} mm"))
        self.form_layout.addRow("Sase Borusu:",
                                 QLabel(f"{chassis.get('tube_od_mm', '-')} x "
                                        f"{chassis.get('wall_mm', '-')} mm, "
                                        f"{chassis.get('length_mm', '-')} mm"))
        self.form_layout.addRow("Sase Malzemesi:", QLabel(str(chassis.get("material", "-"))))
        self.form_layout.addRow("Arac Kutlesi:", QLabel(f"{dynamics.get('mass_kg', '-')} kg"))
        self.form_layout.addRow("Agirlik Merkezi:",
                                 QLabel(f"{dynamics.get('cog_height_mm', '-')} mm"))
        self.form_layout.addRow("Dingil Mesafesi:",
                                 QLabel(f"{suspension.get('wheelbase_mm', '-')} mm"))
        self.form_layout.addRow("Iz Genisligi:",
                                 QLabel(f"{suspension.get('track_width_mm', '-')} mm"))
        self.form_layout.addRow("Kanat Alani:",
                                 QLabel(f"{aero.get('wing_area_m2', '-')} m2"))
        self.form_layout.addRow(QLabel(""))
        note = QLabel("Degerleri degistirmek icin diger sekmeleri veya\n"
                       "Dosya > Profil Ac/Kaydet menusunu kullanin.")
        note.setWordWrap(True)
        self.form_layout.addRow(note)

    def run_analysis(self):
        p = self.profile
        chassis = p.get("chassis", {})
        engine_cfg = p.get("engine", {})
        dynamics = p.get("dynamics", {})
        aero = p.get("aerodynamics", {})
        scoring_cfg = p.get("scoring", {})

        mass_kg = dynamics.get("mass_kg", 300.0)

        # ---- sase agirligi (tek boru temsili hesap) ----
        weight_result = analyze_weight(
            [(chassis.get("tube_od_mm", 25.4),
              chassis.get("wall_mm", 1.6),
              chassis.get("length_mm", 5000.0))],
            material=_normalize_material(chassis.get("material", "4130")),
        )
        frame_weight_kg = weight_result["total_weight"]

        # ---- motor / kisitlanmis guc ----
        engine_key = engine_cfg.get("engine_key", "Honda_CBR600RR")
        eng = get_engine(engine_key)
        stock_hp = eng["power_hp"] if eng else 0.0
        restrictor_mm = engine_cfg.get("restrictor_mm", 20.0)
        restricted_hp = (
            calculate_restricted_power(restrictor_mm, stock_hp) if eng else 0.0
        )

        # ---- 0-100 tahmini ----
        accel_0_100 = None
        if eng:
            perf = calculate_0_100_estimation(
                engine_key, mass_kg,
                gear_ratio=engine_cfg.get("gear_ratio", 2.5),
                final_drive=engine_cfg.get("final_drive", 3.5),
                tire_radius_m=engine_cfg.get("tire_radius_m", 0.26),
            )
            if perf:
                accel_0_100 = perf["estimated_0_100_kmh"]

        # ---- downforce ----
        downforce_N = calculate_downforce(
            ASSUMED_CL, aero.get("wing_area_m2", 0.5), aero.get("speed_kmh", 80.0)
        )

        # ---- puanlama tahmini (varsayilan referans sureler ile) ----
        accel_pts = score_acceleration(scoring_cfg.get("accel_time_s", 4.5), 3.5)
        skidpad_pts = score_skidpad(scoring_cfg.get("skidpad_time_s", 5.5), 4.8)
        autocross_pts = score_autocross(scoring_cfg.get("autocross_time_s", 60.0), 50.0)
        endurance_pts = score_endurance(scoring_cfg.get("endurance_time_s", 1500.0), 1350.0)
        dynamic_total = accel_pts + skidpad_pts + autocross_pts + endurance_pts

        # ---- 0-100 normalized [0, 100] gostergeler ----
        weight_score = max(0.0, min(100.0, 100.0 - (mass_kg - FS_MIN_WEIGHT) * 0.5))
        power_score = max(0.0, min(100.0, restricted_hp))
        if accel_0_100:
            accel_score = max(0.0, min(100.0, 100.0 - (accel_0_100 - 3.0) * 15.0))
        else:
            accel_score = 0.0
        downforce_score = max(0.0, min(100.0, downforce_N / 20.0))
        scoring_score = dynamic_total / DYNAMIC_MAX * 100.0 if DYNAMIC_MAX else 0.0

        categories = ["Agirlik", "Guc", "0-100", "Downforce", "Puan"]
        values = [weight_score, power_score, accel_score, downforce_score, scoring_score]
        self._draw_radar(categories, values)

        # ---- results ----
        lines = []
        lines.append("=== ARAC OZETI ===")
        lines.append(f"Toplam kutle: {mass_kg:.0f} kg  (sase boru tahmini: {frame_weight_kg:.1f} kg)")
        lines.append(f"Motor: {eng['name'] if eng else 'bulunamadi'}  "
                      f"({stock_hp:.0f} hp fabrika)")
        lines.append(f"Restriktor sonrasi tahmini guc: {restricted_hp:.1f} hp "
                      f"({restrictor_mm:.0f} mm)")
        if accel_0_100:
            lines.append(f"0-100 km/s tahmini: {accel_0_100:.2f} s")
        else:
            lines.append("0-100 km/s tahmini: hesaplanamadi (motor bulunamadi)")
        lines.append(f"Kanat downforce (varsayilan CL={ASSUMED_CL}, "
                      f"{aero.get('speed_kmh', 80.0):.0f} km/s): {downforce_N:.0f} N")
        lines.append("")
        lines.append("=== TAHMINI PUANLAMA (dinamik) ===")
        lines.append(f"Ivmelenme:   {accel_pts:6.1f} / {MAX_POINTS['acceleration']}")
        lines.append(f"Skidpad:     {skidpad_pts:6.1f} / {MAX_POINTS['skidpad']}")
        lines.append(f"Autocross:   {autocross_pts:6.1f} / {MAX_POINTS['autocross']}")
        lines.append(f"Dayanikilik: {endurance_pts:6.1f} / {MAX_POINTS['endurance']}")
        lines.append(f"Toplam:      {dynamic_total:6.1f} / {DYNAMIC_MAX}")
        lines.append("")
        lines.append("Not: Grafikteki degerler her kategori icin 0-100 araliginda")
        lines.append("normalize edilmis gostergelerdir, mutlak degerler degildir.")
        lines.append("Guc, downforce ve puan tahminleri modullerdeki basitlestirilmis")
        lines.append("modellere dayanir; kesin muhendislik hesabi yerine gecmez.")

        self.show_results("\n".join(lines))

    def _draw_radar(self, categories, values):
        self.clear_chart()
        n = len(categories)
        angles = [i / n * 2 * math.pi for i in range(n)]
        angles.append(angles[0])
        vals = list(values) + [values[0]]

        ax = self.new_axes(projection="polar")
        ax.plot(angles, vals, color=COLORS[0], linewidth=2, marker="o", markersize=4)
        ax.fill(angles, vals, color=COLORS[0], alpha=0.25)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 100)
        ax.set_title("Performans Gostergeleri (normalize, 0-100)")
        self.refresh_canvas()
