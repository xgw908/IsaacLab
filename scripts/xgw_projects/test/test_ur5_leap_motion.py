"""UR5 CB3 + LEAP Hand Right combined motion test.

Stage 1:
    Move UR5 smoothly from its default pose to a working pose.

Stage 2:
    Hold UR5 still.
    LEAP Hand repeatedly performs:

        OPEN -> CLOSE -> OPEN

Combined articulation:
    UR5  : 6 DoF
    LEAP : 16 DoF
    Total: 22 DoF
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

LOCK_PATH = "/tmp/xgw_test_ur5_leap_motion.lock"
_lock_file = open(LOCK_PATH, "w")

try:
    fcntl.flock(
        _lock_file,
        fcntl.LOCK_EX | fcntl.LOCK_NB,
    )
except BlockingIOError:
    raise RuntimeError(
        "test_ur5_leap_motion.py is already running."
    )


# =============================================================================
# Launcher
# =============================================================================

parser = argparse.ArgumentParser(
    description="UR5 + LEAP Hand combined motion test."
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

    actuators={

        # ---------------------------------------------------------------------
        # UR5
        # ---------------------------------------------------------------------

        "ur5_arm": ImplicitActuatorCfg(
            joint_names_expr=[
                "shoulder_pan_joint",
                "shoulder_lift_joint",
                "elbow_joint",
                "wrist_1_joint",
                "wrist_2_joint",
                "wrist_3_joint",
            ],

            joint_effort_limit=150.0,
            joint_velocity_limit=1.0,
            stiffness=100.0,
            damping=10.0,
        ),

        # ---------------------------------------------------------------------
        # LEAP Hand
        # ---------------------------------------------------------------------

        "leap_hand": ImplicitActuatorCfg(
            joint_names_expr=[
                "leap_joint_.*",
            ],

            joint_effort_limit=0.95,
            joint_velocity_limit=8.0,
            stiffness=3.0,
            damping=0.1,
        ),
    },
)


# =============================================================================
# Shutdown
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
# Smooth interpolation
# =============================================================================

def smooth_alpha(alpha: float) -> float:
    """0 -> 1 cosine interpolation with zero velocity at both ends."""

    alpha = max(0.0, min(1.0, alpha))

    return (
        0.5
        - 0.5
        * math.cos(
            math.pi * alpha
        )
    )


# =============================================================================
# Helper
# =============================================================================

def set_joint_by_name(
    target_tensor,
    robot,
    joint_name,
    value,
):
    """Set one target value by actual Isaac Lab joint name."""

    if joint_name not in robot.joint_names:
        raise RuntimeError(
            f"Joint '{joint_name}' not found."
        )

    index = robot.joint_names.index(
        joint_name
    )

    target_tensor[
        0,
        index
    ] = value


# =============================================================================
# Main
# =============================================================================

def main():

    if not ROBOT_USD_PATH.exists():
        raise FileNotFoundError(
            f"Combined USD not found:\n{ROBOT_USD_PATH}"
        )

    # -------------------------------------------------------------------------
    # Simulation
    # -------------------------------------------------------------------------

    sim_cfg = sim_utils.SimulationCfg(
        dt=0.01,
        device=args_cli.device,
    )

    sim = sim_utils.SimulationContext(
        sim_cfg
    )

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

    # Robot
    robot = Articulation(
        cfg=ROBOT_CFG,
    )

    # Camera
    sim.set_camera_view(
        eye=(1.3, 1.3, 1.2),
        target=(0.0, 0.0, 0.5),
    )

    sim.reset()
    robot.reset()

    sim_dt = sim.get_physics_dt()

    # -------------------------------------------------------------------------
    # Validate articulation
    # -------------------------------------------------------------------------

    if robot.num_joints != 22:
        raise RuntimeError(
            f"Expected 22 joints, got {robot.num_joints}."
        )

    print("\n" + "=" * 82)
    print("[INFO] UR5 + LEAP combined motion test")
    print("=" * 82)

    print(
        f"[INFO] Total joints: "
        f"{robot.num_joints}"
    )

    print("\n[INFO] Joint order:")

    for index, name in enumerate(
        robot.joint_names
    ):
        print(
            f"    {index:2d}"
            f" -> {name}"
        )

    # -------------------------------------------------------------------------
    # Joint limits
    # -------------------------------------------------------------------------

    limits = (
        robot.data
        .soft_joint_pos_limits
        .torch[0]
    )

    lower = limits[:, 0]
    upper = limits[:, 1]

    # -------------------------------------------------------------------------
    # Starting pose
    # -------------------------------------------------------------------------

    start_pose = (
        robot.data
        .default_joint_pos
        .torch
        .clone()
    )

    # -------------------------------------------------------------------------
    # UR5 working pose
    # -------------------------------------------------------------------------

    working_pose = (
        start_pose.clone()
    )

    #
    # Same basic working configuration used in our UR5-only validation.
    #
    # shoulder_pan  = 0
    # shoulder_lift = -90 deg
    # elbow         = 0
    # wrist_1       = -90 deg
    # wrist_2       = 0
    # wrist_3       = 0
    #

    ur5_working_targets = {
        "shoulder_pan_joint": 0.0,
        "shoulder_lift_joint": -math.pi / 2.0,
        "elbow_joint": 0.0,
        "wrist_1_joint": -math.pi / 2.0,
        "wrist_2_joint": 0.0,
        "wrist_3_joint": 0.0,
    }

    for joint_name, value in (
        ur5_working_targets.items()
    ):

        set_joint_by_name(
            working_pose,
            robot,
            joint_name,
            value,
        )

    # -------------------------------------------------------------------------
    # LEAP OPEN pose
    # -------------------------------------------------------------------------

    open_pose = (
        working_pose.clone()
    )

    for joint_number in range(16):

        set_joint_by_name(
            open_pose,
            robot,
            f"leap_joint_{joint_number}",
            0.0,
        )

    # -------------------------------------------------------------------------
    # LEAP CLOSE pose
    # -------------------------------------------------------------------------

    close_pose = (
        open_pose.clone()
    )

    #
    # Mapping already verified:
    #
    # Index finger:
    #   leap_joint_0 ~ leap_joint_3
    #
    # Middle finger:
    #   leap_joint_4 ~ leap_joint_7
    #
    # Ring finger:
    #   leap_joint_8 ~ leap_joint_11
    #
    # Thumb:
    #   leap_joint_12 ~ leap_joint_15
    #

    close_targets = {

        # -------------------------------------------------------------
        # Index finger
        # -------------------------------------------------------------

        "leap_joint_0": 0.00,
        "leap_joint_1": 1.20,
        "leap_joint_2": 1.10,
        "leap_joint_3": 1.10,

        # -------------------------------------------------------------
        # Middle finger
        # -------------------------------------------------------------

        "leap_joint_4": 0.00,
        "leap_joint_5": 1.20,
        "leap_joint_6": 1.10,
        "leap_joint_7": 1.10,

        # -------------------------------------------------------------
        # Ring finger
        # -------------------------------------------------------------

        "leap_joint_8": 0.00,
        "leap_joint_9": 1.20,
        "leap_joint_10": 1.10,
        "leap_joint_11": 1.10,

        # -------------------------------------------------------------
        # Thumb
        # -------------------------------------------------------------

        "leap_joint_12": 0.80,
        "leap_joint_13": 0.90,
        "leap_joint_14": 0.90,
        "leap_joint_15": 0.70,
    }

    for joint_name, value in (
        close_targets.items()
    ):

        set_joint_by_name(
            close_pose,
            robot,
            joint_name,
            value,
        )

    # -------------------------------------------------------------------------
    # Safety clamp
    # -------------------------------------------------------------------------

    working_pose = torch.maximum(
        working_pose,
        lower.unsqueeze(0),
    )

    working_pose = torch.minimum(
        working_pose,
        upper.unsqueeze(0),
    )

    open_pose = torch.maximum(
        open_pose,
        lower.unsqueeze(0),
    )

    open_pose = torch.minimum(
        open_pose,
        upper.unsqueeze(0),
    )

    close_pose = torch.maximum(
        close_pose,
        lower.unsqueeze(0),
    )

    close_pose = torch.minimum(
        close_pose,
        upper.unsqueeze(0),
    )

    # -------------------------------------------------------------------------
    # Print control mapping
    # -------------------------------------------------------------------------

    print("\n" + "=" * 82)
    print("[INFO] UR5 working pose")
    print("=" * 82)

    for joint_name, value in (
        ur5_working_targets.items()
    ):

        index = robot.joint_names.index(
            joint_name
        )

        print(
            f"    {joint_name:25s}"
            f" index={index:2d}"
            f" target={value: .3f}"
        )

    print("\n" + "=" * 82)
    print("[INFO] LEAP mapping")
    print("=" * 82)

    finger_groups = {
        "Index finger": range(0, 4),
        "Middle finger": range(4, 8),
        "Ring finger": range(8, 12),
        "Thumb": range(12, 16),
    }

    for finger_name, numbers in (
        finger_groups.items()
    ):

        print(f"\n{finger_name}:")

        for number in numbers:

            name = (
                f"leap_joint_{number}"
            )

            index = (
                robot.joint_names.index(
                    name
                )
            )

            print(
                f"    {name:15s}"
                f" -> tensor index "
                f"{index:2d}"
            )

    # -------------------------------------------------------------------------
    # Stage timing
    # -------------------------------------------------------------------------

    #
    # First 3 seconds:
    #
    # default posture -> UR5 working posture
    #
    move_to_working_duration = 3.0

    #
    # Then:
    #
    # 2 seconds OPEN -> CLOSE
    # 2 seconds CLOSE -> OPEN
    #
    hand_half_cycle = 2.0
    hand_full_cycle = 4.0

    print("\n" + "=" * 82)
    print("[INFO] Motion sequence")
    print("=" * 82)

    print(
        "[INFO] Stage 1: "
        "UR5 moves to working pose in 3 s"
    )

    print(
        "[INFO] Stage 2: "
        "UR5 holds position"
    )

    print(
        "[INFO]          "
        "LEAP OPEN -> CLOSE in 2 s"
    )

    print(
        "[INFO]          "
        "LEAP CLOSE -> OPEN in 2 s"
    )

    print(
        "[INFO] Ctrl+C to stop."
    )

    print("=" * 82 + "\n")

    # -------------------------------------------------------------------------
    # Main loop
    # -------------------------------------------------------------------------

    elapsed_time = 0.0
    last_phase = None

    while (
        simulation_app.is_running()
        and not stop_requested
    ):

        # =====================================================================
        # Stage 1
        # =====================================================================

        if elapsed_time < (
            move_to_working_duration
        ):

            phase = "UR5 -> WORKING POSE"

            alpha = (
                elapsed_time
                / move_to_working_duration
            )

            s = smooth_alpha(alpha)

            target = (
                (1.0 - s)
                * start_pose
                +
                s
                * open_pose
            )

        # =====================================================================
        # Stage 2
        # =====================================================================

        else:

            hand_time = (
                elapsed_time
                - move_to_working_duration
            )

            cycle_time = (
                hand_time
                % hand_full_cycle
            )

            # -------------------------------------------------------------
            # OPEN -> CLOSE
            # -------------------------------------------------------------

            if cycle_time < (
                hand_half_cycle
            ):

                phase = (
                    "LEAP CLOSING"
                )

                alpha = (
                    cycle_time
                    / hand_half_cycle
                )

                s = smooth_alpha(
                    alpha
                )

                target = (
                    (1.0 - s)
                    * open_pose
                    +
                    s
                    * close_pose
                )

            # -------------------------------------------------------------
            # CLOSE -> OPEN
            # -------------------------------------------------------------

            else:

                phase = (
                    "LEAP OPENING"
                )

                alpha = (
                    cycle_time
                    - hand_half_cycle
                ) / hand_half_cycle

                s = smooth_alpha(
                    alpha
                )

                target = (
                    (1.0 - s)
                    * close_pose
                    +
                    s
                    * open_pose
                )

        # ---------------------------------------------------------------------
        # Print phase changes
        # ---------------------------------------------------------------------

        if phase != last_phase:

            print(
                f"[INFO] {phase}"
            )

            last_phase = phase

        # ---------------------------------------------------------------------
        # Final safety clamp
        # ---------------------------------------------------------------------

        target = torch.maximum(
            target,
            lower.unsqueeze(0),
        )

        target = torch.minimum(
            target,
            upper.unsqueeze(0),
        )

        # ---------------------------------------------------------------------
        # Send target
        # ---------------------------------------------------------------------

        robot.set_joint_position_target(
            target
        )

        robot.write_data_to_sim()

        sim.step()

        robot.update(
            sim_dt
        )

        elapsed_time += (
            sim_dt
        )


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
