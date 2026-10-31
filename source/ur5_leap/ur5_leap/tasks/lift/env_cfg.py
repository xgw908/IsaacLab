# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Manager-based joint-position cube lifting with the simplified UR5 + LEAP model."""

import math

from isaaclab_physx.physics import PhysxCfg
from isaaclab_physx.sim.schemas import PhysxRigidBodyCfg

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg, RigidObjectCfg
from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab.envs import mdp as base_mdp
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import RewardTermCfg as RewTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.managers import TerminationTermCfg as DoneTerm
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass
from isaaclab.utils.modifiers import ModifierCfg

from ur5_leap import LEAP_JOINT_NAMES, UR5_JOINT_NAMES, UR5_SIMPLE_LEAP_CFG

from . import mdp

_JOINTS = SceneEntityCfg("robot", joint_names=UR5_JOINT_NAMES + LEAP_JOINT_NAMES, preserve_order=True)
_TIPS = SceneEntityCfg("robot", body_names=mdp.FINGERTIP_NAMES, preserve_order=True)


@configclass
class LiftSceneCfg(InteractiveSceneCfg):
    """An offline cube/table scene; only the robot itself is loaded from the local USD."""

    robot: ArticulationCfg = UR5_SIMPLE_LEAP_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")
    object: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/Object",
        init_state=RigidObjectCfg.InitialStateCfg(pos=(0.67, 0.14, mdp.CUBE_REST_HEIGHT + 0.001)),
        spawn=sim_utils.CuboidCfg(
            size=(mdp.CUBE_SIZE,) * 3,
            rigid_props=[
                sim_utils.UsdPhysicsRigidBodyCfg(rigid_body_enabled=True, kinematic_enabled=False),
                PhysxRigidBodyCfg(disable_gravity=False, max_depenetration_velocity=1.0),
            ],
            collision_props=sim_utils.UsdPhysicsCollisionCfg(collision_enabled=True),
            mass_props=sim_utils.MassCfg(mass=0.05),
            physics_material=sim_utils.RigidBodyMaterialBaseCfg(static_friction=1.0, dynamic_friction=1.0),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.1, 0.4, 0.8)),
        ),
    )
    table = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Table",
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.65, 0.14, mdp.TABLE_HEIGHT - 0.025)),
        spawn=sim_utils.CuboidCfg(
            size=(0.6, 0.6, 0.05),
            rigid_props=sim_utils.UsdPhysicsRigidBodyCfg(rigid_body_enabled=True, kinematic_enabled=True),
            collision_props=sim_utils.UsdPhysicsCollisionCfg(collision_enabled=True),
            physics_material=sim_utils.RigidBodyMaterialBaseCfg(static_friction=1.0, dynamic_friction=1.0),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(0.35, 0.35, 0.35)),
        ),
    )
    ground = AssetBaseCfg(prim_path="/World/GroundPlane", spawn=sim_utils.GroundPlaneCfg())
    light = AssetBaseCfg(
        prim_path="/World/Light", spawn=sim_utils.DomeLightCfg(intensity=3000.0, color=(0.75, 0.75, 0.75))
    )


@configclass
class ActionsCfg:
    """Six arm targets around the task pose, then sixteen hand targets spanning joint limits."""

    arm = base_mdp.JointPositionActionCfg(
        asset_name="robot", joint_names=UR5_JOINT_NAMES, preserve_order=True, scale=0.5, use_default_offset=True
    )
    hand = base_mdp.JointPositionToLimitsActionCfg(
        asset_name="robot", joint_names=LEAP_JOINT_NAMES, preserve_order=True, rescale_to_limits=True
    )


