"""file-sorter-cli: safely sort messy directories into categorized folders."""

from .categories import default_categories
from .exceptions import FileOrganizerError, InvalidOptionError, InvalidPathError
from .models import FileError, Move, OrganizationResult, SkippedFile
from .organizer import Organizer, organize, preview

__version__ = "0.1.0"

__all__ = [
    "FileError",
    "FileOrganizerError",
    "InvalidOptionError",
    "InvalidPathError",
    "Move",
    "OrganizationResult",
    "Organizer",
    "SkippedFile",
    "__version__",
    "default_categories",
    "organize",
    "preview",
]
