"""LEAP Hand v1 Right joint mapping test v2.

Purpose:
- Do NOT assume any finger/joint mapping.
- Test original LEAP joints 0 -> 15 in numerical order.
- Only one joint moves at a time.
- For every joint:
    neutral -> positive -> neutral -> negative -> neutral
- Print:
    original LEAP number
    Isaac/USD joint name
    Isaac Lab tensor index
    position limits

Use the WebRTC view to record the actual physical mapping.
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

LOCK_PATH = "/tmp/xgw_test_leap_joint_mapping_v2.lock"
_lock_file = open(LOCK_PATH, "w")

try:
    fcntl.flock(
        _lock_file,
        fcntl.LOCK_EX | fcntl.LOCK_NB,
    )
except BlockingIOError:
    raise RuntimeError(
        "test_leap_joint_mapping_v2.py is already running.\n"
        "Stop the previous process before starting another one."
    )


# -----------------------------------------------------------------------------
# Launcher
# -----------------------------------------------------------------------------

parser = argparse.ArgumentParser(
    description="LEAP Hand v1 Right joint mapping test v2."
)

AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app


# Isaac Lab imports after SimulationApp
import torch

import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import Articulation, ArticulationCfg


# -----------------------------------------------------------------------------
# Asset
# -----------------------------------------------------------------------------

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
# LEAP configuration
# -----------------------------------------------------------------------------

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


# -----------------------------------------------------------------------------
# Clean shutdown
# -----------------------------------------------------------------------------

stop_requested = False


def request_stop(signum, frame):
    global stop_requested

    if not stop_requested:
        print("\n[INFO] Stop requested. Closing cleanly...")

    stop_requested = True


signal.signal(signal.SIGINT, request_stop)
signal.signal(signal.SIGTERM, request_stop)


# -----------------------------------------------------------------------------
# Smooth interpolation
# -----------------------------------------------------------------------------

def smoothstep(alpha: float) -> float:
    """Cosine interpolation from 0 to 1."""
    return 0.5 - 0.5 * math.cos(math.pi * alpha)


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

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

    # Hand
    hand = Articulation(cfg=LEAP_CFG)

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

    limits = hand.data.soft_joint_pos_limits.torch[0]

    lower = limits[:, 0]
    upper = limits[:, 1]

    print("\n" + "=" * 78)
    print("[INFO] LEAP Hand joint mapping test v2")
    print("[INFO] No finger mapping is assumed.")
    print("[INFO] Testing original LEAP joint numbers 0 -> 15.")
    print("=" * 78)

    print("\n[INFO] Actual Isaac Lab tensor order:")

    for tensor_index, joint_name in enumerate(hand.joint_names):

        print(
            f"    tensor index {tensor_index:2d}"
            f" -> {joint_name}"
            f"    limits:"
            f" [{lower[tensor_index].item(): .3f},"
            f" {upper[tensor_index].item(): .3f}]"
        )

    # -------------------------------------------------------------------------
    # Build original-number -> Isaac tensor-index mapping
    # -------------------------------------------------------------------------

    joint_mapping = []

    for original_number in range(16):

        usd_name = f"tn__{original_number}_"

        if usd_name not in hand.joint_names:

            raise RuntimeError(
                f"Expected imported joint '{usd_name}' not found."
            )

        tensor_index = hand.joint_names.index(usd_name)

        joint_mapping.append(
            (
                original_number,
                usd_name,
                tensor_index,
            )
        )

    print("\n[INFO] Original LEAP number -> Isaac mapping:")

    for original_number, usd_name, tensor_index in joint_mapping:

        print(
            f"    LEAP {original_number:2d}"
            f" -> {usd_name:8s}"
            f" -> tensor index {tensor_index:2d}"
        )

    # -------------------------------------------------------------------------
    # Neutral pose
    # -------------------------------------------------------------------------

    # Use zero as the neutral/open reference whenever zero is valid.
    # If zero is outside a joint's limits, clamp it safely.
    neutral = torch.zeros(
        (1, hand.num_joints),
        device=hand.device,
        dtype=torch.float32,
    )

    neutral = torch.maximum(
        neutral,
        lower.unsqueeze(0),
    )

    neutral = torch.minimum(
        neutral,
        upper.unsqueeze(0),
    )

    # -------------------------------------------------------------------------
    # Timing
    # -------------------------------------------------------------------------

    # Every joint gets 2 seconds:
    #
    # 0.00 - 0.50 : neutral -> positive
    # 0.50 - 1.00 : positive -> neutral
    # 1.00 - 1.50 : neutral -> negative
    # 1.50 - 2.00 : negative -> neutral
    #
    joint_test_duration = 2.0
    segment_duration = joint_test_duration / 4.0

    print("\n" + "=" * 78)
    print("[INFO] Test pattern for EACH joint:")
    print("[INFO] 0.0-0.5 s : NEUTRAL -> POSITIVE")
    print("[INFO] 0.5-1.0 s : POSITIVE -> NEUTRAL")
    print("[INFO] 1.0-1.5 s : NEUTRAL -> NEGATIVE")
    print("[INFO] 1.5-2.0 s : NEGATIVE -> NEUTRAL")
    print("[INFO]")
    print("[INFO] One complete 0-15 round = 32 seconds.")
    print("[INFO] Press Ctrl+C once to stop.")
    print("=" * 78 + "\n")

    # -------------------------------------------------------------------------
    # Simulation loop
    # -------------------------------------------------------------------------

    elapsed_time = 0.0

    last_original_number = -1
    last_direction = None

    while (
        simulation_app.is_running()
        and not stop_requested
    ):

        # -------------------------------------------------------------
        # Which original LEAP joint are we testing?
        # -------------------------------------------------------------

        original_number = (
            int(elapsed_time // joint_test_duration)
            % 16
        )

        usd_name = f"tn__{original_number}_"

        tensor_index = hand.joint_names.index(
            usd_name
        )

        local_time = (
            elapsed_time
            % joint_test_duration
        )

        # -------------------------------------------------------------
        # Choose visible but safe positive / negative targets
        # -------------------------------------------------------------

        joint_lower = lower[tensor_index].item()
        joint_upper = upper[tensor_index].item()

        neutral_value = neutral[0, tensor_index].item()

        # Move 60% from neutral toward each physical limit.
        positive_target = (
            neutral_value
            + 0.60
            * (
                joint_upper
                - neutral_value
            )
        )

        negative_target = (
            neutral_value
            + 0.60
            * (
                joint_lower
                - neutral_value
            )
        )

        # -------------------------------------------------------------
        # Print new joint
        # -------------------------------------------------------------

        if original_number != last_original_number:

            print("\n" + "-" * 78)

            print(
                f"[TEST] ORIGINAL LEAP JOINT : "
                f"{original_number}"
            )

            print(
                f"[TEST] USD / Isaac name    : "
                f"{usd_name}"
            )

            print(
                f"[TEST] Tensor index        : "
                f"{tensor_index}"
            )

            print(
                f"[TEST] Limits              : "
                f"{joint_lower:.3f}"
                f" -> "
                f"{joint_upper:.3f} rad"
            )

            print(
                f"[TEST] Neutral             : "
                f"{neutral_value:.3f} rad"
            )

            print(
                f"[TEST] Positive target     : "
                f"{positive_target:.3f} rad"
            )

            print(
                f"[TEST] Negative target     : "
                f"{negative_target:.3f} rad"
            )

            print("-" * 78)

            last_original_number = original_number
            last_direction = None

        # -------------------------------------------------------------
        # Other 15 joints stay neutral
        # -------------------------------------------------------------

        targets = neutral.clone()

        # -------------------------------------------------------------
        # Phase 1: neutral -> positive
        # -------------------------------------------------------------

        if local_time < segment_duration:

            direction = "POSITIVE"

            alpha = (
                local_time
                / segment_duration
            )

            s = smoothstep(alpha)

            value = (
                (1.0 - s)
                * neutral_value
                +
                s
                * positive_target
            )

        # -------------------------------------------------------------
        # Phase 2: positive -> neutral
        # -------------------------------------------------------------

        elif local_time < 2.0 * segment_duration:

            direction = "POSITIVE -> NEUTRAL"

            alpha = (
                (
                    local_time
                    - segment_duration
                )
                / segment_duration
            )

            s = smoothstep(alpha)

            value = (
                (1.0 - s)
                * positive_target
                +
                s
                * neutral_value
            )

        # -------------------------------------------------------------
        # Phase 3: neutral -> negative
        # -------------------------------------------------------------

        elif local_time < 3.0 * segment_duration:

            direction = "NEGATIVE"

            alpha = (
                (
                    local_time
                    - 2.0 * segment_duration
                )
                / segment_duration
            )

            s = smoothstep(alpha)

            value = (
                (1.0 - s)
                * neutral_value
                +
                s
                * negative_target
            )

        # -------------------------------------------------------------
        # Phase 4: negative -> neutral
        # -------------------------------------------------------------

        else:

            direction = "NEGATIVE -> NEUTRAL"

            alpha = (
                (
                    local_time
                    - 3.0 * segment_duration
                )
                / segment_duration
            )

            s = smoothstep(alpha)

            value = (
                (1.0 - s)
                * negative_target
                +
                s
                * neutral_value
            )

        if direction != last_direction:

            print(
                f"[MOVE] joint {original_number:2d}"
                f" | {usd_name:8s}"
                f" | {direction}"
            )

            last_direction = direction

        targets[0, tensor_index] = value

        # -------------------------------------------------------------
        # Extra safety
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
        # Command + physics
        # -------------------------------------------------------------

        hand.set_joint_position_target(
            targets
        )

        hand.write_data_to_sim()

        sim.step()

        hand.update(sim_dt)

        elapsed_time += sim_dt


# -----------------------------------------------------------------------------
# Entry
# -----------------------------------------------------------------------------

if __name__ == "__main__":

    try:
        main()

    finally:
        print("\n[INFO] Closing Isaac Sim...")
        simulation_app.close()
        print("[INFO] Isaac Sim closed.")
