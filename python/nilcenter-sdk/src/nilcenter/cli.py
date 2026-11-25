"""Command-line interface for NILcenter laboratory discovery."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from nilcenter import NIL
from nilcenter.manifest import ToolManifest


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nilcenter",
        description="Discover NILcenter.ai research laboratories and validate tool manifests.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    labs = commands.add_parser("labs", help="Discover research laboratories")
    lab_commands = labs.add_subparsers(dest="lab_command", required=True)
    lab_commands.add_parser("list", help="List all laboratories")
    search = lab_commands.add_parser("search", help="Search laboratories")
    search.add_argument("query")

    tools = commands.add_parser("tools", help="Inspect tool metadata")
    tool_commands = tools.add_subparsers(dest="tool_command", required=True)
    listing = tool_commands.add_parser("list", help="List registered tool descriptors")
    listing.add_argument("--lab", dest="laboratory")

    validate = tool_commands.add_parser("validate", help="Validate a JSON tool manifest")
    validate.add_argument("manifest", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the NILcenter CLI and return a process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    nil = NIL()

    if args.command == "labs" and args.lab_command == "list":
        for lab in nil.labs.list():
            print(f"{lab.id:24} {lab.name}")
        return 0

    if args.command == "labs" and args.lab_command == "search":
        matches = nil.labs.search(args.query)
        for lab in matches:
            print(f"{lab.id:24} {lab.name}")
        return 0 if matches else 1

    if args.command == "tools" and args.tool_command == "list":
        for tool in nil.tools_registry.list(args.laboratory):
            print(f"{tool.id} ({tool.version}) — {tool.name}")
        return 0

    if args.command == "tools" and args.tool_command == "validate":
        try:
            payload = json.loads(args.manifest.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("Manifest root must be a JSON object")
            manifest = ToolManifest.from_mapping(payload)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"Manifest validation failed: {exc}", file=sys.stderr)
            return 2
        print(f"Valid manifest: {manifest.id} ({manifest.version})")
        return 0

    parser.error("Unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
