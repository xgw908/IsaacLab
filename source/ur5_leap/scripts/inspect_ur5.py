# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Inspect the expanded official UR5 CB3, without starting Isaac Sim."""

import argparse

from asset_utils import UR5, inspect_urdf, print_inspection

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    print_inspection(inspect_urdf(UR5 / "generated/ur5_cb3.urdf", 6), args.json)
