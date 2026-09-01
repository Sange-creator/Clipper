"""Hashing utilities for content identification and caching."""

import hashlib
from pathlib import Path


def compute_file_hash(file_path: Path | str, chunk_size: int = 65536) -> str:
    """Compute SHA-256 hash of a file efficiently without loading entirely into memory."""
    sha256 = hashlib.sha256()
    path = Path(file_path)
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_string_hash(content: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
