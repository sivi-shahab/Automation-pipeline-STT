"""Audio conversion helpers leveraging ffmpeg."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .file_system import ensure_directory


class AudioConversionError(RuntimeError):
    """Raised when ffmpeg fails to convert the GSM file."""


def convert_gsm_to_wav(
    source_path: Path,
    destination_path: Path,
    *,
    ffmpeg_binary: str = "ffmpeg",
) -> None:
    """Convert a GSM audio file into a WAV file using ffmpeg."""

    ensure_directory(destination_path)
    command = [
        ffmpeg_binary,
        "-y",  # overwrite existing files
        "-i",
        str(source_path),
        "-ac",
        "1",
        "-ar",
        "8000",
        str(destination_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise AudioConversionError(
            "ffmpeg failed to convert %s to WAV: %s" % (source_path, result.stderr.strip())
        )
