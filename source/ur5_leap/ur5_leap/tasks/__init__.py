# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Register UR5 + LEAP tasks when the package or the Isaac Lab CLI entry point is imported."""

import gymnasium as gym

gym.register(
    id="Isaac-UR5-SimpleLEAP-Lift-Cube",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": "ur5_leap.tasks.lift.env_cfg:UR5SimpleLeapLiftEnvCfg",
        "rsl_rl_cfg_entry_point": "ur5_leap.tasks.lift.agents:UR5SimpleLeapLiftPPORunnerCfg",
        "default_agent": "rsl_rl",
    },
)
