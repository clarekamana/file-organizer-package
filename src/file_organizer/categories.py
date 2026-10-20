"""Extension -> category folder mappings.

All knowledge about which extension belongs where lives in this module.
To add a default category, edit ``_CATEGORY_EXTENSIONS``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Mapping, Optional

#: Folder used for files whose extension is unknown or missing.
FALLBACK_CATEGORY = "Other"

#: Category folder -> space-separated extensions it contains.
_CATEGORY_EXTENSIONS: Dict[str, str] = {
    "Images": ".jpg .jpeg .png .gif .webp .svg .bmp .tiff",
    "Documents": ".pdf .doc .docx .txt .rtf .odt",
    "Spreadsheets": ".csv .xls .xlsx .ods",
    "Presentations": ".ppt .pptx .odp",
    "Music": ".mp3 .wav .flac .ogg .m4a",
    "Videos": ".mp4 .mkv .mov .avi .webm",
    "Archives": ".zip .rar .7z .tar .gz .bz2",
    "Programs": ".exe .msi .apk .deb .rpm",
    "Code": (
        ".py .js .ts .jsx .tsx .java .c .cpp .h .cs .go .rs .php .rb "
        ".swift .kt .html .css .sql .sh .ps1"
    ),
    "Fonts": ".ttf .otf .woff .woff2",
}


def normalize_extension(extension: str) -> str:
    """Return ``extension`` lower-cased with a single leading dot.

    >>> normalize_extension("JPG")
    '.jpg'
    """
    cleaned = extension.strip().lower().lstrip(".")
    if not cleaned:
        raise ValueError("extension must not be empty")
    return "." + cleaned


def default_categories() -> Dict[str, str]:
    """Return a fresh copy of the default extension -> category mapping."""
    return {
        normalize_extension(ext): category
        for category, extensions in _CATEGORY_EXTENSIONS.items()
        for ext in extensions.split()
    }


def build_category_map(custom: Optional[Mapping[str, str]] = None) -> Dict[str, str]:
    """Merge ``custom`` mappings over the defaults.

    Custom entries are *added* to the defaults; if an extension appears in
    both, the custom entry wins. Extensions are case-insensitive and the
    leading dot is optional. Folder names must be plain names, not paths.
    """
    mapping = default_categories()
    for extension, category in (custom or {}).items():
        if not category or category in (".", "..") or Path(category).name != category:
            raise ValueError(
                f"invalid category folder name {category!r}: "
                "it must be a plain folder name, not a path"
            )
        mapping[normalize_extension(extension)] = category
    return mapping


def category_for(path: Path, mapping: Mapping[str, str]) -> str:
    """Return the category folder for ``path`` (case-insensitive extension)."""
    return mapping.get(path.suffix.lower(), FALLBACK_CATEGORY)