@configclass
class ObservationsCfg:
    @configclass
    class PolicyCfg(ObsGroup):
        """91 values: 22 joint positions, 22 velocities, 13 cube state, 12 fingertip positions, 22 actions."""

        joint_pos = ObsTerm(func=base_mdp.joint_pos_rel, params={"asset_cfg": _JOINTS})
        joint_vel = ObsTerm(func=base_mdp.joint_vel_rel, params={"asset_cfg": _JOINTS}, scale=0.1)
        object_state = ObsTerm(func=mdp.object_state_b)
        # Revolute fingertip bodies survive fixed-joint merging; the fixed palm may not.
        hand_positions = ObsTerm(func=mdp.hand_positions_b, params={"robot_cfg": _TIPS})
        last_action = ObsTerm(func=base_mdp.last_action)

        def __post_init__(self):
            self.concatenate_terms = True
            self.enable_corruption = False
            # Opt-in checks synchronize with the GPU; keep them out of normal training.
            if mdp.CHECK_FINITE_OBSERVATIONS:
                self.joint_pos.func = mdp.checked_joint_positions
                for name in ("joint_vel", "object_state", "hand_positions", "last_action"):
                    getattr(self, name).modifiers = [
                        ModifierCfg(func=mdp.require_finite_observation, params={"term_name": name})
                    ]

    policy: PolicyCfg = PolicyCfg()


@configclass
class EventsCfg:
    validate_hand_limits = EventTerm(
        func=mdp.validate_hand_action_limits,
        mode="startup",
        params={"asset_cfg": SceneEntityCfg("robot", joint_names=LEAP_JOINT_NAMES, preserve_order=True)},
    )
    reset_scene = EventTerm(func=base_mdp.reset_scene_to_default, mode="reset", params={"reset_joint_targets": True})
    reset_cube = EventTerm(
        func=base_mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "asset_cfg": SceneEntityCfg("object"),
            "pose_range": {"x": (-0.025, 0.025), "y": (-0.025, 0.025), "yaw": (-0.3, 0.3)},
            "velocity_range": {},
        },
    )


@configclass
class RewardsCfg:
    reaching = RewTerm(func=mdp.finger_reaching, weight=2.0, params={"robot_cfg": _TIPS, "std": 0.10})
    opposing_proximity = RewTerm(
        func=mdp.opposing_finger_proximity, weight=2.0, params={"robot_cfg": _TIPS, "std": 0.08}
    )
    lifting = RewTerm(func=mdp.lift_progress, weight=12.0, params={"robot_cfg": _TIPS})
    success = RewTerm(func=mdp.success_bonus, weight=10.0)
    action_rate = RewTerm(func=base_mdp.action_rate_l2, weight=-1e-3)
    joint_velocity = RewTerm(func=base_mdp.joint_vel_l2, weight=-1e-4, params={"asset_cfg": _JOINTS})


@configclass
class TerminationsCfg:
    time_out = DoneTerm(func=base_mdp.time_out, time_out=True)
    object_dropped = DoneTerm(
        func=base_mdp.root_height_below_minimum, params={"asset_cfg": SceneEntityCfg("object"), "minimum_height": 0.03}
    )
    success = DoneTerm(func=mdp.HeldLiftSuccess, params={"robot_cfg": _TIPS, "hold_time": 0.5, "max_speed": 0.2})


@configclass
class UR5SimpleLeapLiftEnvCfg(ManagerBasedRLEnvCfg):
    """A first state-based lift task, to qualify and tune on the server before long training."""

    # Qualify the custom converted articulation without native physics replication first.
    scene: LiftSceneCfg = LiftSceneCfg(num_envs=128, env_spacing=2.5, replicate_physics=False)
    actions: ActionsCfg = ActionsCfg()
    observations: ObservationsCfg = ObservationsCfg()
    events: EventsCfg = EventsCfg()
    rewards: RewardsCfg = RewardsCfg()
    terminations: TerminationsCfg = TerminationsCfg()

    def __post_init__(self):
        self.decimation = 4
        self.episode_length_s = 8.0
        self.sim.dt = 1.0 / 120.0
        self.sim.render_interval = self.decimation
        self.sim.physics = PhysxCfg()
        self.viewer.eye = (1.6, 1.4, 1.2)
        self.viewer.lookat = (0.6, 0.14, 0.2)
        self.scene.robot.spawn.variants = {"Physics": "physx"}
        # Only this environment changes the working pose; asset defaults and actuators stay intact.
        self.scene.robot.init_state.joint_pos.update(
            {
                "shoulder_pan_joint": 0.0,
                "shoulder_lift_joint": -1.2,
                "elbow_joint": 1.6,
                "wrist_1_joint": -2.0,
                "wrist_2_joint": -math.pi / 2.0,
                "wrist_3_joint": 0.0,
            }
        )
