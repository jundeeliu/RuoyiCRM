#!/usr/bin/env python3
"""Offline RuoyiCRM dual-run compare, or read-only write-isolation preflight."""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

try:
    from .compare import ComparisonError, compare_http
    from .fence import FenceError, authorize_write
except ImportError:
    from compare import ComparisonError, compare_http
    from fence import FenceError, authorize_write


def response(path):
    if Path(path).stat().st_size > 3_000_000:
        raise ComparisonError("response file exceeds bounded capture size")
    obj = json.loads(Path(path).read_text())
    if type(obj) is not dict or set(obj) != {"status", "content_type", "body_base64"}:
        raise ComparisonError("response file requires exact status/content_type/body_base64")
    if type(obj["body_base64"]) is not str:
        raise ComparisonError("body_base64 must be a string")
    if len(obj["body_base64"]) > 2_800_000:
        raise ComparisonError("body_base64 exceeds bounded capture size")
    return {"status": obj["status"], "content_type": obj["content_type"],
            "body": base64.b64decode(obj["body_base64"], validate=True)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    diff = sub.add_parser("compare")
    diff.add_argument("--left", required=True, type=Path)
    diff.add_argument("--right", required=True, type=Path)
    diff.add_argument("--rules", required=True, type=Path)
    fence = sub.add_parser("fence-write")
    for name in ("source-state", "target-state", "source-app", "target-app", "source-snapshot", "target-snapshot"):
        fence.add_argument("--" + name, required=True, type=Path)
    for name in ("source-url", "target-url", "method", "path"):
        fence.add_argument("--" + name, required=True)
    args = parser.parse_args()
    try:
        if args.mode == "compare":
            rules = json.loads(args.rules.read_text())
            result = compare_http(response(args.left), response(args.right), rules)
        else:
            result = authorize_write(args.source_state, args.target_state, args.source_app,
                                     args.target_app, args.source_url, args.target_url,
                                     args.method, args.path, args.source_snapshot, args.target_snapshot)
    except (ComparisonError, FenceError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": type(exc).__name__}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("equal", True) else 1


if __name__ == "__main__":
    sys.exit(main())
