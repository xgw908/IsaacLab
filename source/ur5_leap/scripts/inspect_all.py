# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Inspect all models, verify provenance, and write the requested inventory and validation reports."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from asset_utils import BODEX, COMBINED, CORDVIP, LEAP, ROOT, UR5, inspect_urdf, resolve_resource
from download_assets import verify_receipts


def _fingerprint(element: ET.Element, model: Path, rename: dict[str, str] | None = None) -> tuple:
    attributes = dict(element.attrib)
    if element.tag == "mesh":
        attributes["filename"] = resolve_resource(attributes["filename"], model, {}).relative_to(ROOT).as_posix()
    if element.tag == "joint" and rename:
        attributes["name"] = rename.get(attributes.get("name"), attributes.get("name"))
    return (
        element.tag,
        sorted(attributes.items()),
        (element.text or "").strip(),
        [_fingerprint(child, model, rename) for child in element],
    )


def _verify_components() -> None:
    combined_path = COMBINED / "urdf/ur5_leap_right.urdf"
    combined = ET.parse(combined_path).getroot()
    for source in [UR5 / "generated/ur5_cb3.urdf", LEAP / "generated/leap_hand_right.urdf"]:
        original = ET.parse(source).getroot()
        rename = {str(index): f"leap_joint_{index}" for index in range(16)} if source.parent.parent == LEAP else {}
        for node in original:
            if node.get("name") == "world" or (node.tag == "joint" and node.find("parent").get("link") == "world"):
                continue
            name = rename.get(node.get("name"), node.get("name")) if node.tag == "joint" else node.get("name")
            match = next((candidate for candidate in combined.findall(node.tag) if candidate.get("name") == name), None)
            if match is None or _fingerprint(node, source, rename) != _fingerprint(match, combined_path):
                raise ValueError(f"Combined model changed official component: {source.name}/{name}")
    expected = {("flange", "mounting_adapter"), ("mounting_adapter", "palm_lower")}
    actual = {
        (joint.find("parent").get("link"), joint.find("child").get("link"))
        for joint in combined.findall("joint")
        if joint.get("type") == "fixed"
    }
    if not expected <= actual:
        raise ValueError("Missing fixed flange -> mounting_adapter -> palm_lower chain")


def _write_inventory(receipt: dict) -> None:
    limit = json.loads((ROOT / "assets/sources.lock.json").read_text(encoding="utf-8"))["git_max_file_bytes"]
    large = sorted(
        (path for path in ROOT.rglob("*") if path.is_file() and path.stat().st_size > limit),
        key=lambda path: path.relative_to(ROOT).as_posix(),
    )
    ignore = [
        "# Large upstream assets stay on disk and are restored by scripts/download_assets.py.",
        "__pycache__/",
        "*.py[cod]",
        ".venv/",
        "generated_usd/",
        "# Retain these small inputs despite parent rules for USD and generated files.",
        "!/assets/official/ur5/generated/*.urdf",
        "!/assets/official/leap_hand_v1_right/generated/*.urdf",
        "!/assets/official/leap_hand_v1_right/isaac_lab_reference/**/*.usd",
    ]
    ignore += ["/" + path.relative_to(ROOT).as_posix() for path in large]
    (ROOT / ".gitignore").write_text("\n".join(ignore) + "\n", encoding="utf-8")
    large_rows = [f"| `{path.relative_to(ROOT).as_posix()}` | {path.stat().st_size:,} |" for path in large]
    large_text = "# 本地保留的大文件\n\n仓库单文件上限为 2,000 KiB。以下文件保留在本地，未强行加入 Git，也没有删除。\n"
    large_text += "服务器拉取 Git 后运行下载脚本恢复；每个文件的 SHA-256 见 `../assets/downloads.json`。\n\n"
    large_text += "| 文件 | 字节数 |\n|---|---:|\n" + "\n".join(large_rows) + "\n"
    (ROOT / "docs/large_files.md").write_text(large_text, encoding="utf-8")
    rows = [
        f"| `{item['destination']}` | {item['source']} | {item['size']:,} | `{item['sha256']}` |"
        for item in receipt["files"]
    ]
    text = "# 实际下载清单\n\n下载时间（UTC）：" + receipt["retrieved_at_utc"] + "\n\n"
    text += (
        "按字节校验原始文件；Git LFS 文件校验真实 payload 的 SHA-256。"
        "原始路径、URL 和 LFS oid 见 `../assets/downloads.json`。\n\n"
    )
    text += "| 本地相对路径 | 来源 ID | 字节数 | SHA-256 |\n|---|---|---:|---|\n" + "\n".join(rows) + "\n\n"
    text += (
        "## 未能下载的文件\n\n"
        + (
            json.dumps(receipt["failures"], indent=2, ensure_ascii=False)
            if receipt["failures"]
            else "无。要求的官网 Right URDF、完整装配 STEP、安装板 STL/STP 和五个 GitHub 来源均已获取。"
        )
        + "\n"
    )
    (ROOT / "docs/download_inventory.md").write_text(text, encoding="utf-8")


