# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Restore pinned upstream assets without changing their bytes; no simulator is needed."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "assets/sources.lock.json"
RECEIPT_PATH = ROOT / "assets/downloads.json"
CAD_PAGE = "https://v1.leaphand.com/leap_cad"


def fetch(url: str) -> bytes:
    """Read a public upstream URL with certificate validation and a finite timeout."""
    request = urllib.request.Request(url, headers={"User-Agent": "ur5-leap-asset-workspace/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return response.read()
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        # Some Windows TLS routes interrupt large STEP responses; curl uses the OS TLS stack.
        curl = shutil.which("curl.exe") or shutil.which("curl")
        if curl is None:
            raise
        return subprocess.run(
            [
                curl,
                "--fail",
                "--location",
                "--silent",
                "--show-error",
                "--retry",
                "2",
                "--retry-all-errors",
                "--max-time",
                "90",
                url,
            ],
            check=True,
            capture_output=True,
        ).stdout


def save_original(destination: Path, data: bytes) -> None:
    """Save original bytes, refusing to overwrite a different existing file."""
    destination = destination.resolve()
    if not destination.is_relative_to(ROOT):
        raise ValueError(f"Destination escapes asset workspace: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.read_bytes() != data:
            raise ValueError(f"Existing file differs; refusing to overwrite: {destination}")
        return
    destination.write_bytes(data)


def _receipt(destination: str, data: bytes, **metadata: object) -> dict:
    return {
        "destination": destination,
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        **metadata,
    }


def _download_source(source: dict) -> list[dict]:
    repository, commit = source["repository"], source["commit"]
    if RECEIPT_PATH.exists():
        previous = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        previous_entries = [entry for entry in previous["files"] if entry.get("source") == source["id"]]
        expected_paths = {item["destination"] for item in source["files"]}
        if {entry["destination"] for entry in previous_entries} == expected_paths and all(
            (ROOT / entry["destination"]).is_file()
            and hashlib.sha256((ROOT / entry["destination"]).read_bytes()).hexdigest() == entry["sha256"]
            for entry in previous_entries
        ):
            print(f"Verified existing {source['id']}: {len(previous_entries)} files", flush=True)
            return previous_entries
    # Archives avoid raw.githubusercontent.com availability and unauthenticated API rate limits.
    archive_url = f"https://codeload.github.com/{repository}/zip/{commit}"
    print(f"Downloading {repository}@{commit[:12]}", flush=True)
    archive_data = fetch(archive_url)
    entries = []
    with zipfile.ZipFile(io.BytesIO(archive_data)) as archive:
        prefix = archive.namelist()[0].split("/")[0] + "/"
        for item in source["files"]:
            data = archive.read(prefix + item["path"])
            blob_sha = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
            if blob_sha != item["git_blob_sha1"]:
                raise ValueError(f"Git blob checksum mismatch: {repository}/{item['path']}")
            metadata = {"source": source["id"], "original_path": item["path"], "url": item["url"]}
            if data.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
                pointer = data.decode("ascii")
                expected_sha = re.search(r"oid sha256:([0-9a-f]{64})", pointer).group(1)
                expected_size = int(re.search(r"size (\d+)", pointer).group(1))
                lfs_url = f"https://media.githubusercontent.com/media/{repository}/{commit}/{item['path']}"
                data = fetch(lfs_url)
                if len(data) != expected_size or hashlib.sha256(data).hexdigest() != expected_sha:
                    raise ValueError(f"Git LFS checksum mismatch: {item['path']}")
                metadata.update(lfs_oid_sha256=expected_sha, lfs_url=lfs_url)
            save_original(ROOT / item["destination"], data)
            entries.append(_receipt(item["destination"], data, **metadata))
    print(f"Verified {source['id']}: {len(entries)} files", flush=True)
    return entries


class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            self.links.append((" ".join("".join(self._text).split()), self._href))
            self._href = None


def _download_website() -> tuple[list[dict], list[dict]]:
    """Use recorded URLs and hashes on restore; discover the official page only on first acquisition."""
    if RECEIPT_PATH.exists():
        previous = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        entries = [entry for entry in previous["files"] if entry.get("source") == "website"]
        required = {
            "right_urdf.zip",
            "full_assembly_right.stp",
            "palm_upper_xarm_franka_ur5.stl",
            "palm_upper_xarm_franka_ur5.stp",
            "leap_cad.html",
        }
        if required <= {Path(entry["destination"]).name for entry in entries}:
            archives = {}
            for entry in entries:
                destination = ROOT / entry["destination"]
                if destination.exists():
                    data = destination.read_bytes()
                elif "archive_member" in entry:
                    url = entry["url"]
                    if url not in archives:
                        archives[url] = fetch(url)
                    with zipfile.ZipFile(io.BytesIO(archives[url])) as archive:
                        data = archive.read(entry["archive_member"])
                else:
                    print(f"Restoring official CAD: {entry['destination']}", flush=True)
                    data = fetch(entry["url"])
                if len(data) != entry["size"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
                    raise ValueError(f"Pinned website content mismatch: {entry['destination']}")
                save_original(destination, data)
            print(f"Verified pinned official website: {len(entries)} files", flush=True)
            return entries, []
    entries, failures = [], []
    html = fetch(CAD_PAGE)
    page_destination = "assets/official/leap_hand_v1_right/cad/leap_cad.html"
    save_original(ROOT / page_destination, html)
    entries.append(_receipt(page_destination, html, source="website", url=CAD_PAGE))
    parser = _Links()
    parser.feed(html.decode("utf-8"))
    targets = {
        "Download Right URDF": "right_urdf.zip",
        "Download Right STP": "full_assembly_right.stp",
        "Xarm/Franka/UR5 STL": "palm_upper_xarm_franka_ur5.stl",
        "Xarm/Franka/UR5 STP": "palm_upper_xarm_franka_ur5.stp",
    }
    for label, filename in targets.items():
        href = next((href for text, href in parser.links if text.casefold() == label.casefold()), None)
        if href is None:
            failures.append({"source": "website", "label": label, "error": "Download label not found in official HTML"})
            continue
        url = urllib.parse.urljoin(CAD_PAGE, href)
        destination = f"assets/official/leap_hand_v1_right/cad/{filename}"
        try:
            print(f"Downloading official CAD: {label}: {url}", flush=True)
            data = fetch(url)
            if filename.endswith(".zip") and not zipfile.is_zipfile(io.BytesIO(data)):
                raise ValueError("Official URDF download is not a ZIP archive")
            if filename.endswith(".stp") and b"ISO-10303-21" not in data[:1000]:
                raise ValueError("Official STEP download is not ISO-10303-21 data")
            if filename.endswith(".stl"):
                binary_stl = len(data) >= 84 and 84 + 50 * int.from_bytes(data[80:84], "little") == len(data)
                if not binary_stl and not data.lstrip().lower().startswith(b"solid"):
                    raise ValueError("Official STL download does not have an STL header")
            save_original(ROOT / destination, data)
            entries.append(_receipt(destination, data, source="website", label=label, url=url))
            if filename.endswith(".zip"):
                with zipfile.ZipFile(io.BytesIO(data)) as archive:
                    for member in archive.infolist():
                        if member.is_dir():
                            continue
                        member_path = PurePosixPath(member.filename.replace("\\", "/"))
                        if member_path.is_absolute() or ".." in member_path.parts or ":" in member.filename:
                            raise ValueError(f"Unsafe archive member: {member.filename}")
                        relative = f"assets/official/leap_hand_v1_right/urdf/website_right/{member_path}"
                        member_data = archive.read(member)
                        save_original(ROOT / relative, member_data)
                        entries.append(
                            _receipt(relative, member_data, source="website", url=url, archive_member=member.filename)
                        )
        except Exception as exc:
            failures.append({"source": "website", "label": label, "url": url, "error": str(exc)})
    return entries, failures


def verify_receipts(receipts: list[dict]) -> None:
    """Check original content hashes, including hydrated Git LFS payloads."""
    for item in receipts:
        path = ROOT / item["destination"]
        if not path.is_file():
            raise FileNotFoundError(path)
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"Downloaded content changed: {path}")
    print(f"Original bytes verified: {len(receipts)} files")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", action="append", choices=["ur", "sim", "lab", "cord", "bodex"])
    parser.add_argument(
        "--website", action="store_true", help="Also fetch the official v1 Right CAD and URDF downloads."
    )
    parser.add_argument("--website-only", action="store_true", help="Fetch only the official website resources.")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    args.website = args.website or args.website_only
    existing = (
        json.loads(RECEIPT_PATH.read_text(encoding="utf-8")) if RECEIPT_PATH.exists() else {"files": [], "failures": []}
    )
    if args.verify_only:
        verify_receipts(existing["files"])
        return
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    selected = [] if args.website_only else (args.source or [source["id"] for source in lock["sources"]])
    receipts = {item["destination"]: item for item in existing["files"]}
    failures = [
        failure
        for failure in existing["failures"]
        if failure["source"] not in selected and not (args.website and failure["source"] == "website")
    ]
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {
            pool.submit(_download_source, source): source for source in lock["sources"] if source["id"] in selected
        }
        for future in as_completed(futures):
            source = futures[future]
            try:
                for entry in future.result():
                    receipts[entry["destination"]] = entry
            except Exception as exc:
                failures.append({"source": source["id"], "error": str(exc)})
                print(f"Download failed for {source['id']}: {exc}", flush=True)
    if args.website:
        try:
            website_entries, website_failures = _download_website()
            for entry in website_entries:
                receipts[entry["destination"]] = entry
            failures.extend(website_failures)
        except Exception as exc:
            failures.append({"source": "website", "error": str(exc)})
    report = {
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": sorted(receipts.values(), key=lambda item: item["destination"]),
        "failures": failures,
    }
    RECEIPT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Downloaded {len(receipts)} files; failures: {json.dumps(failures, ensure_ascii=False)}", flush=True)
    if any(failure["source"] != "website" for failure in failures):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
