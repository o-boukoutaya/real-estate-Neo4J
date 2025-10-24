# corpus/router.py
from __future__ import annotations
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from typing import List
from corpus.storage import FileStorage
from corpus.importer import Importer
from corpus.extractor import TextExtractor
from corpus.models import (
    ImportResult, ExtractRequest, ExtractResult,
    MoveFilesRequest, MergeSeriesRequest, DeleteSeriesRequest, SeriesInfo
)
import os

router = APIRouter(prefix="/corpus", tags=["corpus"])

def get_storage() -> FileStorage:
    return FileStorage(root=os.getenv("CORPUS_ROOT", "data/corpus"))

@router.post("/import", response_model=ImportResult)
async def import_files(
    files: List[UploadFile] = File(...),
    series_id: str | None = None,
    storage: FileStorage = Depends(get_storage),
):
    imp = Importer(storage)
    return await imp.import_uploads(files, series_id)

@router.get("/series", response_model=List[str])
def list_series(storage: FileStorage = Depends(get_storage)):
    return storage.list_series()

@router.delete("/series", response_model=dict)
def delete_series(req: DeleteSeriesRequest, storage: FileStorage = Depends(get_storage)):
    if not storage.series_exists(req.series_id):
        raise HTTPException(404, "series not found")
    storage.delete_series(req.series_id)
    return {"ok": True}

@router.post("/extract", response_model=ExtractResult)
def extract_texts(req: ExtractRequest, storage: FileStorage = Depends(get_storage)):
    if not storage.series_exists(req.series_id):
        raise HTTPException(404, "series not found")
    ex = TextExtractor(storage)
    return ex.extract_series(req)

@router.post("/move", response_model=dict)
def move_files(req: MoveFilesRequest, storage: FileStorage = Depends(get_storage)):
    if not (storage.series_exists(req.src_series_id) and storage.series_exists(req.dst_series_id)):
        raise HTTPException(404, "series not found")
    moved = storage.move_files(req.src_series_id, req.dst_series_id, req.filenames)
    return {"moved": [p.name for p in moved]}

@router.post("/merge", response_model=dict)
def merge_series(req: MergeSeriesRequest, storage: FileStorage = Depends(get_storage)):
    if not storage.series_exists(req.target_series_id):
        raise HTTPException(404, "target series not found")
    merged = storage.merge_series(req.target_series_id, req.from_series_ids)
    return {"merged": [p.name for p in merged]}