"""LEAP Hand v1 Right open-close test.

Confirmed mapping from physical observation:

Index finger:
    tn__0_  -> tensor index 4
    tn__1_  -> tensor index 0
    tn__2_  -> tensor index 8
    tn__3_  -> tensor index 12

Middle finger:
    tn__4_  -> tensor index 5
    tn__5_  -> tensor index 1
    tn__6_  -> tensor index 9
    tn__7_  -> tensor index 13

Ring finger:
    tn__8_  -> tensor index 6
    tn__9_  -> tensor index 2
    tn__10_ -> tensor index 10
    tn__11_ -> tensor index 14

Thumb:
    tn__12_ -> tensor index 3
    tn__13_ -> tensor index 7
    tn__14_ -> tensor index 11
    tn__15_ -> tensor index 15

Motion:
    OPEN -> CLOSE -> OPEN -> repeat
"""

import argparse
import fcntl
import math
import signal
from pathlib import Path

from isaaclab.app import AppLauncher


# =============================================================================
# Prevent duplicate processes
# =============================================================================

LOCK_PATH = "/tmp/xgw_test_leap_open_close.lock"
_lock_file = open(LOCK_PATH, "w")

try:
    fcntl.flock(
        _lock_file,
        fcntl.LOCK_EX | fcntl.LOCK_NB,
    )
except BlockingIOError:
    raise RuntimeError(
        "test_leap_open_close.py is already running."
    )


# =============================================================================
# Isaac Lab launcher
# =============================================================================

parser = argparse.ArgumentParser(
    description="LEAP Hand v1 Right open-close test."
)

AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app


# Import after SimulationApp starts
import torch

import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import Articulation, ArticulationCfg


# =============================================================================
# Asset path
# =============================================================================

ISAACLAB_ROOT = Path(__file__).resolve().parents[3]

LEAP_USD_PATH = (
    ISAACLAB_ROOT
    / "source"
    / "ur5_leap"
    / "assets"
    / "official"
    / "leap_hand_v1_right"
    / "generated"
    / "usd"
    / "leap_hand_right.usd"
    / "leap_hand_right"
    / "leap_hand_right.usda"
)


# =============================================================================
# LEAP configuration
# =============================================================================

LEAP_CFG = ArticulationCfg(
    prim_path="/World/LEAP",

    spawn=sim_utils.UsdFileCfg(
        usd_path=str(LEAP_USD_PATH),
    ),

    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0.0, 0.0, 0.35),
    ),

    actuators={
        "fingers": ImplicitActuatorCfg(
            joint_names_expr=[".*"],
            joint_effort_limit=0.95,
            joint_velocity_limit=8.0,
            stiffness=3.0,
            damping=0.1,
        ),
    },
)


# =============================================================================
# Clean shutdown
# =============================================================================

stop_requested = False


def request_stop(signum, frame):
    global stop_requested

    if not stop_requested:
        print("\n[INFO] Stop requested.")

    stop_requested = True


signal.signal(signal.SIGINT, request_stop)
signal.signal(signal.SIGTERM, request_stop)


# =============================================================================
# Main
# =============================================================================

