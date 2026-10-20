"""Command-line interface."""

from __future__ import annotations

import utils.session
import argparse
import sys
from typing import List, Optional

from . import __version__
from .exceptions import FileOrganizerError
from .models import OrganizationResult
from .organizer import Organizer

RULE = "─" * 28


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="file-sorter",
        description="Organize files into folders (Images, Documents, ...) by type.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", metavar="{organize,preview}")

    organize_cmd = subparsers.add_parser("organize", help="move files into category folders")
    organize_cmd.add_argument("path", help="directory to organize")
    organize_cmd.add_argument(
        "--dry-run", action="store_true", help="show what would happen without changing anything"
    )
    _add_common_options(organize_cmd)

    preview_cmd = subparsers.add_parser("preview", help="same as organize --dry-run")
    preview_cmd.add_argument("path", help="directory to preview")
    _add_common_options(preview_cmd)
    return parser


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--include-hidden", action="store_true", help="also move hidden files")
    parser.add_argument(
        "--conflict",
        choices=("rename", "skip"),
        default="rename",
        help="when the target file exists: rename the new file (default) or skip it",
    )
    parser.add_argument(
        "--recursive", action="store_true", help="also organize files in sub-directories"
    )


def format_report(result: OrganizationResult) -> str:
    """Render a result as human-readable text."""
    lines = ["File Organizer", RULE, ""]
    if result.dry_run:
        lines += ["DRY RUN — No files will be moved", ""]

    rows = []
    for move in result.moves:
        shown = str(move.source.relative_to(result.root))
        target = move.category + "/" + (move.destination.name if move.renamed else "")
        rows.append((shown, target))
    width = max((len(shown) for shown, _ in rows), default=0)
    lines += [f"{shown.ljust(width)}  → {target}" for shown, target in rows]
    if rows:
        lines.append("")

    verb = "would be moved" if result.dry_run else "moved"
    lines.append(f"{result.files_moved} file{'s' if result.files_moved != 1 else ''} {verb}.")
    if result.skipped:
        lines.append(f"{result.files_skipped} skipped:")
        lines += [
            f"  {item.path.relative_to(result.root)} ({item.reason})" for item in result.skipped
        ]
    if result.errors:
        lines.append(f"{result.files_failed} failed:")
        lines += [f"  {err.path} — {err.message}" for err in result.errors]
    return "\n".join(lines)


def _configure_output() -> None:
    """Never crash on consoles that can't display box/arrow characters."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(errors="replace")


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point. Returns the process exit code."""
    _configure_output()
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    dry_run = args.command == "preview" or args.dry_run
    try:
        organizer = Organizer(
            include_hidden=args.include_hidden,
            conflict=args.conflict,
            recursive=args.recursive,
        )
        result = organizer.organize(args.path, dry_run=dry_run)
    except FileOrganizerError as exc:
        print(f"file-sorter: error: {exc}", file=sys.stderr)
        return 2

    print(format_report(result))
    return 1 if result.errors else 0
