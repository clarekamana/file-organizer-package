# file-sorter-cli

A lightweight Python package for automatically organizing files into categorized directories.
No dependencies, no configuration needed.

```text
Downloads/                       Downloads/
├── photo.jpg                    ├── Images/       photo.jpg, vacation.png
├── vacation.png                 ├── Documents/    report.pdf, homework.docx
├── report.pdf          ──►      ├── Music/        song.mp3
├── homework.docx                ├── Videos/       movie.mp4
├── song.mp3                     ├── Programs/     setup.exe
├── movie.mp4                    ├── Spreadsheets/ data.csv
├── setup.exe                    └── Archives/     archive.zip
├── data.csv
└── archive.zip
```

Requires **Python 3.9+**.

## Installation

```bash
pip install file-sorter-cli
```

The project is installed as `file-sorter-cli`, imported as `file_organizer`
(`from file_organizer import organize`), and run as the `file-sorter` command.

For local development:

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from file_organizer import organize

result = organize("~/Downloads")

print(f"Moved {result.files_moved} files")
```

### Preview

Nothing is created or moved in a dry run; the result describes what *would* happen.

```python
from file_organizer import organize, preview

result = organize("~/Downloads", dry_run=True)   # same as preview("~/Downloads")
for move in result.moves:
    print(move.source.name, "->", move.category)
```

### The result object

| Attribute | Meaning |
|---|---|
| `files_moved` | number of files moved (planned, in a dry run) |
| `files_skipped` / `skipped` | files left in place, each with a `reason` |
| `files_failed` / `errors` | files that could not be moved (`path`, `message`) |
| `created_directories` | category folders created (or that would be) |
| `moves` | list of `Move(source, destination, category)` |
| `dry_run` | whether this was a dry run |

One bad file never aborts the run: permission errors, files vanishing mid-run, etc.
are recorded in `result.errors`.

## CLI

```bash
file-sorter organize ~/Downloads
file-sorter organize ~/Downloads --dry-run
file-sorter preview ~/Downloads
file-sorter organize ~/Downloads --conflict skip --include-hidden --recursive
file-sorter --version
file-sorter --help
```

Example output:

```text
File Organizer
────────────────────────────

DRY RUN — No files will be moved

photo.jpg   → Images/
report.pdf  → Documents/
song.mp3    → Music/
setup.exe   → Programs/

4 files would be moved.
```

Exit codes: `0` success, `1` some files failed, `2` invalid path or usage.

## Supported categories

| Folder | Extensions |
|---|---|
| `Images` | jpg jpeg png gif webp svg bmp tiff |
| `Documents` | pdf doc docx txt rtf odt |
| `Spreadsheets` | csv xls xlsx ods |
| `Presentations` | ppt pptx odp |
| `Music` | mp3 wav flac ogg m4a |
| `Videos` | mp4 mkv mov avi webm |
| `Archives` | zip rar 7z tar gz bz2 |
| `Programs` | exe msi apk deb rpm |
| `Code` | py js ts jsx tsx java c cpp h cs go rs php rb swift kt html css sql sh ps1 |
| `Fonts` | ttf otf woff woff2 |
| `Other` | everything else, including files with no extension |

Extensions are case-insensitive (`photo.JPG` and `photo.jpg` behave the same).

## Custom categories

Custom mappings are **merged into** the defaults. If an extension is in both, **your
mapping wins**. The leading dot is optional and case is ignored.

```python
from file_organizer import Organizer

organizer = Organizer(categories={".blend": "3D", ".fbx": "3D", ".txt": "Notes"})
organizer.organize("~/Downloads")
```

`organize(path, categories={...})` accepts the same mapping. Folder names must be plain
names, not paths.

## Conflict handling

Existing files are **never overwritten**.

- `conflict="rename"` (default): the incoming file gets a numeric suffix:
  `Images/photo.jpg` exists → `Images/photo_1.jpg`, then `photo_2.jpg`, …
- `conflict="skip"`: the incoming file stays where it is and is reported in `result.skipped`.

## Recursive mode

Off by default. With `recursive=True` (CLI: `--recursive`), files in sub-folders are
organized too and moved into category folders directly under the root.

```python
organize("~/Downloads", recursive=True)
```

Every file is collected *before* anything is moved, so no file is processed twice.
Category folders already in the root (`Images/`, …) and hidden folders (unless
`include_hidden` is set) are not searched, so running it a second time changes nothing.

## Safety behavior

- Only **files** are moved. Directories are never moved, renamed, or deleted.
- Nothing is ever deleted and file contents are never modified.
- Existing files are never overwritten (see conflict handling above).
- **Hidden files** (names starting with `.`, or with the Windows hidden attribute) are
  skipped unless `include_hidden=True`. This protects files like `.bashrc` or `.env`.
- **Symlinks** are always skipped and reported, never followed.
- Do not point it at system or application directories (for example a project root or
  `C:\Windows`). Run with `--dry-run` first.

## Development and testing

```bash
pip install -e ".[dev]"
pytest
```

## Project structure

```text
file-sorter-cli/
├── pyproject.toml
├── README.md  LICENSE  CHANGELOG.md
├── src/file_organizer/
│   ├── __init__.py      public API
│   ├── organizer.py     Organizer, organize(), preview()
│   ├── categories.py    extension -> folder mappings
│   ├── models.py        result dataclasses
│   ├── exceptions.py
│   ├── cli.py           argparse command line
│   └── __main__.py      python -m file_organizer
└── tests/
```

## License

MIT. The full text is in the `LICENSE` file shipped with the package.
