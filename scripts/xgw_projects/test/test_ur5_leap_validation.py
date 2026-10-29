import argparse
import math

from isaaclab.app import AppLauncher

# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

parser = argparse.ArgumentParser(description="Validate UR5 + LEAP 22-DoF models.")
parser.add_argument(
    "--model",
    type=str,
    choices=["full", "simple"],
    default="full",
    help="full = official LEAP, simple = CordViP simplified LEAP",
)

AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# -----------------------------------------------------------------------------
# Isaac Lab
# -----------------------------------------------------------------------------

import torch

import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import Articulation, ArticulationCfg
from isaaclab.sim import SimulationCfg, SimulationContext


# -----------------------------------------------------------------------------
# Model
# -----------------------------------------------------------------------------

ROOT = "/workspace/isaaclab"

if args_cli.model == "full":
    USD_PATH = (
        ROOT
        + "/source/ur5_leap/assets/combined/ur5_leap/generated/usd/"
        + "ur5_leap.usd/ur5_leap/ur5_leap.usda"
    )
    PRIM_PATH = "/World/UR5Leap"
else:
    USD_PATH = (
        ROOT
        + "/source/ur5_leap/assets/combined/ur5_simple_leap/generated/usd/"
        + "ur5_simple_leap.usd/ur5_simple_leap/ur5_simple_leap.usda"
    )
    PRIM_PATH = "/World/UR5SimpleLeap"


UR5_NAMES = [
    "shoulder_pan_joint",
    "shoulder_lift_joint",
    "elbow_joint",
    "wrist_1_joint",
    "wrist_2_joint",
    "wrist_3_joint",
]

LEAP_NAMES = [f"leap_joint_{i}" for i in range(16)]

EXPECTED_NAMES = UR5_NAMES + LEAP_NAMES


# -----------------------------------------------------------------------------
# Robot cfg
# -----------------------------------------------------------------------------

ROBOT_CFG = ArticulationCfg(
    prim_path=PRIM_PATH,
    spawn=sim_utils.UsdFileCfg(
        usd_path=USD_PATH,
        activate_contact_sensors=False,
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0.0, 0.0, 0.0),
        joint_pos={
            ".*": 0.0,
        },
    ),
    actuators={
        "ur5_arm": ImplicitActuatorCfg(
            joint_names_expr=[
                "shoulder_pan_joint",
                "shoulder_lift_joint",
                "elbow_joint",
            ],
            effort_limit_sim=150.0,
            velocity_limit_sim=3.15,
            stiffness=100.0,
            damping=10.0,
        ),
        "ur5_wrist": ImplicitActuatorCfg(
            joint_names_expr=[
                "wrist_1_joint",
                "wrist_2_joint",
                "wrist_3_joint",
            ],
            effort_limit_sim=28.0,
            velocity_limit_sim=3.2,
            stiffness=80.0,
            damping=8.0,
        ),
        "leap_hand": ImplicitActuatorCfg(
            joint_names_expr=["leap_joint_.*"],
            effort_limit_sim=0.95,
            velocity_limit_sim=8.0,
            stiffness=3.0,
            damping=0.1,
        ),
    },
)


def step_robot(sim, robot, target, steps):
    """Hold the given target for N simulation steps."""
    dt = sim.get_physics_dt()

    for _ in range(steps):
        robot.set_joint_position_target(target)
        robot.write_data_to_sim()

        sim.step()
        robot.update(dt)


def smooth_move(sim, robot, start, goal, duration):
    """Linear interpolation between two joint targets."""
    dt = sim.get_physics_dt()
    steps = max(1, int(duration / dt))

    for i in range(steps):
        alpha = (i + 1) / steps
        target = start + alpha * (goal - start)

        robot.set_joint_position_target(target)
        robot.write_data_to_sim()

        sim.step()
        robot.update(dt)


