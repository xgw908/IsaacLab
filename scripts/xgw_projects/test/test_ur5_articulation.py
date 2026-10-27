"""UR5 CB3 articulation test.

The robot starts from an upright working posture and all six joints
perform slow sinusoidal motion around that posture.
"""

import argparse
import fcntl
import math
import signal
from pathlib import Path

from isaaclab.app import AppLauncher


# -----------------------------------------------------------------------------
# Prevent multiple copies of this test from running at the same time
# -----------------------------------------------------------------------------

LOCK_PATH = "/tmp/xgw_test_ur5_articulation.lock"
_lock_file = open(LOCK_PATH, "w")

try:
    fcntl.flock(_lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    raise RuntimeError(
        "test_ur5_articulation.py is already running.\n"
        "Stop the previous process before starting another one."
    )


# -----------------------------------------------------------------------------
# CLI / Isaac Sim
# -----------------------------------------------------------------------------

parser = argparse.ArgumentParser(
    description="UR5 CB3 six-joint articulation test."
)
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app


# Isaac Lab / torch imports after SimulationApp starts
import torch

import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import Articulation, ArticulationCfg


# -----------------------------------------------------------------------------
# Asset
# -----------------------------------------------------------------------------

ISAACLAB_ROOT = Path(__file__).resolve().parents[3]

UR5_USD_PATH = (
    ISAACLAB_ROOT
    / "source"
    / "ur5_leap"
    / "assets"
    / "official"
    / "ur5"
    / "generated"
    / "usd"
    / "ur5_cb3.usd"
    / "ur5_cb3"
    / "ur5_cb3.usda"
)


# -----------------------------------------------------------------------------
# UR5
# -----------------------------------------------------------------------------

UR5_CFG = ArticulationCfg(
    prim_path="/World/UR5",

    spawn=sim_utils.UsdFileCfg(
        usd_path=str(UR5_USD_PATH),
    ),

    # Upright / folded working posture instead of the flat zero pose.
    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0.0, 0.0, 0.0),
        joint_pos={
            "shoulder_pan_joint": 0.0,
            "shoulder_lift_joint": -math.pi / 2,  # -90 deg
            "elbow_joint": 0.0,           # +90 deg
            "wrist_1_joint": -math.pi / 2,        # -90 deg
            "wrist_2_joint": 0.0,
            "wrist_3_joint": 0.0,
        },
    ),

    actuators={
        # The three large arm joints need substantially more torque
        # than the wrist joints to hold the robot against gravity.
        "arm": ImplicitActuatorCfg(
            joint_names_expr=[
                "shoulder_pan_joint",
                "shoulder_lift_joint",
                "elbow_joint",
            ],
            joint_effort_limit=150.0,
            joint_velocity_limit=1.0,
            stiffness=100.0,
            damping=10.0,
        ),

        "wrist": ImplicitActuatorCfg(
            joint_names_expr=[
                "wrist_1_joint",
                "wrist_2_joint",
                "wrist_3_joint",
            ],
            joint_effort_limit=28.0,
            joint_velocity_limit=1.0,
            stiffness=80.0,
            damping=8.0,
        ),
    },
)


# -----------------------------------------------------------------------------
# Clean Ctrl+C / SIGTERM handling
# -----------------------------------------------------------------------------

stop_requested = False


def request_stop(signum, frame):
    global stop_requested

    if not stop_requested:
        print("\n[INFO] Stop requested. Closing simulation cleanly...")

    stop_requested = True


signal.signal(signal.SIGINT, request_stop)
signal.signal(signal.SIGTERM, request_stop)


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    if not UR5_USD_PATH.exists():
        raise FileNotFoundError(
            f"UR5 USD not found:\n{UR5_USD_PATH}"
        )

    # Simulation
    sim_cfg = sim_utils.SimulationCfg(
        dt=0.01,
        device=args_cli.device,
    )
    sim = sim_utils.SimulationContext(sim_cfg)

    # Ground
    ground_cfg = sim_utils.GroundPlaneCfg()
    ground_cfg.func("/World/GroundPlane", ground_cfg)

    # Light
    light_cfg = sim_utils.DomeLightCfg(
        intensity=3000.0,
        color=(0.75, 0.75, 0.75),
    )
    light_cfg.func("/World/Light", light_cfg)

    # Robot
    robot = Articulation(cfg=UR5_CFG)

    # Camera
    sim.set_camera_view(
        eye=(1.8, 1.8, 1.5),
        target=(0.0, 0.0, 0.55),
    )

    # Initialize physics and articulation
    sim.reset()
    robot.reset()

    sim_dt = sim.get_physics_dt()

    print("\n" + "=" * 70)
    print("[INFO] UR5 CB3 articulation initialized")
    print(f"[INFO] USD: {UR5_USD_PATH}")
    print(f"[INFO] Number of joints: {robot.num_joints}")
    print("[INFO] Joint names:")

    for i, name in enumerate(robot.joint_names):
        print(f"    [{i}] {name}")

    print("=" * 70)

    if robot.num_joints != 6:
        raise RuntimeError(
            f"Expected 6 movable joints, got {robot.num_joints}."
        )

    # -------------------------------------------------------------------------
    # Motion
    # -------------------------------------------------------------------------

    # Center = upright initial working posture.
    center_pos = robot.data.default_joint_pos.torch.clone()

    # Different amplitudes for each joint.
    #
    # shoulder_pan  : +/- 45 deg
    # shoulder_lift : +/- 30 deg
    # elbow         : +/- 45 deg
    # wrist_1       : +/- 45 deg
    # wrist_2       : +/- 60 deg
    # wrist_3       : +/- 90 deg
    amplitudes = torch.tensor(
        [
            math.pi / 4,
            math.pi / 6,
            math.pi / 4,
            math.pi / 4,
            math.pi / 3,
            math.pi / 2,
        ],
        device=robot.device,
    ).unsqueeze(0)

    # One full cycle every 10 seconds.
    frequency = 0.10
    omega = 2.0 * math.pi * frequency

    # Give each joint a slightly different phase.
    phases = torch.tensor(
        [
            0.0,
            math.pi / 6,
            math.pi / 3,
            math.pi / 2,
            2.0 * math.pi / 3,
            5.0 * math.pi / 6,
        ],
        device=robot.device,
    ).unsqueeze(0)

    print("[INFO] Upright working posture enabled.")
    print("[INFO] Motion period: 10 seconds")
    print("[INFO] shoulder_lift center: -90 deg, amplitude: +/-30 deg")
    print("[INFO] Press Ctrl+C once to stop cleanly.\n")

    elapsed_time = 0.0

    while simulation_app.is_running() and not stop_requested:
        joint_targets = (
            center_pos
            + amplitudes
            * torch.sin(omega * elapsed_time + phases)
        )

        # This API currently works in our environment.
        # It is deprecated in Isaac Lab 3.x and can be migrated later.
        robot.set_joint_position_target(joint_targets)

        robot.write_data_to_sim()
        sim.step()
        robot.update(sim_dt)

        elapsed_time += sim_dt


if __name__ == "__main__":
    try:
        main()
    finally:
        print("[INFO] Closing Isaac Sim...")
        simulation_app.close()
        print("[INFO] Isaac Sim closed.")
