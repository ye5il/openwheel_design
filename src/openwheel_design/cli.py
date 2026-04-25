#!/usr/bin/env python3
import sys
import argparse
from chassis.analyses import analyze_weight, reverse_engineer_weight, optimize_weight, analyze_stress
from chassis.constraints import check_fs_compliance, full_fs_compliance_check
from chassis.materials import list_materials, get_material
from chassis.geometry import list_tube_sizes, check_fs_dimensions
from chassis.safety import calculate_rollbar_force, calculate_harness_force
from engine.database import list_engines, get_engine, get_engine_specs
from engine.analyses import analyze_engine, optimize_engine_choice, analyze_performance
import suspension
import aerodynamics
import tires
import dynamics
import scoring
import transmission
import brakes
import fuel
import data_log
import lap_sim
import reporting
import ev_system
from engine.constraints import check_engine_displacement, check_intake_restrictor

def cmd_chassis_analyze(args):
    tubes = [(args.tube_od, args.wall, args.length)] if args.length else [(args.tube_od, args.wall)]
    result = analyze_weight(tubes, material=args.material)
    print(f"\n=== Chassis Weight Analysis ===")
    print(f"Material: {result['material']}")
    print(f"Total Weight: {result['total_weight']:.2f} kg")
    print(f"Total Length: {result['total_length']:.0f} mm")
    for tube in result['tubes']:
        print(f"  {tube['spec']}: {tube['weight']:.3f} kg")

def cmd_chassis_reverse(args):
    result = reverse_engineer_weight(args.target_weight, material=args.material, tube_od_mm=args.tube_od)
    print(f"\n=== Reverse Engineering ===")
    print(f"Target Weight: {args.target_weight} kg")
    print(f"Material: {result['material']}")
    print("\nPossible Configurations:")
    for cfg in result["possible_configurations"][:5]:
        print(f"  OD: {cfg['od']}mm, Wall: {cfg['wall']}mm -> {cfg['weight_per_m']:.3f} kg/m")

def cmd_chassis_optimize(args):
    result = optimize_weight(args.target_weight)
    print(f"\n=== Weight Optimization ===")
    print(f"Target: {args.target_weight} kg")
    print("\nOptimal Configurations:")
    for cfg in result["optimal_configurations"]:
        print(f"  {cfg['material']} - OD: {cfg['od']}mm, Wall: {cfg['wall']}mm, Length: {cfg['total_length_m']:.1f}m")

def cmd_engine_list(args):
    engines = list_engines(common_only=args.common)
    print(f"\n=== Available Engines ===")
    for key, name in engines.items():
        print(f"  {name}")

def cmd_engine_info(args):
    specs = get_engine_specs(args.engine)
    if not specs:
        print(f"Engine not found: {args.engine}")
        return
    print(f"\n=== {specs['name']} ===")
    for k, v in specs.items():
        print(f"  {k}: {v}")

def cmd_engine_analyze(args):
    result = analyze_performance(args.engine, args.weight, include_restrictor=args.restrictor > 0, restrictor_mm=args.restrictor)
    if "error" in result:
        print(result["error"])
        return
    print(f"\n=== Performance Analysis ({result['engine']}) ===")
    print(f"Vehicle Weight: {args.weight} kg")
    print(f"Power/Weight: {result['power_to_weight']['kW_per_kg']:.3f} kW/kg")
    if "with_restrictor" in result:
        r = result["with_restrictor"]
        print(f"With {r['restrictor_mm']}mm Restrictor: {r['estimated_power_hp']} HP ({r['power_lost_percent']}% loss)")

def cmd_fs_check(args):
    result = check_fs_compliance(args.weight, args.length, args.width)
    print(f"\n=== FSAE Compliance ===")
    print(f"Passed: {result['passed']}")
    for check, data in result['checks'].items():
        status = "✓" if data['compliant'] else "✗"
        print(f"  {check}: {data['value']} (max: {data['constraint']}) {status}")

