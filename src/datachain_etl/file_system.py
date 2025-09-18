"""Helpers for working with the filesystem."""

from __future__ import annotations

from pathlib import Path
from typing import Optional


class MissingSourceFileError(FileNotFoundError):
    """Raised when the expected source GSM file cannot be located."""


def resolve_file_path(source_root: Path, file_path: str) -> Path:
    """Resolve a database ``file_path`` into an absolute path on disk."""

    candidate = source_root.joinpath(file_path.lstrip("/"))
    if candidate.exists():
        return candidate

    gsm_candidate = candidate.with_suffix(".gsm")
    if gsm_candidate.exists():
        return gsm_candidate

    raise MissingSourceFileError(f"Unable to locate GSM file for {file_path}")


def ensure_directory(path: Path) -> None:
    """Create the parent directory for ``path`` if necessary."""

    path.parent.mkdir(parents=True, exist_ok=True)


def archive_source_file(source_path: Path, archive_root: Optional[Path]) -> None:
    """Move the processed file into an archive directory if configured."""

    if not archive_root:
        return
    archive_path = archive_root / source_path.name
    ensure_directory(archive_path)
    source_path.rename(archive_path)
