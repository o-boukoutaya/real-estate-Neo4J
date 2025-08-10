# app/api/v1/ingestion.py
import tempfile, os
from ingestion.data_info_manager import DataInfoManager
from ingestion.data_importer import DataImporter
from ingestion.extractor import Extractor
from ingestion.chunker import Chunker
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Optional
from .schemas import (         # met tes Pydantic ici si besoin
    SimpleFileRequest, CustomFileRequest, SaveChunksRequest, SaveChunksResponse, GetChunksByVersionResponse
)
from ingestion.document_loader import DocumentLoader
from pydantic import BaseModel
from embedding.embedding_pipeline import EmbeddingPipeline

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])
# router = APIRouter()

# --------------------------------------------------------------------------
# Routes for Data Info Management
# --------------------------------------------------------------------------

@router.get("/series") # (GET) http://localhost:8050/api/v1/ingestion/series
async def list_series():
    try:
        loader = DataInfoManager()
        return {"series": loader.list_versions(which="provfiles")}
    except Exception as e:
        return {"error": str(e)}

@router.get("/series/{version}") # (GET) http://localhost:8050/api/v1/ingestion/series/{version}
async def get_series_metadata(version: str):
    try:
        # Validation de la version selon la logique existante
        if not version.startswith("serie_"):
            return {"error": "Version invalide. Les versions doivent commencer par 'serie_'."}

        from ingestion.data_info_manager import DataInfoManager
        data_info = DataInfoManager()
        return data_info.version_info(version, which='provfiles')
    except Exception as e:
        return {"error": str(e)}

@router.get("/version/{version}") # (GET) http://localhost:8050/api/v1/ingestion/version/{version}
async def get_version_info(version: str):
    try:
        loader = DataInfoManager()
        return loader.version_info(version, which="provfiles")
    except Exception as e:
        return {"error": str(e)}

# @router.get("/file/{path}") # (GET) http://localhost:8050/api/v1/ingestion/file/{path}
# async def get_file_info(path: str):
#     try:
#         print(f"Received path: {path}")  # Log the received path
#         loader = DataInfoManager()
#         file_info = loader.file_info(path)
#         print(f"File info: {file_info}")  # Log the file info
#         return file_info
#     except Exception as e:
#         print(f"Error: {str(e)}")  # Log the error
#         return {"error": str(e)}

@router.get("/all-versions-info") # (GET) http://localhost:8050/api/v1/ingestion/all-versions-info
async def get_all_versions_info():
    try:
        loader = DataInfoManager()
        return loader.all_versions_info(which="provfiles")
    except Exception as e:
        return {"error": str(e)}

# @router.get("/is-indexed/{version}") # (GET) http://localhost:8050/api/v1/ingestion/is-indexed/{version}
# async def check_version_indexed(version: str):
#     try:
#         loader = DataInfoManager()
#         neo4j_config = {
#             "url": "bolt://localhost:7687",
#             "username": "neo4j",
#             "password": "123456789",
#             "database": "Addoha",
#             "node_label": "Chunk",
#         }
#         return {"is_indexed": loader.is_version_indexed(version, neo4j_config)}
#     except Exception as e:
#         return {"error": str(e)}

# @router.get("/summarize-tree") # (GET) http://localhost:8050/api/v1/ingestion/summarize-tree
# async def summarize_versions_tree():
#     try:
#         loader = DataInfoManager()
#         return loader.summarize_versions_tree()
#     except Exception as e:
#         return {"error": str(e)}

# --------------------------------------------------------------------------
# Routes for Document Loading
# --------------------------------------------------------------------------

@router.delete("/series/{version}") # (DELETE) http://localhost:8050/api/v1/ingestion/series/{version}
async def delete_series(version: str):
    try:
        from ingestion.document_loader import DocumentLoader
        loader = DocumentLoader()
        loader.clear_serie(version)
        return {"message": f"Série {version} supprimée"}
    except Exception as e:
        return {"error": str(e)}

@router.delete("/series") # (DELETE) http://localhost:8050/api/v1/ingestion/series
async def delete_all_series():
    try:
        from ingestion.document_loader import DocumentLoader
        loader = DocumentLoader()
        loader.clear_all_series()
        return {"message": "Toutes les séries supprimées"}
    except Exception as e:
        return {"error": str(e)}

@router.post("/upload-files") # (POST) http://localhost:8050/api/v1/ingestion/upload-files
async def save_uploaded_files(files: List[UploadFile] = File(...), tags: Optional[str] = None, description: Optional[str] = None):
    try:
        loader = DocumentLoader()
        for file in files:
            if file.size == 0:
                return {"error": f"Le fichier {file.filename} est vide."}
        result = loader.save_uploaded_files(files, tags=tags, description=description)
        return result
    except Exception as e:
        return {"error": str(e)}

