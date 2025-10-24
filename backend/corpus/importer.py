# corpus/importer.py
from __future__ import annotations
import os
from pathlib import Path
from typing import Iterable, List, Tuple
from fastapi import UploadFile
from .storage import FileStorage
from .models import ImportResult, ImportedFile

# File import service
class Importer:
    """
    Import service: only manages files and series.
    - Validates extensions
    - Saves multiple files at once (without collisions)
    - Deduplicates (based on SHA-256) within the same series
    - Does not touch extraction (extractor.py takes care of that)
    """
    # Initialization : define the storage
    def __init__(self, storage: FileStorage):
        self.storage = storage

    # Import files : handle file uploads
    async def import_uploads(self, files: Iterable[UploadFile], series_id: str | None = None) -> ImportResult:
        sid = series_id or self.storage.create_series()
        seen_hashes: set[str] = set()
        results: List[ImportedFile] = []
        skipped: List[str] = []

        # reconstruire set des hachés déjà présents dans la série
        for p in self.storage.list_raw(sid):
            try:
                from .utils import file_sha256
                seen_hashes.add(file_sha256(p))
            except Exception:
                pass

        for uf in files:
            name = uf.filename or "file"
            try:
                data = await uf.read()
            finally:
                await uf.close()
            # validation extension
            from .utils import is_allowed, safe_filename, file_sha256, unique_path
            if not is_allowed(name):
                skipped.append(f"{name}: unsupported")
                continue
            # dédup simple
            tmp_path = unique_path(self.storage.raw_dir(sid), safe_filename(name) + ".tmp")
            tmp_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path.write_bytes(data)
            h = file_sha256(tmp_path)
            if h in seen_hashes:
                skipped.append(f"{name}: duplicate")
                tmp_path.unlink(missing_ok=True)
                continue
            seen_hashes.add(h)
            # commit vers nom final
            final_name = safe_filename(name)
            dst = unique_path(self.storage.raw_dir(sid), final_name)
            os.replace(tmp_path, dst)
            results.append(ImportedFile(filename=dst.name, size=dst.stat().st_size, sha256=h, path=str(dst)))

        return ImportResult(series_id=sid, files=results, skipped=skipped)
