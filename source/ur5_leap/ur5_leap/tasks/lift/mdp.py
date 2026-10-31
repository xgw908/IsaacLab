# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Observation, shaping and sustained-lift success terms for the first learning task."""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from typing import TYPE_CHECKING

import torch

from isaaclab.managers import ManagerTermBase, SceneEntityCfg
from isaaclab.utils.math import quat_apply_inverse, subtract_frame_transforms

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv
    from isaaclab.managers import TerminationTermCfg

CUBE_SIZE = 0.04
TABLE_HEIGHT = 0.15
CUBE_REST_HEIGHT = TABLE_HEIGHT + CUBE_SIZE / 2.0
LIFT_HEIGHT = 0.10
FINGERTIP_NAMES = ["fingertip", "fingertip_2", "fingertip_3", "thumb_fingertip"]
CHECK_FINITE_OBSERVATIONS = os.environ.get("UR5_LEAP_CHECK_FINITE", "0") == "1"


def require_finite_observation(data: torch.Tensor, term_name: str) -> torch.Tensor:
    """Report the first non-finite observation term when opt-in diagnostics are enabled."""
    invalid = ~torch.isfinite(data)
    if invalid.any():
        indices = invalid.nonzero(as_tuple=False)[:8].tolist()
        values = data[invalid][:8].tolist()
        raise ValueError(
            f"UR5 LEAP: policy.{term_name} contains NaN/Inf. "
            f"First [environment, column] indices: {indices}; values: {values}."
        )
    return data


def checked_joint_positions(env: ManagerBasedRLEnv, asset_cfg: SceneEntityCfg) -> torch.Tensor:
    """Diagnose raw state and applied targets when the debug joint observation becomes non-finite."""
    robot = env.scene[asset_cfg.name]
    positions = robot.data.joint_pos.torch[:, asset_cfg.joint_ids]
    defaults = robot.data.default_joint_pos.torch[:, asset_cfg.joint_ids]
    relative = positions - defaults
    invalid = ~torch.isfinite(relative)
    if invalid.any():
        env_ids = invalid.any(dim=-1).nonzero(as_tuple=False).flatten()[:4].tolist()
        _, names = robot.find_joints(asset_cfg.joint_names, preserve_order=asset_cfg.preserve_order)
        actions = env.action_manager.action
        targets = {name: env.action_manager.get_term(name).processed_actions for name in ("arm", "hand")}
        # Observation shapes can be inspected before episode bookkeeping buffers are initialized.
        episode_steps = getattr(env, "episode_length_buf", None)
        rows = []
        for env_id in env_ids:
            bad_columns = invalid[env_id].nonzero(as_tuple=False).flatten().tolist()
            rows.append(
                {
                    "environment": env_id,
                    "episode_step": int(episode_steps[env_id]) if episode_steps is not None else None,
                    "invalid_joints": [names[index] for index in bad_columns],
                    "joint_pos_finite": bool(torch.isfinite(positions[env_id]).all()),
                    "default_joint_pos_finite": bool(torch.isfinite(defaults[env_id]).all()),
                    "joint_pos": positions[env_id].tolist(),
                    "default_joint_pos": defaults[env_id].tolist(),
                    "joint_vel": robot.data.joint_vel.torch[env_id, asset_cfg.joint_ids].tolist(),
                    "environment_origin": env.scene.env_origins[env_id].tolist(),
                    "root_pose_w": robot.data.root_pose_w.torch[env_id].tolist(),
                    "actions_finite": bool(torch.isfinite(actions[env_id]).all()),
                    "actions": actions[env_id].tolist(),
                    "targets_finite": {
                        name: bool(torch.isfinite(value[env_id]).all()) for name, value in targets.items()
                    },
                    "targets": {name: value[env_id].tolist() for name, value in targets.items()},
                }
            )
        raise ValueError(
            f"UR5 LEAP: policy.joint_pos contains NaN/Inf at control step "
            f"{getattr(env, 'common_step_counter', None)}; "
            f"{int(invalid.any(dim=-1).sum())}/{env.num_envs} environments affected. "
            f"State/action details (up to 4 environments): {json.dumps(rows)}"
        )
    return relative


def validate_hand_action_limits(
    env: ManagerBasedRLEnv,
    env_ids: torch.Tensor | slice | None,
    asset_cfg: SceneEntityCfg,
) -> None:
    """Check once that USD hand limits can be used to map normalized policy actions."""
    robot = env.scene[asset_cfg.name]
    limits = robot.data.soft_joint_pos_limits.torch[:, asset_cfg.joint_ids]
    invalid = ~torch.isfinite(limits).all(dim=-1) | (limits[..., 0] >= limits[..., 1])
    if invalid.any():
        env_id, joint_index = invalid.nonzero(as_tuple=False)[0].tolist()
        _, names = robot.find_joints(asset_cfg.joint_names, preserve_order=asset_cfg.preserve_order)
        hard_limits = robot.data.joint_pos_limits.torch[:, asset_cfg.joint_ids]
        raise ValueError(
            f"UR5 LEAP: invalid action limits for {names[joint_index]!r} in environment {env_id}. "
            f"USD limits: {hard_limits[env_id, joint_index].tolist()}; "
            f"soft limits: {limits[env_id, joint_index].tolist()}. "
            "JointPositionToLimitsAction requires finite lower < upper bounds."
        )