@router.get("/latest-series") # (GET) http://localhost:8050/api/v1/ingestion/latest-series
async def get_latest_series():
    try:
        loader = DocumentLoader()
        latest_series = loader.get_latest_serie()
        return {"latest_series": latest_series}
    except Exception as e:
        return {"error": str(e)}

# (POST) http://localhost:8050/api/v1/ingestion/upload
# Body: ??
# @router.post("/upload", response_model=IngestionUploadResponse) 
# async def upload(
#     files: List[UploadFile] = File(...),
#     overwrite: bool = False,
# ):
#     # --- logique métier ---
#     file_id = "file_123"
#     indexed_chunks = [ChunkInfo(id="c1", size=2048), ChunkInfo(id="c2", size=1024)]

#     return IngestionUploadResponse(
#         status="ok",
#         file_id=file_id,
#         chunks_indexed=len(indexed_chunks),
#         chunks=indexed_chunks,
#     )



# --------------------------------------------------------------------------
# Routes for Extraction
# --------------------------------------------------------------------------

# Route pour extraire les textes
@router.post("/extract-texts") # (POST) http://localhost:8050/api/v1/ingestion/extract-texts
async def extract_texts(serie_version: Optional[str] = None, files: Optional[List[str]] = None, page_ranges: Optional[dict] = None, txt_version: Optional[str] = None, overwrite: bool = False):
    try:
        extractor = Extractor()
        result = extractor.extract_texts(serie_version=serie_version, files=files, page_ranges=page_ranges, txt_version=txt_version, overwrite=overwrite)
        return {"extracted": result}
    except Exception as e:
        return {"error": str(e)}

# Route pour supprimer les fichiers extraits
@router.delete("/clear-extracted") # (DELETE) http://localhost:8050/api/v1/ingestion/clear-extracted
async def clear_extracted(txt_version: Optional[str] = None):
    try:
        extractor = Extractor()
        extractor.clear_extracted(txt_version=txt_version)
        return {"message": "Fichiers extraits supprimés avec succès."}
    except Exception as e:
        return {"error": str(e)}

# Route pour lister les versions extraites
@router.get("/list-extracted-versions") # (GET) http://localhost:8050/api/v1/ingestion/list-extracted-versions
async def list_extracted_versions():
    try:
        extractor = Extractor()
        versions = extractor.list_extracted_versions()
        return {"extracted_versions": versions}
    except Exception as e:
        return {"error": str(e)}



# --------------------------------------------------------------------------
# Routes for Chunking
# --------------------------------------------------------------------------

    
# Route pour diviser le texte par caractère
@router.post("/chunking/character") # (POST) http://localhost:8050/api/v1/ingestion/chunking/character
async def character_split(request: SimpleFileRequest):
    try:
        # Initialiser le Chunker avec le répertoire d'extraction
        chunker = Chunker()
        text = chunker.get_text_file(
            serie_version=request.extracted_serie,
            fname=request.file_name,
            fext=request.file_ext
        )

        # Utiliser la méthode character_split pour découper le texte
        chunks = chunker.character_split(text=text)

        # Log les chunks générés
        print(f"Chunks générés : {chunks}")

        return {"chunks": chunks}
    except Exception as e:
        print(f"Erreur : {str(e)}")
        return {"error": str(e)}

# Route pour diviser le texte par phrase
@router.post("/chunking/sentence") # (POST) http://localhost:8050/api/v1/ingestion/chunking/sentence
async def sentence_split(request: SimpleFileRequest):
    try:
        chunker = Chunker()
        text = chunker.get_text_file(
            serie_version=request.extracted_serie,
            fname=request.file_name,
            fext=request.file_ext
        )
        chunks = chunker.sentence_split(text)
        return {"chunks": chunks}
    except Exception as e:
        return {"error": str(e)}

# Route pour diviser le texte par paragraphe
@router.post("/chunking/paragraph") # (POST) http://localhost:8050/api/v1/ingestion/chunking/paragraph
async def paragraph_split(request: SimpleFileRequest):
    try:
        chunker = Chunker()
        text = chunker.get_text_file(
            serie_version=request.extracted_serie,
            fname=request.file_name,
            fext=request.file_ext
        )
        chunks = chunker.paragraph_split(text)
        return {"chunks": chunks}
    except Exception as e:
        return {"error": str(e)}