def _write_tree() -> None:
    lines = ["source/ur5_leap/"]

    def walk(directory: Path, prefix: str) -> None:
        entries = sorted(
            (path for path in directory.iterdir() if path.name not in {"__pycache__", ".venv"}),
            key=lambda path: (not path.is_dir(), path.name),
        )
        for index, entry in enumerate(entries):
            last = index == len(entries) - 1
            lines.append(prefix + ("└── " if last else "├── ") + entry.name + ("/" if entry.is_dir() else ""))
            if entry.is_dir():
                walk(entry, prefix + ("    " if last else "│   "))

    walk(ROOT, "")
    (ROOT / "docs/directory_tree.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    receipt = json.loads((ROOT / "assets/downloads.json").read_text(encoding="utf-8"))
    verify_receipts(receipt["files"])
    models = {
        "ur5_cb3": (UR5 / "generated/ur5_cb3.urdf", 6, {}),
        "leap_right_website_original": (LEAP / "urdf/website_right/robot.urdf", 16, {"": LEAP / "urdf/website_right"}),
        "leap_right_portable": (LEAP / "generated/leap_hand_right.urdf", 16, {}),
        "leap_sim_original": (LEAP / "sim_reference/leap_hand/robot.urdf", 16, {}),
        "combined": (COMBINED / "urdf/ur5_leap_right.urdf", 22, {}),
        "cordvip": (CORDVIP / "ur5_leaphand.urdf", 22, {}),
        "bodex": (BODEX / "urdf/ur5_leap.urdf", 22, {"ur_description": BODEX}),
        "bodex_simplified": (BODEX / "urdf/ur5_leap_simplified.urdf", 22, {"ur_description": BODEX}),
        "bodex_hand": (BODEX / "urdf/leap_hand.urdf", 16, {"ur_description": BODEX}),
        "bodex_hand_simplified": (BODEX / "urdf/leap_hand_simplified.urdf", 16, {"ur_description": BODEX}),
    }
    results = {name: inspect_urdf(path, dof, packages) for name, (path, dof, packages) in models.items()}
    _verify_components()
    report = {
        "scope": "Static URDF/resource validation only; no Isaac Sim import or physics stepping",
        "official_components_preserved": True,
        "original_downloads_verified": len(receipt["files"]),
        "models": results,
    }
    (docs / "validation.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# 静态检查结果",
        "",
        "只做 XML、树结构、关节限制、资源与原始文件校验；未做 USD 转换、动力学或真机验证。",
        "",
        "| 模型 | 结果 | 根 link | 可动关节 | 唯一 mesh |",
        "|---|---|---|---:|---:|",
    ]
    for name, result in results.items():
        lines.append(
            f"| {name} | {'PASS' if result['passed'] else 'FAIL'} | {', '.join(result['roots'])} "
            f"| {result['movable_joints']} | {len(result['meshes'])} |"
        )
        print(
            f"{name}: {'PASS' if result['passed'] else 'FAIL'}; DoF={result['movable_joints']}; root={result['roots']}"
        )
    lines += [
        "",
        "原始下载文件 SHA-256 全部通过。联合模型的官方 link/joint、惯量、碰撞、限制和实际 mesh 目标"
        "与独立模型逐项比较通过；允许的变换只有去掉 UR5 的 world 锚定、重命名手关节、"
        "重定位相对路径和添加两个占位 fixed joint。",
        "",
        "官网 Right 原文件需要显式空包名映射；BODex 需要把 ur_description 映射到其资产根。"
        "原文件保持不变，便携生成版本消除了这些依赖。",
        "",
        "## 联合模型 22 关节顺序",
        "",
        "以下是 XML 顺序；仿真器导入后仍须按名称解析索引。",
        "",
        "```text",
    ]
    lines += [f"{index:02d} {name}" for index, name in enumerate(results["combined"]["joint_order_xml"])] + ["```", ""]
    (docs / "validation.md").write_text("\n".join(lines), encoding="utf-8")
    _write_inventory(receipt)
    _write_tree()
    failed = [name for name, result in results.items() if not result["passed"]]
    if failed:
        raise SystemExit(f"Static inspection failed: {failed}")


if __name__ == "__main__":
    main()
