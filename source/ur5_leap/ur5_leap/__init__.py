# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Asset configurations and registered reinforcement learning tasks for UR5 + LEAP."""

import importlib.metadata

from isaaclab.utils.module import lazy_export

# Register Gym tasks without loading environment configurations or starting simulation.
from . import tasks  # noqa: F401

try:
    __version__ = importlib.metadata.version("ur5_leap")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"

lazy_export()