# Route pour diviser le texte par ligne
@router.post("/chunking/line") # (POST) http://localhost:8050/api/v1/ingestion/chunking/line
async def line_split(request: SimpleFileRequest):
    try:
        chunker = Chunker()
        text = chunker.get_text_file(
            serie_version=request.extracted_serie,
            fname=request.file_name,
            fext=request.file_ext
        )
        chunks = chunker.line_split(text)
        return {"chunks": chunks}
    except Exception as e:
        return {"error": str(e)}



# Route pour diviser le texte de manière récursive
@router.post("/chunking/recursive") # (POST) http://localhost:8050/api/v1/ingestion/chunking/recursive
async def recursive_split(request: CustomFileRequest):
    try:
        chunker = Chunker()
        text = chunker.get_text_file(
            serie_version=request.extracted_serie,
            fname=request.file_name,
            fext=request.file_ext
        )
        chunks = chunker.recursive_split(text, separators=request.options)
        return {"chunks": chunks}
    except Exception as e:
        return {"error": str(e)}

# Route pour prévisualiser le chunking
@router.post("/chunking/preview") # (POST) http://localhost:8050/api/v1/ingestion/chunking/preview
async def preview_chunking(request: CustomFileRequest):
    try:
        chunker = Chunker()
        text = chunker.get_text_file(
            serie_version=request.extracted_serie,
            fname=request.file_name,
            fext=request.file_ext
        )
        stats = chunker.preview_chunking(text, methods=request.options)
        return {"preview": stats}
    except Exception as e:
        return {"error": str(e)}

# Route pour suggérer la méthode de chunking
@router.post("/chunking/suggest") # (POST) http://localhost:8050/api/v1/ingestion/chunking/suggest
async def llm_suggest_chunking(request: SimpleFileRequest):
    try:
        chunker = Chunker()
        text = chunker.get_text_file(
            serie_version=request.extracted_serie,
            fname=request.file_name,
            fext=request.file_ext
        )
        suggestion = chunker.llm_suggest_chunking(text)
        return {"suggestion": suggestion}
    except Exception as e:
        return {"error": str(e)}

# Route pour sauvegarder les chunks dans un dossier
@router.post("/chunking/save_to_dir") # (POST) http://localhost:8050/api/v1/ingestion/chunking/save_to_dir
async def save_chunks_to_dir(chunks: List[str], out_dir: str, base_filename: Optional[str] = "chunk"):
    try:
        chunker = Chunker()
        paths = chunker.save_chunks_to_dir(chunks, out_dir, base_filename=base_filename)
        return {"paths": paths}
    except Exception as e:
        return {"error": str(e)}

# Route pour construire les métadonnées des chunks
@router.post("/chunking/metadata") # (POST) http://localhost:8050/api/v1/ingestion/chunking/metadata
async def build_chunk_metadata(chunks: List[str], source_doc: str, n: Optional[int] = None, size_max: Optional[int] = None):
    try:
        chunker = Chunker()
        metadata = chunker.build_chunk_metadata(chunks, source_doc, n=n, size_max=size_max)
        return {"metadata": metadata}
    except Exception as e:
        return {"error": str(e)}



@router.post("/chunking/save", response_model=SaveChunksResponse)
async def save_chunks(request: SaveChunksRequest):
    try:
        chunker = Chunker()
        result = chunker.save_chunks(request.chunks, request.base_filename)
        return SaveChunksResponse(
            version_path=result["chunks_dir"],
            version=result["chunks_vrsion"],
            paths=result["paths"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chunking/metadata")
async def build_version_chunk_metadata(version: str, chunks: List[str], n: Optional[int] = None, size_max: Optional[int] = None):
    try:
        chunker = Chunker()
        metadata = chunker.build_version_chunk_metadata(chunks, version, n, size_max)
        return {"metadata": metadata}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chunking/get_chunks/{version}", response_model=GetChunksByVersionResponse)
def get_chunks_by_version(version: str):
    chunker = Chunker()
    try:
        # return "test"
        chunks = chunker.get_chunks_by_version(version)
        return GetChunksByVersionResponse(chunks=chunks)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Une erreur est survenue lors de la récupération des chunks.");

class IndexChunksRequest(BaseModel):
    chunks: List[str]
    index_name: str

@router.post("/chunking/index")
def index_chunks(request: IndexChunksRequest):
    pipeline = EmbeddingPipeline()
    try:
        result = pipeline.index_chunks(request.chunks, request.index_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Une erreur est survenue lors de l'indexation des chunks : {str(e)}")

