"""UR5 CB3 + LEAP Hand Right combined articulation validation.

Goals:
1. Load the combined USD.
2. Verify that it is one Articulation.
3. Verify that it contains 22 movable joints:
      UR5  = 6 DoF
      LEAP = 16 DoF
4. Print the REAL Isaac Lab joint order and limits.
5. Keep the model still for visual inspection through WebRTC.

No joint-name assumption is made for the LEAP Hand.
"""

import argparse
import fcntl
import signal
from pathlib import Path

from isaaclab.app import AppLauncher


# =============================================================================
# Prevent duplicate processes
# =============================================================================

LOCK_PATH = "/tmp/xgw_test_ur5_leap_articulation.lock"
_lock_file = open(LOCK_PATH, "w")

try:
    fcntl.flock(
        _lock_file,
        fcntl.LOCK_EX | fcntl.LOCK_NB,
    )
except BlockingIOError:
    raise RuntimeError(
        "test_ur5_leap_articulation.py is already running."
    )


# =============================================================================
# Launcher
# =============================================================================

parser = argparse.ArgumentParser(
    description="UR5 + LEAP Hand combined articulation validation."
)

AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app


# Isaac Lab imports after SimulationApp starts
import torch

import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import Articulation, ArticulationCfg


# =============================================================================
# Asset path
# =============================================================================

ISAACLAB_ROOT = Path(__file__).resolve().parents[3]

ROBOT_USD_PATH = (
    ISAACLAB_ROOT
    / "source"
    / "ur5_leap"
    / "assets"
    / "combined"
    / "ur5_leap_right"
    / "generated"
    / "usd"
    / "ur5_leap_right.usd"
    / "ur5_leap_right"
    / "ur5_leap_right.usda"
)


# =============================================================================
# Combined robot configuration
# =============================================================================

ROBOT_CFG = ArticulationCfg(
    prim_path="/World/Robot",

    spawn=sim_utils.UsdFileCfg(
        usd_path=str(ROBOT_USD_PATH),
    ),

    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0.0, 0.0, 0.0),
    ),

    # This first test does NOT actively move the robot.
    # A generic actuator is enough for loading/validation.
    actuators={
        "all_joints": ImplicitActuatorCfg(
            joint_names_expr=[".*"],
            joint_effort_limit=150.0,
            joint_velocity_limit=3.0,
            stiffness=40.0,
            damping=5.0,
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

    if not ROBOT_USD_PATH.exists():
        raise FileNotFoundError(
            f"Combined USD not found:\n{ROBOT_USD_PATH}"
        )

    print("\n[INFO] Loading combined USD:")
    print(ROBOT_USD_PATH)

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

    # Combined articulation
    robot = Articulation(
        cfg=ROBOT_CFG,
    )

    # Camera
    sim.set_camera_view(
        eye=(1.4, 1.4, 1.1),
        target=(0.0, 0.0, 0.45),
    )

    sim.reset()
    robot.reset()

    sim_dt = sim.get_physics_dt()

    # -------------------------------------------------------------------------
    # Joint information
    # -------------------------------------------------------------------------

    print("\n" + "=" * 88)
    print("[INFO] UR5 + LEAP COMBINED ARTICULATION")
    print("=" * 88)

    print(
        f"[INFO] Total movable joints detected: "
        f"{robot.num_joints}"
    )

    limits = robot.data.soft_joint_pos_limits.torch[0]

    lower = limits[:, 0]
    upper = limits[:, 1]

    print("\n[INFO] Isaac Lab actual joint order:\n")

    for index, name in enumerate(robot.joint_names):

        print(
            f"    index {index:2d}"
            f" -> {name:25s}"
            f" limits "
            f"[{lower[index].item(): .3f}, "
            f"{upper[index].item(): .3f}]"
        )

    # -------------------------------------------------------------------------
    # UR5 joint verification
    # -------------------------------------------------------------------------

    ur5_joint_names = [
        "shoulder_pan_joint",
        "shoulder_lift_joint",
        "elbow_joint",
        "wrist_1_joint",
        "wrist_2_joint",
        "wrist_3_joint",
    ]

    print("\n" + "-" * 88)
    print("[INFO] UR5 joints")
    print("-" * 88)

    ur5_indices = []

    for joint_name in ur5_joint_names:

        if joint_name in robot.joint_names:

            index = robot.joint_names.index(
                joint_name
            )

            ur5_indices.append(index)

            print(
                f"    [OK] {joint_name:25s}"
                f" -> index {index}"
            )

        else:

            print(
                f"    [MISSING] {joint_name}"
            )

    # -------------------------------------------------------------------------
    # Detect remaining LEAP joints automatically
    # -------------------------------------------------------------------------

    leap_joint_names = [
        name
        for name in robot.joint_names
        if name not in ur5_joint_names
    ]

    print("\n" + "-" * 88)
    print("[INFO] Remaining joints (expected LEAP Hand)")
    print("-" * 88)

    for name in leap_joint_names:

        index = robot.joint_names.index(name)

        print(
            f"    {name:25s}"
            f" -> index {index}"
        )

    # -------------------------------------------------------------------------
    # Final validation
    # -------------------------------------------------------------------------

    print("\n" + "=" * 88)
    print("[INFO] VALIDATION RESULT")
    print("=" * 88)

    print(
        f"UR5 joints detected : "
        f"{len(ur5_indices)} / 6"
    )

    print(
        f"LEAP joints detected: "
        f"{len(leap_joint_names)} / 16"
    )

    print(
        f"Total joints        : "
        f"{robot.num_joints} / 22"
    )

    if (
        robot.num_joints == 22
        and len(ur5_indices) == 6
        and len(leap_joint_names) == 16
    ):

        print("\n[PASS] Combined robot is a valid 22-DoF Articulation.")

    else:

        print("\n[FAIL] Combined articulation structure is not as expected.")

        raise RuntimeError(
            "Expected UR5 6 DoF + LEAP 16 DoF = 22 DoF."
        )

    print("\n[INFO] Keep WebRTC open and inspect:")
    print("       1. Is LEAP attached to the UR5 wrist?")
    print("       2. Is the hand orientation correct?")
    print("       3. Is there obvious overlap/separation?")
    print("       4. Is the right hand model used?")
    print("\n[INFO] Ctrl+C to stop.\n")

    # -------------------------------------------------------------------------
    # Hold default pose
    # -------------------------------------------------------------------------

    target = (
        robot.data.default_joint_pos
        .torch
        .clone()
    )

    while (
        simulation_app.is_running()
        and not stop_requested
    ):

        robot.set_joint_position_target(
            target
        )

        robot.write_data_to_sim()

        sim.step()

        robot.update(sim_dt)


# =============================================================================
# Entry
# =============================================================================

if __name__ == "__main__":

    try:
        main()

    finally:

        print("\n[INFO] Closing Isaac Sim...")

        simulation_app.close()

        print("[INFO] Isaac Sim closed.")