def main():
    parser = argparse.ArgumentParser(description="Openwheel Design Assistant")
    subparsers = parser.add_subparsers()
    
    p_chassis = subparsers.add_parser("chassis")
    p_chassis_sub = p_chassis.add_subparsers()
    
    sp = p_chassis_sub.add_parser("analyze")
    sp.add_argument("--tube-od", type=float, required=True, help="Tube outer diameter (mm)")
    sp.add_argument("--wall", type=float, default=1.6, help="Wall thickness (mm)")
    sp.add_argument("--length", type=float, default=1000, help="Tube length (mm)")
    sp.add_argument("--material", default="4130", help="Material type")
    sp.set_defaults(func=cmd_chassis_analyze)
    
    sp = p_chassis_sub.add_parser("reverse")
    sp.add_argument("--target-weight", type=float, required=True, help="Target weight (kg)")
    sp.add_argument("--material", default="4130", help="Material type")
    sp.add_argument("--tube-od", type=float, default=25.4, help="Tube OD (mm)")
    sp.set_defaults(func=cmd_chassis_reverse)
    
    sp = p_chassis_sub.add_parser("optimize")
    sp.add_argument("--target-weight", type=float, required=True, help="Target weight (kg)")
    sp.set_defaults(func=cmd_chassis_optimize)
    
    sp = p_chassis_sub.add_parser("list-materials")
    sp.set_defaults(func=lambda args: [print(f"  {k}: {v}") for k, v in list_materials().items()])
    
    sp = p_chassis_sub.add_parser("list-tubes")
    sp.set_defaults(func=lambda args: [print(f"  {t}") for t in list_tube_sizes()])
    
    p_engine = subparsers.add_parser("engine")
    p_engine_sub = p_engine.add_subparsers()
    
    sp = p_engine_sub.add_parser("list")
    sp.add_argument("--common", action="store_true", help="Show only common FS engines")
    sp.set_defaults(func=cmd_engine_list)
    
    sp = p_engine_sub.add_parser("info")
    sp.add_argument("engine", help="Engine name")
    sp.set_defaults(func=cmd_engine_info)
    
    sp = p_engine_sub.add_parser("analyze")
    sp.add_argument("engine", help="Engine name")
    sp.add_argument("--weight", type=float, required=True, help="Vehicle weight (kg)")
    sp.add_argument("--restrictor", type=float, default=0, help="Intake restrictor diameter (mm)")
    sp.set_defaults(func=cmd_engine_analyze)
    
    sp = p_engine_sub.add_parser("optimize")
    sp.add_argument("--weight", type=float, required=True, help="Vehicle weight (kg)")
    sp.add_argument("--target", default="power_to_weight", help="Optimization target")
    sp.set_defaults(func=lambda args: print(optimize_engine_choice(args.weight, args.target)))
    
    p_fs = subparsers.add_parser("fs-check")
    p_fs.add_argument("--weight", type=float, required=True, help="Vehicle weight (kg)")
    p_fs.add_argument("--length", type=float, required=True, help="Vehicle length (mm)")
    p_fs.add_argument("--width", type=float, required=True, help="Vehicle width (mm)")
    p_fs.set_defaults(func=cmd_fs_check)
    
    p_susp = subparsers.add_parser("suspension")
    p_susp_sub = p_susp.add_subparsers()
    
    sp = p_susp_sub.add_parser("geometry")
    sp.add_argument("--camber", type=float, default=-2.5, help="Camber angle (deg)")
    sp.add_argument("--toe", type=float, default=1.0, help="Toe (mm)")
    sp.add_argument("--caster", type=float, default=6.0, help="Caster angle (deg)")
    sp.add_argument("--axle", default="front", help="Front or rear")
    sp.set_defaults(func=lambda args: print(suspension.check_camber(args.camber, args.axle)))
    
    sp = p_susp_sub.add_parser("ackermann")
    sp.add_argument("--wheelbase", type=float, default=1600, help="Wheelbase (mm)")
    sp.add_argument("--track", type=float, default=1200, help="Track width (mm)")
    sp.add_argument("--turn-radius", type=float, default=5000, help="Turn radius (mm)")
    sp.set_defaults(func=lambda args: print(suspension.calculate_ackermann(args.wheelbase, args.track, args.turn_radius)))
    
    sp = p_susp_sub.add_parser("wheel-rate")
    sp.add_argument("--spring-rate", type=float, required=True, help="Spring rate (N/mm)")
    sp.add_argument("--motion-ratio", type=float, default=0.75, help="Motion ratio")
    sp.set_defaults(func=lambda args: print(suspension.calculate_wheel_rate(args.spring_rate, args.motion_ratio)))
    
    p_aero = subparsers.add_parser("aero")
    p_aero_sub = p_aero.add_subparsers()
    
    sp = p_aero_sub.add_parser("downforce")
    sp.add_argument("--CL", type=float, default=2.0, help="Lift coefficient")
    sp.add_argument("--area", type=float, default=1.2, help="Reference area (m²)")
    sp.add_argument("--speed", type=float, default=80, help="Speed (km/h)")
    sp.set_defaults(func=lambda args: print(f"Downforce: {aerodynamics.calculate_downforce(args.CL, args.area, args.speed)} N"))
    
    sp = p_aero_sub.add_parser("drag")
    sp.add_argument("--CD", type=float, default=1.5, help="Drag coefficient")
    sp.add_argument("--area", type=float, default=1.2, help="Reference area (m²)")
    sp.add_argument("--speed", type=float, default=80, help="Speed (km/h)")
    sp.set_defaults(func=lambda args: print(f"Drag: {aerodynamics.calculate_drag(args.CD, args.area, args.speed)} N"))
    
    p_tire = subparsers.add_parser("tires")
    p_tire_sub = p_tire.add_subparsers()
    
    sp = p_tire_sub.add_parser("temp")
    sp.add_argument("--temp", type=float, required=True, help="Tire temperature (°C)")
    sp.add_argument("--compound", default="medium", help="Compound (soft/medium/hard)")
    sp.set_defaults(func=lambda args: print(tires.check_tire_temperature(args.temp, args.compound)))
    
    sp = p_tire_sub.add_parser("pressure")
    sp.add_argument("--bar", type=float, required=True, help="Tire pressure (bar)")
    sp.add_argument("--axle", default="front", help="Front or rear")
    sp.set_defaults(func=lambda args: print(tires.check_tire_pressure(args.bar, args.axle)))
    
    p_dyn = subparsers.add_parser("dynamics")
    p_dyn_sub = p_dyn.add_subparsers()
    
    sp = p_dyn_sub.add_parser("load-transfer")
    sp.add_argument("--mass", type=float, required=True, help="Vehicle mass (kg)")
    sp.add_argument("--lateral-g", type=float, default=1.5, help="Lateral g")
    sp.add_argument("--cog", type=float, required=True, help="CoG height (mm)")
    sp.add_argument("--track", type=float, required=True, help="Track width (mm)")
    sp.set_defaults(func=lambda args: print(dynamics.calculate_lateral_load_transfer(args.mass, args.lateral_g, args.cog, args.track)))
    
    sp = p_dyn_sub.add_parser("balance")
    sp.add_argument("--front-cs", type=float, required=True, help="Front cornering stiffness")
    sp.add_argument("--rear-cs", type=float, required=True, help="Rear cornering stiffness")
    sp.add_argument("--front-weight", type=float, required=True, help="Front weight (N)")
    sp.add_argument("--rear-weight", type=float, required=True, help="Rear weight (N)")
    sp.set_defaults(func=lambda args: print(dynamics.calculate_understeer_gradient(args.front_cs, args.rear_cs, args.front_weight, args.rear_weight)))
    
    p_score = subparsers.add_parser("scoring")
    p_score_sub = p_score.add_subparsers()
    
    sp = p_score_sub.add_parser("acceleration")
    sp.add_argument("--your-time", type=float, required=True, help="Your time (s)")
    sp.add_argument("--best-time", type=float, required=True, help="Best time (s)")
    sp.add_argument("--max-time", type=float, required=True, help="Max time (s)")
    sp.set_defaults(func=lambda args: print(f"Score: {scoring.score_acceleration(args.your_time, args.best_time, args.max_time)}"))
    
    sp = p_score_sub.add_parser("endurance")
    sp.add_argument("--your-time", type=float, required=True, help="Your time (s)")
    sp.add_argument("--best-time", type=float, required=True, help="Best time (s)")
    sp.set_defaults(func=lambda args: print(f"Score: {scoring.score_endurance(args.your_time, args.best_time)}"))
    
    p_fs_full = subparsers.add_parser("fs-check-full")
    p_fs_full.add_argument("--weight", type=float, required=True)
    p_fs_full.add_argument("--length", type=float, required=True)
    p_fs_full.add_argument("--width", type=float, required=True)
    p_fs_full.add_argument("--displacement", type=float, default=600)
    p_fs_full.add_argument("--restrictor", type=float, default=20)
    p_fs_full.add_argument("--fuel-tank", type=float, default=8)
    p_fs_full.add_argument("--rollbar-od", type=float, default=25.4)
    p_fs_full.add_argument("--rollbar-wall", type=float, default=2.4)
    p_fs_full.add_argument("--cockpit-width", type=float, default=350)
    p_fs_full.add_argument("--cockpit-height", type=float, default=580)
    p_fs_full.set_defaults(func=lambda args: print(chassis.full_fs_compliance_check({
        "weight": args.weight, "length": args.length, "width": args.width,
        "displacement": args.displacement, "restrictor": args.restrictor,
        "fuel_tank": args.fuel_tank, "rollbar_od": args.rollbar_od,
        "rollbar_wall": args.rollbar_wall, "cockpit_width": args.cockpit_width,
        "cockpit_height": args.cockpit_height
    })))
    
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()