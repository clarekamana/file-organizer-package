"""Exceptions raised by file_organizer."""


class FileOrganizerError(Exception):
    """Base class for all errors raised by this package."""


class InvalidPathError(FileOrganizerError):
    """The path to organize does not exist or is not a readable directory."""


class InvalidOptionError(FileOrganizerError, ValueError):
    """An option such as ``conflict`` was given an unsupported value."""
