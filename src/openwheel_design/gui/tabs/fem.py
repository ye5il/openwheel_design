"""Sasi FEM sekmesi — 3D kiris (beam) elemanli burulma rijitligi analizi."""

from openwheel_design.simulation.frame_fem import (
    create_simple_spaceframe,
    TubeSection,
    analyze_torsional_rigidity,
)
from openwheel_design.modules.chassis.materials import MATERIALS

from ..base_tab import BaseTab, MPL_STYLE, COLORS


# Profildeki "4130_steel" gibi kullanici dostu isimleri gercek
# MATERIALS anahtarlarina esler.
_MATERIAL_MAP = {"4130_steel": "4130"}


class FEMTab(BaseTab):
    tab_title = "Sasi FEM"

    def build_form(self):
        defaults = self.profile.get("fem", {})

        self.add_double(
            "tube_od_mm", "Boru dis capi", defaults.get("tube_od_mm", 25.4),
            lo=5.0, hi=100.0, step=0.1, decimals=2, suffix="mm",
        )
        self.add_double(
            "wall_mm", "Et kalinligi", defaults.get("wall_mm", 1.6),
            lo=0.5, hi=10.0, step=0.1, decimals=2, suffix="mm",
        )
        self.add_combo(
            "material", "Malzeme", list(_MATERIAL_MAP.keys()), current=0,
        )
        self.add_double(
            "E_GPa", "Elastisite modulu (E)", 205.0,
            lo=50.0, hi=500.0, step=5.0, decimals=0, suffix="GPa",
        )
        self.add_double(
            "yield_MPa", "Akma dayanimi", 560.0,
            lo=50.0, hi=3000.0, step=10.0, decimals=0, suffix="MPa",
        )
        self.add_double(
            "force_N", "Uygulanan kuvvet", 1000.0,
            lo=0.0, hi=50000.0, step=100.0, decimals=0, suffix="N",
        )

    def run_analysis(self):
        tube_od_mm = self.val("tube_od_mm")
        wall_mm = self.val("wall_mm")
        material_key = _MATERIAL_MAP.get(self.val("material"), "4130")
        E_GPa = self.val("E_GPa")
        yield_MPa = self.val("yield_MPa")
        force_N = self.val("force_N")

        section = TubeSection(od_mm=tube_od_mm, wall_mm=wall_mm)
        nodes, elements, _default_section = create_simple_spaceframe()

        # Kullanicinin girdigi E / akma degerlerini gecici olarak malzeme
        # tablosuna yaz — analyze_torsional_rigidity malzeme ozelliklerini
        # dogrudan MATERIALS tablosundan (get_material uzerinden) okuyor.
        original = dict(MATERIALS[material_key])
        MATERIALS[material_key]["youngs_modulus"] = E_GPa * 1000.0  # GPa -> MPa
        MATERIALS[material_key]["yield_strength"] = yield_MPa
        try:
            result = analyze_torsional_rigidity(
                nodes, elements, section, material_key,
                front_susp_nodes=[0, 1], rear_susp_nodes=[8, 9],
                applied_force_N=force_N,
            )
        finally:
            MATERIALS[material_key].update(original)

        # ---- grafik: en yuksek gerilmeli 15 eleman ----
        elem_stresses = result["element_stresses"]
        top = sorted(
            elem_stresses, key=lambda s: s["von_mises_stress_MPa"], reverse=True
        )[:15]
        labels = [str(s["element_index"]) for s in top]
        values = [s["von_mises_stress_MPa"] for s in top]

        self.clear_chart()
        ax = self.new_axes()
        ax.bar(labels, values, color=COLORS[0])
        ax.axhline(
            yield_MPa, color=COLORS[3], linestyle="--",
            label=f"Akma siniri ({yield_MPa:.0f} MPa)",
        )
        ax.set_xlabel("Eleman indeksi")
        ax.set_ylabel("Von Mises gerilmesi (MPa)")
        ax.set_title("En Yuksek Gerilmeli 15 Eleman")
        ax.legend(
            loc="upper right", fontsize=8,
            facecolor=MPL_STYLE["legend.facecolor"],
            edgecolor=MPL_STYLE["legend.edgecolor"],
            labelcolor=MPL_STYLE["axes.labelcolor"],
        )
        self.refresh_canvas()

        # ---- sonuc metni ----
        lines = [
            f"Burulma rijitligi: {result['torsional_rigidity_Nm_per_deg']} Nm/derece",
            f"Burulma acisi: {result['twist_angle_deg']} derece",
            f"Uygulanan tork: {result['applied_torque_Nm']} Nm",
            f"Maksimum yer degistirme: {result['max_displacement_mm']} mm",
            f"Maksimum gerilme (von Mises): {result['max_stress_MPa']} MPa",
            f"Emniyet katsayisi: {result['safety_factor']}",
        ]
        if result["safety_factor"] < 1.5:
            lines.append(
                "Uyari: emniyet katsayisi dusuk, boru kesitini veya "
                "malzemeyi guclendirmeyi dusunun."
            )
        self.show_results("\n".join(lines))
