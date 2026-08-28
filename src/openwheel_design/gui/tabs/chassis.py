"""Sasi (chassis) sekmesi — boru govde analizi."""

from ..base_tab import BaseTab, COLORS

from openwheel_design.modules.chassis.materials import get_material, calculate_tube_weight
from openwheel_design.modules.chassis.analyses import (
    calculate_section_modulus, calculate_bending_stress,
)
from openwheel_design.modules.chassis.safety import calculate_rollbar_force
from openwheel_design.modules.chassis.constraints import check_fs_compliance


# Ekranda gorunen Turkce etiket -> materials.py'nin taniyacagi malzeme kodu
MATERIAL_LABELS = {
    "4130 Kromoli Celik": "4130",
    "Aluminyum 7075-T6": "al7075",
    "Karbon Fiber": "carbon_fiber",
}


class ChassisTab(BaseTab):
    tab_title = "Sasi"

    def build_form(self):
        c = self.profile.get("chassis", {})
        self.add_double("tube_od", "Boru Dis Capi", c.get("tube_od_mm", 25.4),
                         lo=10.0, hi=100.0, step=0.1, decimals=2, suffix="mm")
        self.add_double("wall", "Et Kalinligi", c.get("wall_mm", 1.6),
                         lo=0.5, hi=10.0, step=0.1, decimals=2, suffix="mm")
        self.add_double("length", "Toplam Boru Uzunlugu", c.get("length_mm", 5000.0),
                         lo=100.0, hi=20000.0, step=50.0, decimals=0, suffix="mm")
        default_idx = 1 if "7075" in c.get("material", "") or "aluminum" in c.get("material", "") else 0
        default_idx = 2 if "carbon" in c.get("material", "") else default_idx
        self.add_combo("material", "Malzeme", list(MATERIAL_LABELS.keys()), current=default_idx)

    def run_analysis(self):
        od = self.val("tube_od")
        wall = self.val("wall")
        length = self.val("length")
        material = MATERIAL_LABELS[self.val("material")]

        mat = get_material(material)
        if not mat:
            raise ValueError(f"Bilinmeyen malzeme: {material}")

        tube = calculate_tube_weight(od, wall, length, material)
        section_modulus_mm3 = calculate_section_modulus(od, wall)
        c_dist = od / 2.0
        moment_of_inertia_mm4 = section_modulus_mm3 * c_dist

        # Varsayimsal yukleme senaryosu: arac agirligina gore roll-bar kuvveti,
        # borunun ortasina etkiyen tekil yuk olarak alinir (M = F*L/4).
        vehicle_weight_kg = self.profile.get("dynamics", {}).get("mass_kg", 300.0)
        rollbar_force_N = calculate_rollbar_force(vehicle_weight_kg)
        moment_N_mm = rollbar_force_N * length / 4.0
        bending_stress_MPa = calculate_bending_stress(moment_N_mm, c_dist, moment_of_inertia_mm4)

        yield_strength_MPa = mat["yield_strength"]
        safety_factor = (yield_strength_MPa / bending_stress_MPa
                          if bending_stress_MPa > 0 else float("inf"))

        youngs_modulus_MPa = mat["youngs_modulus"]
        stiffness_N_per_mm = (48.0 * youngs_modulus_MPa * moment_of_inertia_mm4
                               / (length ** 3)) if length > 0 else 0.0

        fs_check = check_fs_compliance(weight=vehicle_weight_kg, length=length, width=1200)

        self.clear_chart()
        ax = self.new_axes()
        labels = ["Egilme Gerilmesi", "Akma Dayanimi"]
        values = [bending_stress_MPa, yield_strength_MPa]
        bars = ax.bar(labels, values, color=[COLORS[3], COLORS[1]])
        ax.set_ylabel("MPa")
        ax.set_title(f"{mat['name']} — Emniyet Katsayisi: {safety_factor:.2f}")
        for bar, v in zip(bars, values):
            ax.annotate(f"{v:.1f}", (bar.get_x() + bar.get_width() / 2, v),
                        ha="center", va="bottom", color="#d6e4f0")
        self.refresh_canvas()

        compliant_lines = "\n".join(
            f"  - {key}: {'UYGUN' if chk['compliant'] else 'UYGUN DEGIL'} "
            f"(deger={chk['value']}, limit={chk['constraint']})"
            for key, chk in fs_check["checks"].items()
        )

        text = (
            f"SASI ANALIZI\n"
            f"{'=' * 40}\n"
            f"Malzeme: {mat['name']}\n"
            f"Boru: OD {od:.2f} mm, Et Kalinligi {wall:.2f} mm, Uzunluk {length:.0f} mm\n\n"
            f"Agirlik: {tube['weight']:.3f} kg\n"
            f"Kesit Alani: {tube['cross_section_area'] * 1e6:.1f} mm2\n"
            f"Kesit Modulu (Z): {section_modulus_mm3:.1f} mm3\n"
            f"Atalet Momenti (I): {moment_of_inertia_mm4:.1f} mm4\n\n"
            f"Akma Dayanimi: {yield_strength_MPa:.1f} MPa\n"
            f"Elastisite Modulu: {youngs_modulus_MPa:.0f} MPa\n\n"
            f"Yukleme Senaryosu (roll-bar kuvveti, orta noktada tekil yuk):\n"
            f"  Kuvvet: {rollbar_force_N:.1f} N (arac agirligi {vehicle_weight_kg:.0f} kg icin)\n"
            f"  Moment: {moment_N_mm:.0f} N.mm\n"
            f"  Maks. Egilme Gerilmesi: {bending_stress_MPa:.2f} MPa\n"
            f"  Emniyet Katsayisi: {safety_factor:.2f}\n\n"
            f"Egilme Rijitligi: {stiffness_N_per_mm:.2f} N/mm\n\n"
            f"FS KURAL UYGUNLUGU: {'GECTI' if fs_check['passed'] else 'GECEMEDI'}\n"
            f"{compliant_lines}\n"
        )
        self.show_results(text)
