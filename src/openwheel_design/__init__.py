"""
openwheel_design
Formula Student araç tasarım ve analiz kütüphanesi
"""

__version__ = "1.0.0"
__author__ = "Openwheel Design Team"
__email__ = "contact@openwheel.design"
__license__ = "MIT"

from openwheel_design.modules.chassis import (
    analyze_weight,
    reverse_engineer_weight,
    check_fs_compliance,
    get_material,
)

from openwheel_design.modules.engine import (
    get_engine,
    list_engines,
    analyze_performance,
)

from openwheel_design.modules.suspension import (
    check_camber,
    calculate_ackermann,
    calculate_wheel_rate,
)

from openwheel_design.modules.aerodynamics import (
    calculate_downforce,
    calculate_drag,
    calculate_lift_to_drag,
)

from openwheel_design.modules.tires import (
    check_tire_temperature,
    check_tire_pressure,
)

from openwheel_design.modules.dynamics import (
    calculate_lateral_load_transfer,
    calculate_understeer_gradient,
)

from openwheel_design.modules.brakes import calculate_brake_bias

from openwheel_design.modules.scoring import (
    score_acceleration,
    score_endurance,
)

from openwheel_design.modules.fuel import (
    estimate_endurance_fuel,
    check_fuel_tank_rule,
)

__all__ = [
    "__version__",
    "analyze_weight",
    "reverse_engineer_weight",
    "check_fs_compliance",
    "get_engine",
    "list_engines",
    "analyze_performance",
    "check_camber",
    "calculate_ackermann",
    "calculate_wheel_rate",
    "calculate_downforce",
    "calculate_drag",
    "calculate_lift_to_drag",
    "check_tire_temperature",
    "check_tire_pressure",
    "calculate_lateral_load_transfer",
    "calculate_understeer_gradient",
    "calculate_brake_bias",
    "score_acceleration",
    "score_endurance",
    "estimate_endurance_fuel",
    "check_fuel_tank_rule",
]