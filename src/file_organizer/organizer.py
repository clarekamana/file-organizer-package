"""Core organizing logic."""

from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Set

from .categories import FALLBACK_CATEGORY, build_category_map, category_for
from .exceptions import InvalidOptionError, InvalidPathError
from .models import FileError, Move, OrganizationResult, SkippedFile

CONFLICT_STRATEGIES = ("rename", "skip")


def is_hidden(path: Path) -> bool:
    """True for dot-files, and for files with the Windows 'hidden' attribute."""
    if path.name.startswith("."):
        return True
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_HIDDEN", 0))


class Organizer:
    """Organizes a directory's files into category folders.

    Args:
        categories: Optional extra ``{extension: folder}`` mappings merged
            over the defaults (custom entries win on conflict).
        include_hidden: Also move hidden files. Default ``False``.
        conflict: ``"rename"`` (default) keeps both files by adding ``_1``,
            ``_2``... to the new name; ``"skip"`` leaves the file in place.
        recursive: Also organize files in sub-directories. Default ``False``.
            Files end up in category folders directly under the root;
            existing category folders under the root are never re-processed.
    """

    def __init__(
        self,
        categories: Optional[Mapping[str, str]] = None,
        *,
        include_hidden: bool = False,
        conflict: str = "rename",
        recursive: bool = False,
    ) -> None:
        if conflict not in CONFLICT_STRATEGIES:
            raise InvalidOptionError(
                f"conflict must be one of {CONFLICT_STRATEGIES}, got {conflict!r}"
            )
        self.category_map: Dict[str, str] = build_category_map(categories)
        self.include_hidden = include_hidden
        self.conflict = conflict
        self.recursive = recursive

    # -- public API -------------------------------------------------------

    def preview(self, path) -> OrganizationResult:
        """Return what :meth:`organize` would do, without changing anything."""
        return self.organize(path, dry_run=True)

    def organize(self, path, *, dry_run: bool = False) -> OrganizationResult:
        """Organize ``path`` and return an :class:`OrganizationResult`.

        Raises:
            InvalidPathError: if ``path`` is not an accessible directory.
        """
        root = self._resolve_root(path)
        result = OrganizationResult(root=root, dry_run=dry_run)
        reserved: Set[Path] = set()  # destinations already claimed this run

        for source in self._collect_files(root, result):
            self._handle_file(root, source, result, reserved, dry_run)
        return result

    # -- discovery --------------------------------------------------------

    @staticmethod
    def _resolve_root(path) -> Path:
        try:
            root = Path(path).expanduser().resolve()
        except (OSError, RuntimeError, TypeError) as exc:
            raise InvalidPathError(f"invalid path {path!r}: {exc}") from exc
        if not root.exists():
            raise InvalidPathError(f"path does not exist: {root}")
        if not root.is_dir():
            raise InvalidPathError(f"path is not a directory: {root}")
        if not os.access(root, os.R_OK | os.X_OK):
            raise InvalidPathError(f"directory is not readable: {root}")
        return root

    def _collect_files(self, root: Path, result: OrganizationResult) -> List[Path]:
        """Snapshot candidate files *before* anything is moved.

        Taking the full list up front guarantees a file is never processed
        twice, even in recursive mode. Real directories are never included;
        symlinks are included so they can be reported as skipped.
        """
        try:
            if self.recursive:
                return self._walk(root, result)
            return sorted(p for p in root.iterdir() if p.is_symlink() or not p.is_dir())
        except OSError as exc:
            raise InvalidPathError(f"cannot read directory {root}: {exc}") from exc

    def _walk(self, root: Path, result: OrganizationResult) -> List[Path]:
        category_folders = set(self.category_map.values()) | {FALLBACK_CATEGORY}
        files: List[Path] = []

        def on_error(exc: OSError) -> None:
            result.errors.append(FileError(Path(exc.filename or root), str(exc)))

        # os.walk never follows directory symlinks (followlinks=False).
        for dirpath, dirnames, filenames in os.walk(root, onerror=on_error):
            current = Path(dirpath)
            if current == root:
                # Already-organized category folders are left alone.
                dirnames[:] = [d for d in dirnames if d not in category_folders]
            if not self.include_hidden:
                dirnames[:] = [d for d in dirnames if not is_hidden(current / d)]
            dirnames.sort()
            files.extend(current / name for name in sorted(filenames))
        return files

    # -- per-file handling ------------------------------------------------

    def _handle_file(
        self,
        root: Path,
        source: Path,
        result: OrganizationResult,
        reserved: Set[Path],
        dry_run: bool,
    ) -> None:
        if source.is_symlink():
            result.skipped.append(SkippedFile(source, "symlink"))
            return
        if not self.include_hidden and is_hidden(source):
            result.skipped.append(SkippedFile(source, "hidden file"))
            return

        category = category_for(source, self.category_map)
        target_dir = root / category
        if target_dir.exists() and not target_dir.is_dir():
            result.errors.append(
                FileError(source, f"cannot use {target_dir}: it exists and is not a directory")
            )
            return

        destination = self._choose_destination(source, target_dir, reserved)
        if destination is None:
            result.skipped.append(
                SkippedFile(source, f"a file with this name already exists in {category}")
            )
            return

        needs_dir = not target_dir.exists() and target_dir not in result.created_directories
        if dry_run:
            reserved.add(destination)
            if needs_dir:
                result.created_directories.append(target_dir)
            result.moves.append(Move(source, destination, category))
            return

        try:
            if needs_dir:
                target_dir.mkdir()
                result.created_directories.append(target_dir)
            shutil.move(str(source), str(destination))
        except FileNotFoundError:
            result.errors.append(FileError(source, "file disappeared before it could be moved"))
        except OSError as exc:
            result.errors.append(FileError(source, f"{type(exc).__name__}: {exc}"))
        else:
            reserved.add(destination)
            result.moves.append(Move(source, destination, category))

    def _choose_destination(
        self, source: Path, target_dir: Path, reserved: Set[Path]
    ) -> Optional[Path]:
        """Pick a free destination path, or ``None`` if the file must be skipped."""

        def taken(candidate: Path) -> bool:
            return candidate in reserved or os.path.lexists(candidate)

        candidate = target_dir / source.name
        if not taken(candidate):
            return candidate
        if self.conflict == "skip":
            return None
        counter = 1
        while True:
            candidate = target_dir / f"{source.stem}_{counter}{source.suffix}"
            if not taken(candidate):
                return candidate
            counter += 1


def organize(
    path,
    *,
    dry_run: bool = False,
    include_hidden: bool = False,
    conflict: str = "rename",
    recursive: bool = False,
    categories: Optional[Mapping[str, str]] = None,
) -> OrganizationResult:
    """Organize the files in ``path`` into category folders.

    See :class:`Organizer` for the meaning of the options. With
    ``dry_run=True`` nothing is changed.
    """
    organizer = Organizer(
        categories,
        include_hidden=include_hidden,
        conflict=conflict,
        recursive=recursive,
    )
    return organizer.organize(path, dry_run=dry_run)


def preview(path, **options) -> OrganizationResult:
    """Return what :func:`organize` would do, without changing anything."""
    options.pop("dry_run", None)
    return organize(path, dry_run=True, **options)