def main():
    # -------------------------------------------------------------------------
    # Simulator
    # -------------------------------------------------------------------------

    sim_cfg = SimulationCfg(
        dt=1.0 / 120.0,
        device=args_cli.device,
    )

    sim = SimulationContext(sim_cfg)

    sim.set_camera_view(
        eye=(1.8, 1.8, 1.4),
        target=(0.0, 0.0, 0.45),
    )

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
    robot = Articulation(ROBOT_CFG)

    sim.reset()
    robot.reset()

    # Warm up
    for _ in range(20):
        robot.write_data_to_sim()
        sim.step()
        robot.update(sim.get_physics_dt())

    # -------------------------------------------------------------------------
    # Joint recognition
    # -------------------------------------------------------------------------

    joint_names = list(robot.joint_names)

    print()
    print("=" * 72)
    print("UR5 + LEAP VALIDATION")
    print("=" * 72)
    print(f"Model        : {args_cli.model}")
    print(f"USD          : {USD_PATH}")
    print(f"Prim         : {PRIM_PATH}")
    print(f"Joint count  : {len(joint_names)}")
    print()

    for i, name in enumerate(joint_names):
        print(f"[{i:02d}] {name}")

    print()
    print("-" * 72)

    missing = [name for name in EXPECTED_NAMES if name not in joint_names]
    unexpected = [name for name in joint_names if name not in EXPECTED_NAMES]

    ur5_found = sum(name in joint_names for name in UR5_NAMES)
    leap_found = sum(name in joint_names for name in LEAP_NAMES)

    print(f"UR5 joints   : {ur5_found}/6")
    print(f"LEAP joints  : {leap_found}/16")

    if len(joint_names) == 22 and not missing and not unexpected:
        print("22-DoF check : PASS")
    else:
        print("22-DoF check : FAIL")

        if missing:
            print("Missing:")
            for name in missing:
                print("  ", name)

        if unexpected:
            print("Unexpected:")
            for name in unexpected:
                print("  ", name)

        simulation_app.close()
        return

    print("=" * 72)
    print()

    # Always map by JOINT NAME, never assume tensor index.
    idx = {name: joint_names.index(name) for name in EXPECTED_NAMES}

    # -------------------------------------------------------------------------
    # Combined UR5 + LEAP continuous motion
    # -------------------------------------------------------------------------

    # UR5 sinusoidal motion:
    # q = center + amplitude * sin(omega * t + phase)
    #
    # Same motion style as the previous standalone
    # test_ur5_articulation.py.

    arm_center = {
        "shoulder_pan_joint": 0.0,
        "shoulder_lift_joint": -math.pi / 2.0,
        "elbow_joint": 0.0,
        "wrist_1_joint": -math.pi / 2.0,
        "wrist_2_joint": 0.0,
        "wrist_3_joint": 0.0,
    }

    arm_phases = {
        "shoulder_pan_joint": 0.0,
        "shoulder_lift_joint": math.pi / 6.0,
        "elbow_joint": math.pi / 3.0,
        "wrist_1_joint": math.pi / 2.0,
        "wrist_2_joint": 2.0 * math.pi / 3.0,
        "wrist_3_joint": 5.0 * math.pi / 6.0,
    }

    arm_amplitudes = {
        "shoulder_pan_joint": 0.30,
        "shoulder_lift_joint": 0.30,
        "elbow_joint": 0.60,
        "wrist_1_joint": 0.60,
        "wrist_2_joint": 0.60,
        "wrist_3_joint": 0.60,
    }

    frequency = 0.50
    omega = 2.0 * math.pi * frequency

    # LEAP close targets.
    close_values = {
        "leap_joint_0": 0.00,
        "leap_joint_1": 1.20,
        "leap_joint_2": 1.10,
        "leap_joint_3": 1.10,

        "leap_joint_4": 0.00,
        "leap_joint_5": 1.20,
        "leap_joint_6": 1.10,
        "leap_joint_7": 1.10,

        "leap_joint_8": 0.00,
        "leap_joint_9": 1.20,
        "leap_joint_10": 1.10,
        "leap_joint_11": 1.10,

        "leap_joint_12": 0.80,
        "leap_joint_13": 0.90,
        "leap_joint_14": 0.90,
        "leap_joint_15": 0.70,
    }

    print()
    print("[PASS] Articulation initialized successfully.")
    print("[ACTION] UR5 sinusoidal motion + LEAP continuous open/close.")
    print("UR5 amplitudes:")
    print("  shoulder_pan_joint  : 0.30 rad")
    print("  shoulder_lift_joint : 0.30 rad")
    print("  elbow_joint         : 0.60 rad")
    print("  wrist_1_joint       : 0.60 rad")
    print("  wrist_2_joint       : 0.60 rad")
    print("  wrist_3_joint       : 0.60 rad")
    print("Frequency             : 0.50 Hz")
    print("Period        : 2.0 s")
    print("Press Ctrl+C to stop.")
    print()

    dt = sim.get_physics_dt()
    t = 0.0
    last_hand_state = None

    try:
        while simulation_app.is_running():

            target = robot.data.joint_pos.clone()

            # -------------------------------------------------------------
            # UR5: six joints move sinusoidally around the working pose.
            # -------------------------------------------------------------
            for name in UR5_NAMES:
                value = (
                    arm_center[name]
                    + arm_amplitudes[name]
                    * math.sin(omega * t + arm_phases[name])
                )
                target[:, idx[name]] = value

            # -------------------------------------------------------------
            # LEAP: continuously open -> close -> open.
            #
            # alpha:
            # t = 0 s   -> 0.0  open
            # t = 1 s   -> 1.0  closed
            # t = 2 s   -> 0.0  open
            # -------------------------------------------------------------
            alpha = 0.5 * (1.0 - math.cos(omega * t))

            # Print only fully open / fully closed states.
            hand_state = None

            if alpha < 0.03:
                hand_state = "OPEN"
            elif alpha > 0.97:
                hand_state = "CLOSED"

            if hand_state is not None and hand_state != last_hand_state:
                print(f"[LEAP] {hand_state}")
                last_hand_state = hand_state

            for name in LEAP_NAMES:
                target[:, idx[name]] = alpha * close_values[name]

            # UR5 and LEAP targets are written in the SAME simulation step.
            robot.set_joint_position_target(target)
            robot.write_data_to_sim()

            sim.step()
            robot.update(dt)

            t += dt

    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
    simulation_app.close()
