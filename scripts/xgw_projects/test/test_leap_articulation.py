"""LEAP Hand v1 Right joint-by-joint articulation test.

The 16 joints are tested sequentially.
Only one joint moves at a time while the other 15 joints stay at
the center of their valid ranges.

Purpose:
- verify all 16 joints
- determine which joint number corresponds to which finger joint
- observe positive/negative rotation direction
"""

import argparse
import fcntl
import math
import signal
from pathlib import Path

from isaaclab.app import AppLauncher


# -----------------------------------------------------------------------------
# Prevent multiple copies
# -----------------------------------------------------------------------------

LOCK_PATH = "/tmp/xgw_test_leap_articulation.lock"
_lock_file = open(LOCK_PATH, "w")

try:
    fcntl.flock(_lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    raise RuntimeError(
        "test_leap_articulation.py is already running.\n"
        "Stop the old process before starting another one."
    )


# -----------------------------------------------------------------------------
# Command line / Isaac Sim
# -----------------------------------------------------------------------------

parser = argparse.ArgumentParser(
    description="LEAP Hand v1 Right sequential 16-joint test."
)

AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app


# Import after SimulationApp starts.
import torch

import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import Articulation, ArticulationCfg


# -----------------------------------------------------------------------------
# LEAP USD path
# -----------------------------------------------------------------------------

# Current file:
# scripts/xgw_projects/test/test_leap_articulation.py
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


# -----------------------------------------------------------------------------
# LEAP Hand configuration
# -----------------------------------------------------------------------------

LEAP_CFG = ArticulationCfg(
    prim_path="/World/LEAP",

    spawn=sim_utils.UsdFileCfg(
        usd_path=str(LEAP_USD_PATH),
    ),

    init_state=ArticulationCfg.InitialStateCfg(
        # Raise the hand so it is easy to observe.
        pos=(0.0, 0.0, 0.35),
    ),

    actuators={
        "fingers": ImplicitActuatorCfg(
            joint_names_expr=[".*"],

            # Temporary parameters for functional testing.
            # These are not final real-hardware motor parameters.
            joint_effort_limit=0.95,
            joint_velocity_limit=8.0,

            stiffness=3.0,
            damping=0.1,
        ),
    },
)


# -----------------------------------------------------------------------------
# Clean shutdown
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

    if not LEAP_USD_PATH.exists():
        raise FileNotFoundError(
            f"LEAP Hand USD not found:\n{LEAP_USD_PATH}"
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

    # Close camera view
    sim.set_camera_view(
        eye=(0.55, 0.55, 0.55),
        target=(0.0, 0.0, 0.35),
    )

    # Initialize simulation
    sim.reset()
    hand.reset()

    sim_dt = sim.get_physics_dt()

    # -------------------------------------------------------------------------
    # Articulation information
    # -------------------------------------------------------------------------

    print("\n" + "=" * 72)

    print("[INFO] LEAP Hand v1 Right initialized")

    print(
        f"[INFO] USD:\n"
        f"       {LEAP_USD_PATH}"
    )

    print(
        f"[INFO] Number of joints: "
        f"{hand.num_joints}"
    )

    print("\n[INFO] Joint names:")

    for i, name in enumerate(hand.joint_names):
        print(
            f"    [{i:2d}] {name}"
        )

    print("=" * 72)

    if hand.num_joints != 16:
        raise RuntimeError(
            f"Expected 16 movable joints, "
            f"but Isaac Lab detected {hand.num_joints}."
        )

    # -------------------------------------------------------------------------
    # Joint limits
    # -------------------------------------------------------------------------

    limits = hand.data.soft_joint_pos_limits.torch[0]

    lower = limits[:, 0]
    upper = limits[:, 1]

    print("\n[INFO] Joint position limits:")

    for i, name in enumerate(hand.joint_names):

        print(
            f"    [{i:2d}] joint {name:>2s}: "
            f"{lower[i].item(): .3f} "
            f"to "
            f"{upper[i].item(): .3f} rad"
        )

    # -------------------------------------------------------------------------
    # Test configuration
    # -------------------------------------------------------------------------

    # Put all joints at the center of their valid range.
    center = (
        (lower + upper) / 2.0
    ).unsqueeze(0)

    # For safety, use only 25% of each joint's half range.
    #
    # Example:
    # total valid range = 2 rad
    # half range        = 1 rad
    # test amplitude    = 0.375 rad
    amplitudes = (
        0.375
        * (upper - lower)
        / 2.0
    )

    # Each joint gets four seconds.
    #
    # During these four seconds it completes:
    #
    # center
    #   -> positive direction
    #   -> center
    #   -> negative direction
    #   -> center
    #
    test_duration = 2.0

    print("\n" + "=" * 72)

    print(
        "[INFO] Sequential joint test starting."
    )

    print(
        "[INFO] Only ONE joint moves at a time."
    )

    print(
        f"[INFO] Time per joint: "
        f"{test_duration:.1f} seconds"
    )

    print(
        "[INFO] Test amplitude: "
        "25% of each joint's half-range."
    )

    print(
        "[INFO] Full 0-15 cycle: "
        f"{16 * test_duration:.0f} seconds"
    )

    print(
        "[INFO] After joint 15, "
        "testing automatically returns to joint 0."
    )

    print(
        "[INFO] Press Ctrl+C once to stop."
    )

    print("=" * 72 + "\n")

    # -------------------------------------------------------------------------
    # Simulation loop
    # -------------------------------------------------------------------------

    elapsed_time = 0.0
    last_joint_id = -1

    while (
        simulation_app.is_running()
        and not stop_requested
    ):

        # Which joint should currently move?
        joint_id = (
            int(
                elapsed_time
                // test_duration
            )
            % 16
        )

        # Print only when switching to a new joint.
        if joint_id != last_joint_id:

            print("\n" + "-" * 60)

            print(
                f"[TEST] Joint index : "
                f"{joint_id}"
            )

            print(
                f"[TEST] Joint name  : "
                f"{hand.joint_names[joint_id]}"
            )

            print(
                f"[TEST] Limits      : "
                f"{lower[joint_id].item():.3f} "
                f"to "
                f"{upper[joint_id].item():.3f} rad"
            )

            print(
                f"[TEST] Center      : "
                f"{center[0, joint_id].item():.3f} rad"
            )

            print(
                f"[TEST] Amplitude   : "
                f"±{amplitudes[joint_id].item():.3f} rad"
            )

            print("-" * 60)

            last_joint_id = joint_id

        # All joints remain at center.
        targets = center.clone()

        # Local time within the current 4-second test.
        local_time = (
            elapsed_time
            % test_duration
        )

        # One complete sinusoidal cycle.
        angle = (
            2.0
            * math.pi
            * local_time
            / test_duration
        )

        # Move only the current joint.
        targets[0, joint_id] = (
            center[0, joint_id]
            + amplitudes[joint_id]
            * math.sin(angle)
        )

        # Extra safety clamp to imported limits.
        targets = torch.maximum(
            targets,
            lower.unsqueeze(0),
        )

        targets = torch.minimum(
            targets,
            upper.unsqueeze(0),
        )

        # Command joint positions.
        hand.set_joint_position_target(
            targets
        )

        # Apply commands.
        hand.write_data_to_sim()

        # Physics step.
        sim.step()

        # Refresh Isaac Lab buffers.
        hand.update(sim_dt)

        elapsed_time += sim_dt


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

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
