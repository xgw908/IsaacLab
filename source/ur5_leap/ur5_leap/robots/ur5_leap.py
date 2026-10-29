# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""UR5 CB3 + LEAP Hand configurations with a shared 22-joint control interface.

``UR5_LEAP_CFG`` uses the official LEAP Hand v1 Full Right model.
``UR5_SIMPLE_LEAP_CFG`` uses the CordViP hand geometry and simplified collisions.
Both models retain the official UR5 CB3 and the converted CordViP mounting transform.
"""

import math
from pathlib import Path

import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import ArticulationCfg
from isaaclab.utils import clone

_ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"

UR5_LEAP_USD_PATH = _ASSETS_DIR / "combined/ur5_leap/generated/usd/ur5_leap.usd/ur5_leap/ur5_leap.usda"
UR5_SIMPLE_LEAP_USD_PATH = (
    _ASSETS_DIR / "combined/ur5_simple_leap/generated/usd/ur5_simple_leap.usd/ur5_simple_leap/ur5_simple_leap.usda"
)

UR5_JOINT_NAMES = [
    "shoulder_pan_joint",
    "shoulder_lift_joint",
    "elbow_joint",
    "wrist_1_joint",
    "wrist_2_joint",
    "wrist_3_joint",
]
LEAP_JOINT_NAMES = [f"leap_joint_{i}" for i in range(16)]

UR5_LEAP_CFG = ArticulationCfg(
    prim_path="{ENV_REGEX_NS}/Robot",
    spawn=sim_utils.UsdFileCfg(
        usd_path=str(UR5_LEAP_USD_PATH),
        activate_contact_sensors=False,
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0.0, 0.0, 0.0),
        joint_pos={
            "shoulder_pan_joint": 0.0,
            "shoulder_lift_joint": -math.pi / 2.0,
            "elbow_joint": 0.0,
            "wrist_1_joint": -math.pi / 2.0,
            "wrist_2_joint": 0.0,
            "wrist_3_joint": 0.0,
            "leap_joint_.*": 0.0,
        },
    ),
    actuators={
        "ur5_arm": ImplicitActuatorCfg(
            joint_names_expr=UR5_JOINT_NAMES[:3],
            effort_limit_sim=150.0,
            velocity_limit_sim=3.15,
            stiffness=100.0,
            damping=10.0,
        ),
        "ur5_wrist": ImplicitActuatorCfg(
            joint_names_expr=UR5_JOINT_NAMES[3:],
            effort_limit_sim=28.0,
            velocity_limit_sim=3.2,
            stiffness=80.0,
            damping=8.0,
        ),
        "leap_hand": ImplicitActuatorCfg(
            joint_names_expr=["leap_joint_.*"],
            effort_limit_sim=0.95,
            velocity_limit_sim=8.0,
            stiffness=3.0,
            damping=0.1,
        ),
    },
)
"""Official UR5 CB3 + official LEAP Hand v1 Full Right, in the working pose with an open hand."""

# Clone the shared controls and initial state so either model can be customized independently.
UR5_SIMPLE_LEAP_CFG = clone(UR5_LEAP_CFG)
UR5_SIMPLE_LEAP_CFG.spawn.usd_path = str(UR5_SIMPLE_LEAP_USD_PATH)
"""Official UR5 CB3 + CordViP simplified LEAP Hand, with the same controls as the full model."""
