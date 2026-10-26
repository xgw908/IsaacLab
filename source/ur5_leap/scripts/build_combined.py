# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Expand official UR5 xacro and combine it with the official website v1 Right URDF."""

from __future__ import annotations

import copy
import json
import os
import shutil
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import xacro
from asset_utils import COMBINED, LEAP, ROOT, UR5, resolve_resource


def write_urdf(robot: ET.Element, path: Path) -> None:
    """Write a deterministic derived file; upstream originals are never changed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(robot, space="  ")
    path.write_bytes(ET.tostring(robot, encoding="utf-8", xml_declaration=True) + b"\n")


def rebase_meshes(robot: ET.Element, source: Path, destination: Path, packages: dict[str, Path]) -> None:
    """Express existing meshes relative to the generated URDF directory."""
    for mesh in robot.findall(".//mesh"):
        original = resolve_resource(mesh.attrib["filename"], source, packages)
        mesh.set("filename", Path(os.path.relpath(original, destination.parent)).as_posix())


def expand_ur5() -> Path:
    """Expand only ur_type=ur5, with ROS package lookup substituted in a temporary copy."""
    output = UR5 / "generated/ur5_cb3.urdf"
    with tempfile.TemporaryDirectory(prefix="ur5-xacro-") as temporary:
        package = Path(temporary) / "ur_description"
        shutil.copytree(UR5 / "urdf", package / "urdf")
        shutil.copytree(UR5 / "config", package / "config")
        for path in (package / "urdf").rglob("*.xacro"):
            text = path.read_text(encoding="utf-8").replace("$(find ur_description)", package.as_posix())
            path.write_text(text, encoding="utf-8")
        document = xacro.process_file(
            str(package / "urdf/ur.urdf.xacro"), mappings={"ur_type": "ur5", "name": "ur5_cb3"}
        )
        robot = ET.fromstring(document.toxml())
    rebase_meshes(robot, UR5 / "urdf/ur.urdf.xacro", output, {"ur_description": UR5})
    write_urdf(robot, output)
    return output


def prepare_right_hand() -> tuple[Path, Path]:
    """Require the explicitly named official Right archive; do not silently substitute another hand."""
    candidates = sorted((LEAP / "urdf/website_right").rglob("*.urdf"))
    matching = []
    for candidate in candidates:
        robot = ET.parse(candidate).getroot()
        children = {joint.find("child").attrib["link"] for joint in robot.findall("joint")}
        roots = {link.attrib["name"] for link in robot.findall("link")} - children
        active = [joint for joint in robot.findall("joint") if joint.attrib["type"] != "fixed"]
        if roots == {"palm_lower"} and len(active) == 16:
            matching.append(candidate)
    if len(matching) != 1:
        raise ValueError(f"Expected one official website Right URDF with root palm_lower and 16 DoF; found {matching}")
    source = matching[0]
    robot = ET.parse(source).getroot()
    destination = LEAP / "generated/leap_hand_right.urdf"
    # The official Right archive uses package:///filename, an empty ROS package name.
    # Resolve that exact upstream convention against its own directory in this derived view.
    rebase_meshes(robot, source, destination, {"": source.parent})
    write_urdf(robot, destination)
    return source, destination


def build() -> None:
    ur5_path = expand_ur5()
    hand_original, hand_path = prepare_right_hand()
    robot = ET.parse(ur5_path).getroot()
    robot.set("name", "ur5_cb3_leap_v1_right")
    # Only the arm base is anchored during USD import. Preserve all remaining official arm frames.
    for joint in list(robot.findall("joint")):
        if joint.find("parent").get("link") == "world":
            robot.remove(joint)
    for link in list(robot.findall("link")):
        if link.get("name") == "world":
            robot.remove(link)
    combined_path = COMBINED / "urdf/ur5_leap_right.urdf"
    rebase_meshes(robot, ur5_path, combined_path, {})
    hand = ET.parse(hand_path).getroot()
    rebase_meshes(hand, hand_path, combined_path, {})
    arm_links = {link.get("name") for link in robot.findall("link")}
    if arm_links & {link.get("name") for link in hand.findall("link")}:
        raise ValueError("Arm/hand link name collision; resolve explicitly before combining")
    joint_mapping = {joint.get("name"): f"leap_joint_{joint.get('name')}" for joint in hand.findall("joint")}
    for joint in hand.findall("joint"):
        joint.set("name", joint_mapping[joint.get("name")])
        mimic = joint.find("mimic")
        if mimic is not None:
            mimic.set("joint", joint_mapping[mimic.get("joint")])
    mounting = json.loads((COMBINED / "config/mounting.json").read_text(encoding="utf-8"))
    robot.append(ET.Comment(" PLACEHOLDER: TODO: replace with measured lab UR5 flange → LEAP palm transform. "))
    robot.append(
        ET.Comment(" mounting_adapter is an empty frame; no measured adapter mesh, mass or inertia is asserted. ")
    )
    ET.SubElement(robot, "link", name="mounting_adapter")
    for name, parent, child, transform in [
        ("flange_to_adapter", "flange", "mounting_adapter", mounting["flange_to_adapter"]),
        ("adapter_to_palm", "mounting_adapter", "palm_lower", mounting["adapter_to_palm"]),
    ]:
        joint = ET.SubElement(robot, "joint", name=name, type="fixed")
        ET.SubElement(joint, "parent", link=parent)
        ET.SubElement(joint, "child", link=child)
        ET.SubElement(
            joint, "origin", xyz=" ".join(map(str, transform["xyz"])), rpy=" ".join(map(str, transform["rpy"]))
        )
    for child in hand:
        robot.append(copy.deepcopy(child))
    write_urdf(robot, combined_path)
    control_order = [
        "shoulder_pan_joint",
        "shoulder_lift_joint",
        "elbow_joint",
        "wrist_1_joint",
        "wrist_2_joint",
        "wrist_3_joint",
    ]
    control_order += [joint_mapping[str(index)] for index in range(16)]
    metadata = {
        "hand_original": hand_original.relative_to(ROOT).as_posix(),
        "ur5_type": "ur5",
        "movable_joints": 22,
        "mounting_status": mounting["status"],
        "leap_joint_name_mapping": joint_mapping,
        "recommended_control_order": control_order,
        "note": (
            "Resolve simulator joint indices by name. XML order and simulator joint order are not guaranteed to match."
        ),
    }
    (COMBINED / "config/joint_mapping.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Built {combined_path.relative_to(ROOT)} from official assets; mounting={mounting['status']}")


if __name__ == "__main__":
    build()
