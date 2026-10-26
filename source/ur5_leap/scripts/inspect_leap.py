# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Inspect the official website Right URDF and the original LEAP Hand Sim model."""

import argparse

from asset_utils import LEAP, inspect_urdf, print_inspection

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--sim-reference", action="store_true")
    args = parser.parse_args()
    model = LEAP / ("sim_reference/leap_hand/robot.urdf" if args.sim_reference else "generated/leap_hand_right.urdf")
    print_inspection(inspect_urdf(model, 16), args.json)
