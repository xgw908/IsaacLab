"""View BODex UR5 + dexterous hand combined model."""

import argparse
import signal
from pathlib import Path

from isaaclab.app import AppLauncher


parser = argparse.ArgumentParser(
    description="View BODex UR5 + hand combined model."
)

AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app


import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import Articulation, ArticulationCfg


ISAACLAB_ROOT = Path(__file__).resolve().parents[3]

USD_ROOT = (
    ISAACLAB_ROOT
    / "source"
    / "ur5_leap"
    / "assets"
    / "references"
    / "bodex"
    / "generated"
    / "usd"
    / "bodex_ur5_leap.usd"
)

candidates = list(USD_ROOT.glob("*/*.usda"))

if not candidates:
    raise FileNotFoundError(
        f"No main BODex USD found under:\n{USD_ROOT}"
    )

ROBOT_USD_PATH = candidates[0]

print("\n[INFO] Loading BODex USD:")
print(ROBOT_USD_PATH)


ROBOT_CFG = ArticulationCfg(
    prim_path="/World/BODex",

    spawn=sim_utils.UsdFileCfg(
        usd_path=str(ROBOT_USD_PATH),
    ),

    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0.0, 0.0, 0.0),
    ),

    actuators={
        "all": ImplicitActuatorCfg(
            joint_names_expr=[".*"],
            joint_effort_limit=150.0,
            joint_velocity_limit=3.0,
            stiffness=40.0,
            damping=5.0,
        ),
    },
)


stop_requested = False


def stop_handler(signum, frame):
    global stop_requested
    stop_requested = True


signal.signal(signal.SIGINT, stop_handler)
signal.signal(signal.SIGTERM, stop_handler)


def main():

    sim_cfg = sim_utils.SimulationCfg(
        dt=0.01,
        device=args_cli.device,
    )

    sim = sim_utils.SimulationContext(sim_cfg)

    ground_cfg = sim_utils.GroundPlaneCfg()
    ground_cfg.func(
        "/World/GroundPlane",
        ground_cfg,
    )

    light_cfg = sim_utils.DomeLightCfg(
        intensity=3000.0,
    )
    light_cfg.func(
        "/World/Light",
        light_cfg,
    )

    robot = Articulation(
        cfg=ROBOT_CFG,
    )

    sim.set_camera_view(
        eye=(1.4, 1.4, 1.1),
        target=(0.0, 0.0, 0.45),
    )

    sim.reset()
    robot.reset()

    sim_dt = sim.get_physics_dt()

    print("\n" + "=" * 80)
    print("[INFO] BODex combined model")
    print(f"[INFO] Movable joints: {robot.num_joints}")
    print("=" * 80)

    for index, name in enumerate(robot.joint_names):
        print(
            f"    index {index:2d} -> {name}"
        )

    target = (
        robot.data.default_joint_pos
        .torch
        .clone()
    )

    print("\n[INFO] Viewing only. Ctrl+C to stop.\n")

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


if __name__ == "__main__":

    try:
        main()

    finally:
        simulation_app.close()
