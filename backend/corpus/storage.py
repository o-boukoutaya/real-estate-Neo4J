# corpus/storage.py
from __future__ import annotations
import json, os, shutil, time
from pathlib import Path
from typing import Optional, List, Dict
from .utils import ensure_dir, safe_filename, file_sha256, is_allowed, unique_path, now_series_id

# Manage file storage for the corpus
class FileStorage:
    """
    Manages the storage area for the corpus.
    Directory structure:
      data/corpus/
        └─ <series_id>/
           ├─ raw/   (originals)
           ├─ text/  (extractions)
           └─ meta.json
    """
    # Initialization : define the root directory
    def __init__(self, root: str = "data/corpus"):
        self.root = Path(root)
        ensure_dir(self.root)

    # ---- series ----
    # to create a new series
    def create_series(self, series_id: Optional[str] = None) -> str:
        sid = series_id or now_series_id()
        serie = self.root / sid
        ensure_dir(serie / "raw")
        ensure_dir(serie / "text")
        meta = {"id": sid, "created_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        self._write_meta(sid, meta)
        return sid

    # List all series
    def list_series(self) -> List[str]:
        return sorted([p.name for p in self.root.iterdir() if p.is_dir()])

    # Check if a series exists
    def series_exists(self, series_id: str) -> bool:
        return (self.root / series_id).is_dir()

    # Delete a series
    def delete_series(self, series_id: str) -> None:
        p = self.root / series_id
        if p.is_dir():
            shutil.rmtree(p)

    # Get the path to the metadata file for a series
    def _meta_path(self, series_id: str) -> Path:
        return self.root / series_id / "meta.json"

    # Write metadata to a series
    def _write_meta(self, series_id: str, data: dict) -> None:
        with open(self._meta_path(series_id), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # Read metadata from a series
    def read_meta(self, series_id: str) -> dict:
        p = self._meta_path(series_id)
        return json.load(open(p, "r", encoding="utf-8")) if p.exists() else {}

    # ---- files ----
    # Save raw file bytes
    def save_bytes(self, series_id: str, filename: str, content: bytes) -> Path:
        if not self.series_exists(series_id):
            raise ValueError(f"series not found: {series_id}")
        if not is_allowed(filename):
            raise ValueError(f"unsupported extension: {filename}")
        filename = safe_filename(filename)
        dst = unique_path(self.root / series_id / "raw", filename)
        with open(dst, "wb") as f:
            f.write(content)
        return dst

    # Get the directory for raw files
    def raw_dir(self, series_id: str) -> Path:
        return self.root / series_id / "raw"

    # Get the directory for text files
    def text_dir(self, series_id: str) -> Path:
        return self.root / series_id / "text"

    # List all raw files in a series
    def list_raw(self, series_id: str) -> List[Path]:
        d = self.raw_dir(series_id)
        return [p for p in d.iterdir() if p.is_file()]

    # Move files between series
    def move_files(self, src_series: str, dst_series: str, filenames: List[str]) -> List[Path]:
        moved = []
        for name in filenames:
            src = self.raw_dir(src_series) / name
            if not src.exists():
                continue
            dst = unique_path(self.raw_dir(dst_series), name)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            moved.append(dst)
        return moved

    # Merge multiple series into one
    def merge_series(self, target_series: str, from_series: List[str]) -> List[Path]:
        out = []
        for sid in from_series:
            for p in self.list_raw(sid):
                dst = unique_path(self.raw_dir(target_series), p.name)
                shutil.move(str(p), str(dst))
                out.append(dst)
        return out