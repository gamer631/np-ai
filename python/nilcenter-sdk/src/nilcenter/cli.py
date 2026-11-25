"""Command-line interface for NILcenter discovery and local research records."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from nilcenter import NIL, ExperimentStore
from nilcenter.manifest import ToolManifest


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nilcenter",
        description="Discover NILcenter laboratories and manage local experiment metadata.",
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

    experiments = commands.add_parser("experiments", help="Manage local experiment records")
    experiments.add_argument(
        "--store",
        type=Path,
        default=Path.home() / ".local" / "share" / "nilcenter" / "experiments.json",
        help="Path to the local experiment JSON store",
    )
    experiment_commands = experiments.add_subparsers(
        dest="experiment_command", required=True
    )
    create = experiment_commands.add_parser("create", help="Create a draft experiment")
    create.add_argument("laboratory")
    create.add_argument("name")
    create.add_argument("--hypothesis", default="")
    create.add_argument("--tag", action="append", default=[])
    experiment_commands.add_parser("list", help="List saved experiments")
    status = experiment_commands.add_parser("status", help="Update an experiment lifecycle status")
    status.add_argument("experiment_id")
    status.add_argument("value", choices=("draft", "planned", "running", "succeeded", "failed", "cancelled"))
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
                raise TypeError("Manifest root must be a JSON object")
            manifest = ToolManifest.from_mapping(payload)
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            print(f"Manifest validation failed: {exc}", file=sys.stderr)
            return 2
        print(f"Valid manifest: {manifest.id} ({manifest.version})")
        return 0

    if args.command == "experiments":
        store = ExperimentStore(args.store)
        if args.experiment_command == "create":
            try:
                laboratory = nil.labs.get(args.laboratory)
                experiment = store.create(
                    args.name,
                    laboratory.id,
                    hypothesis=args.hypothesis,
                    tags=tuple(args.tag),
                )
            except (KeyError, OSError, TypeError, ValueError) as exc:
                print(f"Experiment creation failed: {exc}", file=sys.stderr)
                return 2
            print(f"Created {experiment.id}: {experiment.name} [{experiment.status}]")
            return 0
        if args.experiment_command == "list":
            for experiment in store.list():
                print(
                    f"{experiment.id}  {experiment.laboratory:20} "
                    f"{experiment.status:10} {experiment.name}"
                )
            return 0
        if args.experiment_command == "status":
            try:
                experiment = store.set_status(args.experiment_id, args.value)
            except (KeyError, OSError, ValueError) as exc:
                print(f"Experiment status update failed: {exc}", file=sys.stderr)
                return 2
            print(f"Updated {experiment.id}: {experiment.status}")
            return 0

    parser.error("Unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
