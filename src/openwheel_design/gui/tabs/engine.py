"""Motor sekmesi — motor secimi, restriktor ve performans analizi."""

from ..base_tab import BaseTab, COLORS

from openwheel_design.modules.engine.database import (
    get_engine, list_engines, calculate_power_to_weight,
)
from openwheel_design.modules.engine.constraints import estimate_power_with_restrictor
from openwheel_design.modules.engine.analyses import calculate_0_100_estimation


class EngineTab(BaseTab):
    tab_title = "Motor"

    def build_form(self):
        e = self.profile.get("engine", {})
        engine_keys = list(list_engines(common_only=True).keys())
        if not engine_keys:
            engine_keys = list(list_engines().keys())
        default_key = e.get("engine_key", engine_keys[0])
        default_idx = engine_keys.index(default_key) if default_key in engine_keys else 0
        self.add_combo("engine_key", "Motor", engine_keys, current=default_idx)
        self.add_double("restrictor", "Restriktor Capi", e.get("restrictor_mm", 20.0),
                         lo=15.0, hi=30.0, step=0.5, decimals=1, suffix="mm")
        self.add_double("gear_ratio", "Vites Orani", e.get("gear_ratio", 2.5),
                         lo=1.0, hi=10.0, step=0.1, decimals=2)
        self.add_double("final_drive", "Ana Redüksiyon", e.get("final_drive", 3.5),
                         lo=1.0, hi=10.0, step=0.1, decimals=2)
        self.add_double("tire_radius", "Lastik Yaricapi", e.get("tire_radius_m", 0.26),
                         lo=0.15, hi=0.40, step=0.005, decimals=3, suffix="m")

    def run_analysis(self):
        key = self.val("engine_key")
        eng = get_engine(key)
        if not eng:
            raise ValueError(f"Motor bulunamadi: {key}")

        restrictor_mm = self.val("restrictor")
        gear_ratio = self.val("gear_ratio")
        final_drive = self.val("final_drive")
        tire_radius_m = self.val("tire_radius")

        restricted = estimate_power_with_restrictor(key, restrictor_mm)

        vehicle_weight_kg = self.profile.get("dynamics", {}).get("mass_kg", 300.0)
        ptw = calculate_power_to_weight(key, vehicle_weight_kg)

        perf = calculate_0_100_estimation(
            key, vehicle_weight_kg,
            gear_ratio=gear_ratio, final_drive=final_drive,
            tire_radius_m=tire_radius_m,
        )

        self.clear_chart()
        ax = self.new_axes()
        labels = ["Stok Guc", "Restriktorlu Guc"]
        values = [restricted["stock_power_hp"], restricted["estimated_power_hp"]]
        bars = ax.bar(labels, values, color=[COLORS[0], COLORS[4]])
        ax.set_ylabel("hp")
        ax.set_title(f"{eng['name']} — %{restricted['power_lost_percent']} guc kaybi")
        for bar, v in zip(bars, values):
            ax.annotate(f"{v:.1f}", (bar.get_x() + bar.get_width() / 2, v),
                        ha="center", va="bottom", color="#d6e4f0")
        self.refresh_canvas()

        text = (
            f"MOTOR ANALIZI\n"
            f"{'=' * 40}\n"
            f"Motor: {eng['name']} ({eng['year']})\n"
            f"Hacim: {eng['displacement_cc']} cc, {eng['cylinders']} silindir\n"
            f"Stok Guc: {eng['power_hp']} hp @ {eng['power_rpm']} rpm\n"
            f"Tork: {eng['torque_Nm']} Nm @ {eng['torque_rpm']} rpm\n"
            f"Agirlik: {eng['weight_kg']} kg\n"
            f"Sikistirma Orani: {eng['compression']}:1\n"
            f"Sogutma: {eng['cooling']}\n\n"
            f"RESTRIKTOR ANALIZI ({restrictor_mm:.1f} mm)\n"
            f"  Stok Guc: {restricted['stock_power_hp']} hp\n"
            f"  Tahmini Guc: {restricted['estimated_power_hp']} hp\n"
            f"  Guc Kaybi: %{restricted['power_lost_percent']}\n\n"
            f"GUC/AGIRLIK ORANI (arac {vehicle_weight_kg:.0f} kg)\n"
            f"  {ptw['power_to_weight_kW_per_kg']} kW/kg  "
            f"({ptw['power_to_weight_hp_per_kg']} hp/kg)\n\n"
            f"0-100 KM/S TAHMINI\n"
            f"  Vites Orani: {perf['gear_ratio']}, Ana Reduksiyon: {perf['final_drive']}\n"
            f"  Lastik Yaricapi: {perf['tire_radius_m']} m\n"
            f"  Tahmini Sure: {perf['estimated_0_100_kmh']} s\n"
            f"  Not: {perf['note']}\n"
        )
        self.show_results(text)
