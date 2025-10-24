# corpus/models.py
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

# Information about a series of files
class SeriesInfo(BaseModel):
    id: str
    created_at: str
    file_count: int
    bytes_total: int

# Information about an imported file
class ImportedFile(BaseModel):
    filename: str
    size: int
    sha256: str
    path: str

# Request to import files into a series
class ImportResult(BaseModel):
    series_id: str
    files: List[ImportedFile]
    skipped: List[str] = Field(default_factory=list)

# Request to extract text from files in a series
class ExtractRequest(BaseModel):
    series_id: str
    ocr: bool = True                 # fallback OCR if needed
    ocr_langs: str = "ara+fra"       # FR/AR by default
    min_text_chars: int = 50         # threshold to decide OCR on a text-poor page

# Response after extracting text from files
class ExtractResultItem(BaseModel):
    filename: str
    text_path: str
    char_count: int
    pages: Optional[int] = None
    used_ocr_pages: int = 0

# Response after extracting text from files
class ExtractResult(BaseModel):
    series_id: str
    items: List[ExtractResultItem]

# Request to move files between series
class MoveFilesRequest(BaseModel):
    src_series_id: str
    dst_series_id: str
    filenames: List[str]

# Request to merge multiple series into one
class MergeSeriesRequest(BaseModel):
    target_series_id: str
    from_series_ids: List[str]

# Request to delete a series
class DeleteSeriesRequest(BaseModel):
    series_id: str
