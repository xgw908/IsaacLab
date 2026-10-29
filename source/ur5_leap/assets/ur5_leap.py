"""Configurations for UR5 CB3 + LEAP Hand robots.

Available configurations:

- UR5_LEAP_CFG
    Official UR5 CB3 + Official LEAP Hand v1 Right.
    High-fidelity model.

- UR5_SIMPLE_LEAP_CFG
    Official UR5 CB3 + CordViP simplified LEAP Hand.
    Lightweight model for training.

Both robots:
- 6 DoF UR5
- 16 DoF LEAP
- 22 revolute joints total
- identical joint names and control interface
"""

from pathlib import Path

import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import ArticulationCfg


# -----------------------------------------------------------------------------
# Asset paths
# -----------------------------------------------------------------------------

# This file:
# source/ur5_leap/assets/ur5_leap.py
ASSETS_DIR = Path(__file__).resolve().parent

UR5_LEAP_USD_PATH = (
    ASSETS_DIR
    / "combined"
    / "ur5_leap"
    / "generated"
    / "usd"
    / "ur5_leap.usd"
    / "ur5_leap"
    / "ur5_leap.usda"
)

UR5_SIMPLE_LEAP_USD_PATH = (
    ASSETS_DIR
    / "combined"
    / "ur5_simple_leap"
    / "generated"
    / "usd"
    / "ur5_simple_leap.usd"
    / "ur5_simple_leap"
    / "ur5_simple_leap.usda"
)


# -----------------------------------------------------------------------------
# Joint groups
# -----------------------------------------------------------------------------

UR5_JOINT_NAMES = [
    "shoulder_pan_joint",
    "shoulder_lift_joint",
    "elbow_joint",
    "wrist_1_joint",
    "wrist_2_joint",
    "wrist_3_joint",
]

LEAP_JOINT_NAMES = [
    f"leap_joint_{i}" for i in range(16)
]


# -----------------------------------------------------------------------------
# Shared initial state
# -----------------------------------------------------------------------------

# UR5 working pose + LEAP fully open.
DEFAULT_JOINT_POS = {
    "shoulder_pan_joint": 0.0,
    "shoulder_lift_joint": -1.5707963267948966,
    "elbow_joint": 0.0,
    "wrist_1_joint": -1.5707963267948966,
    "wrist_2_joint": 0.0,
    "wrist_3_joint": 0.0,

    "leap_joint_.*": 0.0,
}


# -----------------------------------------------------------------------------
# Shared actuator configuration
# -----------------------------------------------------------------------------

UR5_ARM_ACTUATOR_CFG = ImplicitActuatorCfg(
    joint_names_expr=[
        "shoulder_pan_joint",
        "shoulder_lift_joint",
        "elbow_joint",
    ],
    effort_limit_sim=150.0,
    velocity_limit_sim=3.15,
    stiffness=100.0,
    damping=10.0,
)

UR5_WRIST_ACTUATOR_CFG = ImplicitActuatorCfg(
    joint_names_expr=[
        "wrist_1_joint",
        "wrist_2_joint",
        "wrist_3_joint",
    ],
    effort_limit_sim=28.0,
    velocity_limit_sim=3.2,
    stiffness=80.0,
    damping=8.0,
)

LEAP_HAND_ACTUATOR_CFG = ImplicitActuatorCfg(
    joint_names_expr=[
        "leap_joint_.*",
    ],
    effort_limit_sim=0.95,
    velocity_limit_sim=8.0,
    stiffness=3.0,
    damping=0.1,
)


# -----------------------------------------------------------------------------
# High-fidelity model
# Official UR5 CB3 + Official LEAP Hand
# -----------------------------------------------------------------------------

UR5_LEAP_CFG = ArticulationCfg(
    prim_path="{ENV_REGEX_NS}/Robot",
    spawn=sim_utils.UsdFileCfg(
        usd_path=str(UR5_LEAP_USD_PATH),
        activate_contact_sensors=False,
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0.0, 0.0, 0.0),
        joint_pos=DEFAULT_JOINT_POS,
    ),
    actuators={
        "ur5_arm": UR5_ARM_ACTUATOR_CFG,
        "ur5_wrist": UR5_WRIST_ACTUATOR_CFG,
        "leap_hand": LEAP_HAND_ACTUATOR_CFG,
    },
)


# -----------------------------------------------------------------------------
# Simplified training model
# Official UR5 CB3 + CordViP simplified LEAP Hand
# -----------------------------------------------------------------------------

UR5_SIMPLE_LEAP_CFG = ArticulationCfg(
    prim_path="{ENV_REGEX_NS}/Robot",
    spawn=sim_utils.UsdFileCfg(
        usd_path=str(UR5_SIMPLE_LEAP_USD_PATH),
        activate_contact_sensors=False,
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0.0, 0.0, 0.0),
        joint_pos=DEFAULT_JOINT_POS,
    ),
    actuators={
        "ur5_arm": UR5_ARM_ACTUATOR_CFG,
        "ur5_wrist": UR5_WRIST_ACTUATOR_CFG,
        "leap_hand": LEAP_HAND_ACTUATOR_CFG,
    },
)
