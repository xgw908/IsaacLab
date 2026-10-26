# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Shared, simulator-independent URDF inspection and resource resolution."""

from __future__ import annotations

import json
import math
import ntpath
import os
import shlex
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
UR5 = ROOT / "assets/official/ur5"
LEAP = ROOT / "assets/official/leap_hand_v1_right"
COMBINED = ROOT / "assets/combined/ur5_leap_right"
CORDVIP = ROOT / "assets/references/cordvip/ur5_leaphand"
BODEX = ROOT / "assets/references/bodex/ur5_leap"
MOVABLE = {"revolute", "continuous", "prismatic", "planar", "floating"}


def resolve_resource(filename: str, urdf_path: Path, packages: dict[str, Path]) -> Path:
    """Resolve a URI with explicit ROS package mappings and Linux case-sensitive names."""
    filename = unquote(filename)
    if filename.startswith("package://"):
        package, relative = filename[len("package://") :].split("/", 1)
        if package not in packages:
            raise ValueError(f"Unmapped ROS package: {package}")
        path = packages[package] / relative
    elif "://" in filename or ntpath.isabs(filename) or Path(filename).is_absolute():
        raise ValueError(f"Nonportable resource URI: {filename}")
    else:
        path = urdf_path.parent / filename
    if "\\" in filename:
        raise ValueError(f"Windows path separator in resource: {filename}")
    # Normalize '..' without resolving Windows filename case before the Linux portability check.
    path = Path(os.path.abspath(path))
    if not path.is_relative_to(ROOT):
        raise ValueError(f"Resource escapes asset workspace: {filename}")
    if not path.is_file():
        raise FileNotFoundError(filename)
    # Windows would otherwise hide filename case mistakes that fail on Linux.
    current = ROOT
    for part in path.relative_to(ROOT).parts:
        names = {child.name for child in current.iterdir()}
        if part not in names:
            raise ValueError(f"Resource case mismatch: {filename}")
        current /= part
    path = path.resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError(f"Resource symlink escapes asset workspace: {filename}")
    with path.open("rb") as stream:
        if stream.read(100).startswith(b"version https://git-lfs.github.com/spec/"):
            raise ValueError(f"Unhydrated Git LFS pointer: {filename}")
    return path


def mesh_dependencies(mesh: Path) -> list[str]:
    """Return direct external rendering dependencies; embedded GLB data needs no extra file."""
    if mesh.suffix.lower() == ".obj":
        return [
            line[7:].strip() for line in mesh.read_text(encoding="utf-8").splitlines() if line.startswith("mtllib ")
        ]
    if mesh.suffix.lower() == ".mtl":
        result = []
        for line in mesh.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith(("map_", "bump ", "disp ", "decal ")):
                result.append(shlex.split(line, posix=False)[-1].strip('"'))
        return result
    if mesh.suffix.lower() == ".dae":
        root = ET.parse(mesh).getroot()
        return [element.text.strip() for element in root.findall(".//{*}image/{*}init_from") if element.text]
    return []


