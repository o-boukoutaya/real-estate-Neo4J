# corpus/utils.py
from __future__ import annotations
import hashlib, os, re, shutil, time, uuid
from pathlib import Path
from typing import Iterable

ALLOWED_EXTS = {".pdf", ".txt", ".csv", ".docx", ".xlsx", ".xls"}

# Ensure a directory exists
def ensure_dir(path: os.PathLike | str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

# Get the current timestamp as a series ID
def now_series_id() -> str:
    # ex: 20250817-142350-3f2a6c
    return f"{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"

# Regular expression for safe filenames
_name_rx = re.compile(r"[^A-Za-z0-9._-]+")

# Sanitize a filename by replacing unsafe characters
def safe_filename(name: str) -> str:
    base = os.path.basename(name)
    return _name_rx.sub("_", base)

# Compute the SHA-256 hash of a file
def file_sha256(path: os.PathLike | str, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()

# Check if a file has an allowed extension
def is_allowed(name: str) -> bool:
    return Path(name).suffix.lower() in ALLOWED_EXTS

# Write bytes to a file atomically - https://stackoverflow.com/a/720171
def atomic_write_bytes(dst: os.PathLike | str, data: bytes) -> None:
    dst = Path(dst)
    tmp = dst.with_suffix(dst.suffix + f".tmp-{uuid.uuid4().hex}")
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, dst)

# Write text to a file atomically
def atomic_write_text(dst: os.PathLike | str, data: str, encoding="utf-8") -> None:
    atomic_write_bytes(dst, data.encode(encoding))

# Generate a unique path in a directory by appending a number if needed
def unique_path(dir_: os.PathLike | str, filename: str) -> Path:
    dirp = Path(dir_)
    stem, ext = os.path.splitext(filename)
    i, candidate = 1, dirp / filename
    while candidate.exists():
        candidate = dirp / f"{stem}({i}){ext}"
        i += 1
    return candidate

# Move a file to a unique path in the destination directory
def move_many(paths: Iterable[Path], dst_dir: os.PathLike | str) -> list[Path]:
    out = []
    dst_dir = ensure_dir(dst_dir)
    for p in paths:
        target = unique_path(dst_dir, p.name)
        shutil.move(str(p), str(target))
        out.append(target)
    return out
