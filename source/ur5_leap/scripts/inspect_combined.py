# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Inspect our connected 22-DoF model or an unchanged third-party reference."""

import argparse

from asset_utils import BODEX, COMBINED, CORDVIP, inspect_urdf, print_inspection

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=["ours", "cordvip", "bodex", "bodex-simplified"], default="ours")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    models = {
        "ours": (COMBINED / "urdf/ur5_leap_right.urdf", {}),
        "cordvip": (CORDVIP / "ur5_leaphand.urdf", {}),
        "bodex": (BODEX / "urdf/ur5_leap.urdf", {"ur_description": BODEX}),
        "bodex-simplified": (BODEX / "urdf/ur5_leap_simplified.urdf", {"ur_description": BODEX}),
    }
    model, packages = models[args.model]
    result = inspect_urdf(model, 22, packages)
    if args.model == "ours":
        expected = {("flange", "mounting_adapter"), ("mounting_adapter", "palm_lower")}
        actual = {(joint["parent"], joint["child"]) for joint in result["joints"] if joint["type"] == "fixed"}
        if not expected <= actual:
            result["errors"].append("Required flange -> adapter -> palm fixed chain is missing")
            result["passed"] = False
    print_inspection(result, args.json)