def inspect_urdf(urdf_path: Path, expected_dof: int, packages: dict[str, Path] | None = None) -> dict:
    """Validate a connected tree, finite joint limits, and actual mesh/dependency files."""
    packages = packages or {}
    robot = ET.parse(urdf_path).getroot()
    errors, rendering_errors = [], []
    links = [link.attrib["name"] for link in robot.findall("link")]
    joints = robot.findall("joint")
    joint_names = [joint.attrib["name"] for joint in joints]
    if len(links) != len(set(links)) or len(joint_names) != len(set(joint_names)):
        errors.append("Duplicate link or joint names")
    parents, children = {}, {name: [] for name in links}
    active = []
    joint_records = []
    for joint in joints:
        name, joint_type = joint.attrib["name"], joint.attrib["type"]
        parent, child = joint.find("parent").attrib["link"], joint.find("child").attrib["link"]
        if parent not in children or child not in children:
            errors.append(f"Unknown parent/child in {name}")
            continue
        if child in parents:
            errors.append(f"Multiple parents for {child}")
        parents[child] = parent
        children[parent].append((child, joint))
        origin = joint.find("origin")
        record = {
            "name": name,
            "type": joint_type,
            "parent": parent,
            "child": child,
            "xyz": origin.get("xyz", "0 0 0") if origin is not None else "0 0 0",
            "rpy": origin.get("rpy", "0 0 0") if origin is not None else "0 0 0",
        }
        if joint_type in MOVABLE:
            if joint.find("mimic") is None:
                active.append(name)
            limits = joint.find("limit")
            record["limits"] = dict(limits.attrib) if limits is not None else {}
            required = (
                ("effort", "velocity", "lower", "upper")
                if joint_type in {"revolute", "prismatic"}
                else ("effort", "velocity")
            )
            try:
                values = {key: float(record["limits"][key]) for key in required}
                if not all(math.isfinite(value) for value in values.values()):
                    raise ValueError("nonfinite value")
                if values["effort"] <= 0 or values["velocity"] <= 0:
                    raise ValueError("nonpositive effort/velocity")
                if "lower" in values and values["lower"] > values["upper"]:
                    raise ValueError("reversed position limits")
            except (KeyError, ValueError) as exc:
                errors.append(f"Invalid limits for {name}: {exc}")
        joint_records.append(record)
    roots = sorted(set(links) - parents.keys())
    visited, traversal, walking = set(), [], set()

    def visit(name: str) -> None:
        if name in walking:
            errors.append(f"Cycle at {name}")
            return
        if name in visited:
            return
        visited.add(name)
        walking.add(name)
        for child, joint in children[name]:
            if joint.attrib["type"] in MOVABLE and joint.find("mimic") is None:
                traversal.append(joint.attrib["name"])
            visit(child)
        walking.remove(name)

    for root in roots:
        visit(root)
    if len(roots) != 1 or len(visited) != len(links) or len(joints) != len(links) - 1:
        errors.append(f"Not one complete tree: roots={roots}, visited={len(visited)}/{len(links)}")
    if len(active) != expected_dof:
        errors.append(f"Expected {expected_dof} active joints, found {len(active)}")
    meshes = {}
    for mesh in robot.findall(".//mesh"):
        filename = mesh.attrib["filename"]
        try:
            resolved = resolve_resource(filename, urdf_path, packages)
            meshes[filename] = resolved.relative_to(ROOT).as_posix()
        except (ValueError, FileNotFoundError) as exc:
            errors.append(f"Mesh: {exc}")
    checked = set()
    pending = [ROOT / relative for relative in meshes.values()]
    while pending:
        mesh = pending.pop()
        if mesh in checked:
            continue
        checked.add(mesh)
        for dependency in mesh_dependencies(mesh):
            try:
                pending.append(resolve_resource(dependency, mesh, packages))
            except (ValueError, FileNotFoundError) as exc:
                rendering_errors.append(f"{mesh.relative_to(ROOT).as_posix()}: {exc}")
    return {
        "file": urdf_path.relative_to(ROOT).as_posix(),
        "robot_name": robot.get("name"),
        "roots": roots,
        "links": len(links),
        "movable_joints": len(active),
        "joint_order_xml": active,
        "joint_order_tree": traversal,
        "joints": joint_records,
        "visuals": len(robot.findall(".//visual")),
        "collisions": len(robot.findall(".//collision")),
        "inertials": len(robot.findall(".//inertial")),
        "meshes": meshes,
        "rendering_dependencies_checked": len(checked),
        "rendering_errors": sorted(set(rendering_errors)),
        "errors": sorted(set(errors)),
        "passed": not errors and not rendering_errors,
    }


def print_inspection(result: dict, json_output: bool = False) -> None:
    """Print machine-readable evidence or a compact model report, and return a failing exit status."""
    if json_output:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"{result['file']}: {'PASS' if result['passed'] else 'FAIL'}")
        print(f"roots={result['roots']}; DoF={result['movable_joints']}; meshes={len(result['meshes'])}")
        print("Joint order (XML, not a simulator indexing guarantee):")
        for index, name in enumerate(result["joint_order_xml"]):
            print(f"  {index:2d}: {name}")
        for error in result["errors"] + result["rendering_errors"]:
            print(f"  ERROR: {error}")
    if not result["passed"]:
        raise SystemExit(1)
