#!/usr/bin/env python3
"""ContextSift 一键打包脚本（零依赖，仅标准库）。

产出：
  releases/contextsift-<version>.tar.gz
  releases/contextsift-<version>.zip
  releases/checksums.sha256

用法：
  python3 scripts/build.py
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RELEASES = ROOT / "releases"
VERSION_FILE = ROOT / "contextsift" / "__init__.py"

INCLUDE = [
    "contextsift",
    "tests",
    "README.md",
    "README_EN.md",
    "README_zh-TW.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "pyproject.toml",
    ".gitignore",
]
EXCLUDE_DIRS = {"__pycache__", ".git", "releases", "*.egg-info"}
EXCLUDE_FILES = {".pyc", ".DS_Store"}


def read_version() -> str:
    import re

    text = VERSION_FILE.read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*["\']([^"\']+)', text)
    if not m:
        raise RuntimeError("cannot find __version__")
    return m.group(1)


def iter_files(base: Path):
    for item in INCLUDE:
        path = ROOT / item
        if not path.exists():
            continue
        if path.is_file():
            yield path, path.relative_to(ROOT)
            continue
        for f in path.rglob("*"):
            if not f.is_file():
                continue
            if any(part in EXCLUDE_DIRS for part in f.parts):
                continue
            if f.suffix in EXCLUDE_FILES or "__pycache__" in f.parts:
                continue
            yield f, f.relative_to(ROOT)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    version = read_version()
    if RELEASES.exists():
        shutil.rmtree(RELEASES)
    RELEASES.mkdir(parents=True)

    tgz = RELEASES / f"contextsift-{version}.tar.gz"
    zpath = RELEASES / f"contextsift-{version}.zip"

    with tarfile.open(tgz, "w:gz") as tf:
        for f, rel in iter_files(ROOT):
            tf.add(f, arcname=str(Path("contextsift") / rel), recursive=False)

    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        for f, rel in iter_files(ROOT):
            zf.write(f, arcname=str(Path("contextsift") / rel))

    checksums = RELEASES / "checksums.sha256"
    lines = [f"{sha256(p)}  {p.name}" for p in (tgz, zpath)]
    checksums.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Built ContextSift {version}")
    for p in (tgz, zpath, checksums):
        print(f"  {p.relative_to(ROOT)}  ({p.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