def object_state_b(env: ManagerBasedRLEnv) -> torch.Tensor:
    """Cube position, xyzw quaternion and velocities in the fixed robot root frame: (N, 13)."""
    robot = env.scene["robot"]
    obj = env.scene["object"]
    root_pos = robot.data.root_pos_w.torch
    root_quat = robot.data.root_quat_w.torch
    pos, quat = subtract_frame_transforms(root_pos, root_quat, obj.data.root_pos_w.torch, obj.data.root_quat_w.torch)
    lin_vel = quat_apply_inverse(root_quat, obj.data.root_lin_vel_w.torch)
    ang_vel = quat_apply_inverse(root_quat, obj.data.root_ang_vel_w.torch)
    return torch.cat((pos, quat, lin_vel, ang_vel), dim=-1)


def hand_positions_b(env: ManagerBasedRLEnv, robot_cfg: SceneEntityCfg) -> torch.Tensor:
    """Selected hand link origins expressed in the fixed robot root frame: (N, 3 * links)."""
    robot = env.scene[robot_cfg.name]
    positions = robot.data.body_pos_w.torch[:, robot_cfg.body_ids] - robot.data.root_pos_w.torch[:, None, :]
    rotations = robot.data.root_quat_w.torch[:, None, :].expand(-1, positions.shape[1], -1)
    return quat_apply_inverse(rotations, positions).reshape(env.num_envs, -1)


def _tip_distances(env: ManagerBasedRLEnv, robot_cfg: SceneEntityCfg) -> torch.Tensor:
    robot = env.scene[robot_cfg.name]
    tips = robot.data.body_pos_w.torch[:, robot_cfg.body_ids]
    return torch.linalg.vector_norm(tips - env.scene["object"].data.root_pos_w.torch[:, None, :], dim=-1)


def finger_reaching(env: ManagerBasedRLEnv, robot_cfg: SceneEntityCfg, std: float) -> torch.Tensor:
    """Shape exploration by the mean distance of the four fingertip link origins to the cube."""
    return 1.0 - torch.tanh(_tip_distances(env, robot_cfg).mean(dim=-1) / std)


def opposing_finger_proximity(env: ManagerBasedRLEnv, robot_cfg: SceneEntityCfg, std: float) -> torch.Tensor:
    """Reward proximity of both the thumb and at least one long finger; this is not a contact sensor."""
    distances = _tip_distances(env, robot_cfg)
    opposing_distance = torch.maximum(distances[:, 3], distances[:, :3].min(dim=-1).values)
    return 1.0 - torch.tanh(opposing_distance / std)


def _lift_state(env: ManagerBasedRLEnv, robot_cfg: SceneEntityCfg) -> tuple[torch.Tensor, torch.Tensor]:
    distances = _tip_distances(env, robot_cfg)
    near_hand = (distances[:, 3] < 0.10) & (distances[:, :3].min(dim=-1).values < 0.10)
    # Subtract environment origins so cloning does not change the height convention.
    height = env.scene["object"].data.root_pos_w.torch[:, 2] - env.scene.env_origins[:, 2] - CUBE_REST_HEIGHT
    return height, near_hand


def lift_progress(env: ManagerBasedRLEnv, robot_cfg: SceneEntityCfg) -> torch.Tensor:
    """Reward height gained above the resting cube center, gated by opposing finger proximity."""
    height, near_hand = _lift_state(env, robot_cfg)
    return (height / LIFT_HEIGHT).clamp(0.0, 1.0) * near_hand.float()


def success_bonus(env: ManagerBasedRLEnv) -> torch.Tensor:
    """One terminal bonus; cancel RewardManager's step-duration scaling."""
    return env.termination_manager.get_term("success").float() / env.step_dt


class HeldLiftSuccess(ManagerTermBase):
    """End an episode after a near-hand cube stays lifted and slow for a continuous interval.

    Proximity is only a geometric gate. Sustained height and low cube speed reject a brief
    airborne pass; this baseline does not independently certify opposing finger contacts.
    """

    def __init__(self, cfg: TerminationTermCfg, env: ManagerBasedRLEnv):
        super().__init__(cfg, env)
        self._held_time = torch.zeros(env.num_envs, device=env.device)

    def reset(self, env_ids: Sequence[int] | torch.Tensor | slice | None = None) -> None:
        if env_ids is None:
            self._held_time.zero_()
        else:
            self._held_time[env_ids] = 0.0

    def __call__(
        self,
        env: ManagerBasedRLEnv,
        robot_cfg: SceneEntityCfg,
        hold_time: float,
        max_speed: float,
    ) -> torch.Tensor:
        height, near_hand = _lift_state(env, robot_cfg)
        speed = torch.linalg.vector_norm(env.scene["object"].data.root_lin_vel_w.torch, dim=-1)
        holding = (height >= LIFT_HEIGHT) & near_hand & (speed <= max_speed)
        self._held_time = torch.where(holding, self._held_time + env.step_dt, 0.0)
        return self._held_time >= hold_time