def main():

    if not LEAP_USD_PATH.exists():
        raise FileNotFoundError(
            f"LEAP USD not found:\n{LEAP_USD_PATH}"
        )

    # -------------------------------------------------------------------------
    # Simulation
    # -------------------------------------------------------------------------

    sim_cfg = sim_utils.SimulationCfg(
        dt=0.01,
        device=args_cli.device,
    )

    sim = sim_utils.SimulationContext(sim_cfg)

    # Ground
    ground_cfg = sim_utils.GroundPlaneCfg()
    ground_cfg.func(
        "/World/GroundPlane",
        ground_cfg,
    )

    # Light
    light_cfg = sim_utils.DomeLightCfg(
        intensity=3000.0,
        color=(0.75, 0.75, 0.75),
    )

    light_cfg.func(
        "/World/Light",
        light_cfg,
    )

    # LEAP Hand
    hand = Articulation(
        cfg=LEAP_CFG,
    )

    # Camera
    sim.set_camera_view(
        eye=(0.55, 0.55, 0.55),
        target=(0.0, 0.0, 0.35),
    )

    sim.reset()
    hand.reset()

    sim_dt = sim.get_physics_dt()

    # -------------------------------------------------------------------------
    # Check articulation
    # -------------------------------------------------------------------------

    if hand.num_joints != 16:
        raise RuntimeError(
            f"Expected 16 joints, got {hand.num_joints}."
        )

    print("\n" + "=" * 76)
    print("[INFO] LEAP Hand v1 Right open-close test")
    print("=" * 76)

    print("\n[INFO] Isaac Lab actual joint order:")

    for index, name in enumerate(hand.joint_names):
        print(
            f"    tensor index {index:2d} -> {name}"
        )

    # -------------------------------------------------------------------------
    # Confirm expected name -> index mapping
    # -------------------------------------------------------------------------

    expected_mapping = {
        "tn__0_": 4,
        "tn__1_": 0,
        "tn__2_": 8,
        "tn__3_": 12,

        "tn__4_": 5,
        "tn__5_": 1,
        "tn__6_": 9,
        "tn__7_": 13,

        "tn__8_": 6,
        "tn__9_": 2,
        "tn__10_": 10,
        "tn__11_": 14,

        "tn__12_": 3,
        "tn__13_": 7,
        "tn__14_": 11,
        "tn__15_": 15,
    }

    print("\n[INFO] Checking confirmed mapping:")

    for joint_name, expected_index in expected_mapping.items():

        if joint_name not in hand.joint_names:
            raise RuntimeError(
                f"Joint {joint_name} not found."
            )

        actual_index = hand.joint_names.index(
            joint_name
        )

        status = (
            "OK"
            if actual_index == expected_index
            else "CHANGED"
        )

        print(
            f"    {joint_name:8s}"
            f" -> actual index {actual_index:2d}"
            f" | expected {expected_index:2d}"
            f" | {status}"
        )

    # -------------------------------------------------------------------------
    # Joint limits
    # -------------------------------------------------------------------------

    limits = (
        hand.data
        .soft_joint_pos_limits
        .torch[0]
    )

    lower = limits[:, 0]
    upper = limits[:, 1]

    # -------------------------------------------------------------------------
    # OPEN pose
    # -------------------------------------------------------------------------

    # Zero is used as open/reference pose.
    open_pose = torch.zeros(
        (1, hand.num_joints),
        device=hand.device,
        dtype=torch.float32,
    )

    # Clamp zero pose in case any joint excludes zero.
    open_pose = torch.maximum(
        open_pose,
        lower.unsqueeze(0),
    )

    open_pose = torch.minimum(
        open_pose,
        upper.unsqueeze(0),
    )

    # -------------------------------------------------------------------------
    # CLOSE pose
    # -------------------------------------------------------------------------

    close_pose = open_pose.clone()

    #
    # IMPORTANT:
    #
    # We control by JOINT NAME.
    #
    # Do not use tensor index directly.
    #

    close_targets_by_name = {

        # =============================================================
        # INDEX FINGER / 食指
        #
        # tn__0_ : root side motion
        # tn__1_ : root flexion
        # tn__2_ : middle flexion
        # tn__3_ : distal flexion
        # =============================================================

        "tn__0_": 0.00,
        "tn__1_": 1.20,
        "tn__2_": 1.10,
        "tn__3_": 1.10,

        # =============================================================
        # MIDDLE FINGER / 中指
        # =============================================================

        "tn__4_": 0.00,
        "tn__5_": 1.20,
        "tn__6_": 1.10,
        "tn__7_": 1.10,

        # =============================================================
        # RING FINGER / 无名指
        # =============================================================

        "tn__8_": 0.00,
        "tn__9_": 1.20,
        "tn__10_": 1.10,
        "tn__11_": 1.10,

        # =============================================================
        # THUMB / 拇指
        # =============================================================

        "tn__12_": 0.80,
        "tn__13_": 0.90,
        "tn__14_": 0.90,
        "tn__15_": 0.70,
    }

    # -------------------------------------------------------------------------
    # Write name-based commands into tensor
    # -------------------------------------------------------------------------

    for joint_name, target_value in close_targets_by_name.items():

        tensor_index = hand.joint_names.index(
            joint_name
        )

        close_pose[
            0,
            tensor_index
        ] = target_value

    # -------------------------------------------------------------------------
    # Clamp CLOSE pose
    # -------------------------------------------------------------------------

    close_pose = torch.maximum(
        close_pose,
        lower.unsqueeze(0),
    )

    close_pose = torch.minimum(
        close_pose,
        upper.unsqueeze(0),
    )

    # -------------------------------------------------------------------------
    # Print final physical mapping
    # -------------------------------------------------------------------------

    print("\n" + "=" * 76)
    print("[INFO] Physical finger mapping")
    print("=" * 76)

    finger_groups = {
        "Index finger": [
            "tn__0_",
            "tn__1_",
            "tn__2_",
            "tn__3_",
        ],

        "Middle finger": [
            "tn__4_",
            "tn__5_",
            "tn__6_",
            "tn__7_",
        ],

        "Ring finger": [
            "tn__8_",
            "tn__9_",
            "tn__10_",
            "tn__11_",
        ],

        "Thumb": [
            "tn__12_",
            "tn__13_",
            "tn__14_",
            "tn__15_",
        ],
    }

    for finger_name, joint_names in finger_groups.items():

        print(f"\n{finger_name}:")

        for joint_name in joint_names:

            tensor_index = hand.joint_names.index(
                joint_name
            )

            target = close_pose[
                0,
                tensor_index
            ].item()

            print(
                f"    {joint_name:8s}"
                f" -> index {tensor_index:2d}"
                f" -> CLOSE {target: .3f} rad"
            )

    # -------------------------------------------------------------------------
    # Timing
    # -------------------------------------------------------------------------

    #
    # OPEN -> CLOSE = 2 seconds
    # CLOSE -> OPEN = 2 seconds
    #

    half_cycle = 2.0
    full_cycle = 4.0

    print("\n" + "=" * 76)
    print("[INFO] OPEN -> CLOSE : 2 s")
    print("[INFO] CLOSE -> OPEN : 2 s")
    print("[INFO] Full cycle    : 4 s")
    print("[INFO] Ctrl+C to stop.")
    print("=" * 76 + "\n")

    # -------------------------------------------------------------------------
    # Simulation loop
    # -------------------------------------------------------------------------

    elapsed_time = 0.0
    last_phase = None

    while (
        simulation_app.is_running()
        and not stop_requested
    ):

        cycle_time = (
            elapsed_time
            % full_cycle
        )

        # -------------------------------------------------------------
        # Closing
        # -------------------------------------------------------------

        if cycle_time < half_cycle:

            phase = "CLOSING"

            alpha = (
                cycle_time
                / half_cycle
            )

            start_pose = open_pose
            end_pose = close_pose

        # -------------------------------------------------------------
        # Opening
        # -------------------------------------------------------------

        else:

            phase = "OPENING"

            alpha = (
                cycle_time
                - half_cycle
            ) / half_cycle

            start_pose = close_pose
            end_pose = open_pose

        if phase != last_phase:

            print(
                f"[INFO] {phase}"
            )

            last_phase = phase

        # -------------------------------------------------------------
        # Smooth interpolation
        # -------------------------------------------------------------

        smooth_alpha = (
            0.5
            - 0.5
            * math.cos(
                math.pi * alpha
            )
        )

        targets = (
            (1.0 - smooth_alpha)
            * start_pose
            +
            smooth_alpha
            * end_pose
        )

        # -------------------------------------------------------------
        # Safety clamp
        # -------------------------------------------------------------

        targets = torch.maximum(
            targets,
            lower.unsqueeze(0),
        )

        targets = torch.minimum(
            targets,
            upper.unsqueeze(0),
        )

        # -------------------------------------------------------------
        # Send commands
        # -------------------------------------------------------------

        hand.set_joint_position_target(
            targets
        )

        hand.write_data_to_sim()

        # Physics
        sim.step()

        hand.update(
            sim_dt
        )

        elapsed_time += sim_dt


# =============================================================================
# Entry point
# =============================================================================

if __name__ == "__main__":

    try:
        main()

    finally:

        print(
            "\n[INFO] Closing Isaac Sim..."
        )

        simulation_app.close()

        print(
            "[INFO] Isaac Sim closed."
        )
