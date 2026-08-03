#!/usr/bin/env python3
"""Validate Lovelace dashboard YAML syntax (local, no HA required)."""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("error: PyYAML required (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <dashboard.yaml>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"error: not a file: {path}", file=sys.stderr)
        return 1

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        print(f"YAML error: {exc}", file=sys.stderr)
        return 1

    if data is None:
        print("warning: empty file")
        return 0

    if not isinstance(data, dict):
        print("error: root must be a mapping (dict)", file=sys.stderr)
        return 1

    if "views" in data and not isinstance(data["views"], list):
        print("error: 'views' must be a list", file=sys.stderr)
        return 1

    view_count = len(data.get("views", []))
    print(f"ok: {path.name} ({view_count} view(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
