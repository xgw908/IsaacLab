# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""PPO settings based on the maintained contributed cube-lift example."""

from isaaclab.utils import configclass

from isaaclab_tasks.contrib.lift.config.franka.agents.rsl_rl_ppo_cfg import LiftCubePPORunnerCfg


@configclass
class UR5SimpleLeapLiftPPORunnerCfg(LiftCubePPORunnerCfg):
    """Train the 22 position actions with state observations."""

    experiment_name = "ur5_simple_leap_lift_cube"
    num_steps_per_env = 32
    max_iterations = 3000
    clip_actions = 1.0
    obs_groups = {"actor": ["policy"], "critic": ["policy"]}
