"""Data structures describing what an organize run did (or would do)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class Move:
    """A single file move."""

    source: Path
    destination: Path
    category: str

    @property
    def renamed(self) -> bool:
        """True if the file name had to change to avoid a conflict."""
        return self.source.name != self.destination.name


@dataclass(frozen=True)
class SkippedFile:
    """A file that was left in place, with the reason."""

    path: Path
    reason: str


@dataclass(frozen=True)
class FileError:
    """A file that could not be moved."""

    path: Path
    message: str


@dataclass
class OrganizationResult:
    """Outcome of :func:`organize` / :func:`preview`.

    When ``dry_run`` is true nothing was changed: ``moves`` and
    ``created_directories`` describe what *would* happen.
    """

    root: Path
    dry_run: bool = False
    moves: List[Move] = field(default_factory=list)
    skipped: List[SkippedFile] = field(default_factory=list)
    errors: List[FileError] = field(default_factory=list)
    created_directories: List[Path] = field(default_factory=list)

    @property
    def files_moved(self) -> int:
        """Number of files moved (planned moves in a dry run)."""
        return len(self.moves)

    @property
    def files_skipped(self) -> int:
        """Number of files intentionally left in place."""
        return len(self.skipped)

    @property
    def files_failed(self) -> int:
        """Number of files that could not be moved because of an error."""
        return len(self.errors)
