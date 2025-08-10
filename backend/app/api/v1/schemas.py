from pydantic import BaseModel
from typing import List, Optional

class ChunkInfo(BaseModel):
    id: str
    size: int

class IngestionUploadResponse(BaseModel):
    status: str           # "ok" | "error"
    file_id: str
    chunks_indexed: int
    chunks: List[ChunkInfo]

# Modèle Pydantic pour valider le corps de la requête
class SimpleFileRequest(BaseModel):
    extracted_serie: str
    file_name: str
    file_ext: str

class CustomFileRequest(BaseModel):
    extracted_serie: str
    file_name: str
    file_ext: str
    options: Optional[List[str]] = None

class SaveChunksRequest(BaseModel):
    chunks: List[str]
    base_filename: Optional[str] = "chunk"

class SaveChunksResponse(BaseModel):
    version_path: str
    version: str
    paths: List[dict]

class GetChunksByVersionResponse(BaseModel):
    chunks: List[str]


# ===============================================

class EmbedderConfigResponse(BaseModel):
    supported_embedders: list
    active_embedder: str

class EmbedderSelect(BaseModel):
    provider: str
    params: dict | None = None

class SeriesIndexRequest(BaseModel):
    series: str               # ex : "110625-022017" (suffixe sans le mot chunks_)
    embedder: str | None = None  # sinon ← config persistée
    version: str | None = None

class KGRequest(BaseModel):
    series: str  # ex: "110625-022017"