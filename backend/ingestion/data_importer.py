# Ce module centralise le pipeline d'ingestion :
# 1. Upload et sauvegarde de documents
# 2. Extraction textuelle
# 3. Découpage en chunks

import os
from ingestion.document_loader import DocumentLoader
from ingestion.extractor import Extractor
from ingestion.chunker import Chunker

class DataImporter:
    def __init__(self):
        self.loader = DocumentLoader()
        self.extractor = Extractor()
        self.chunker = Chunker()

    def run_ingestion(self, files, overwrite=False, chunk_method='sentence', chunk_size=1000, chunk_overlap=100):
        """
        Exécute tout le workflow d'ingestion :
        - Upload et sauvegarde des fichiers
        - Extraction textuelle
        - Chunking
        """
        # Étape 1 : sauvegarde des fichiers uploadés
        serie_path = self.loader.save_uploaded_files(files)
        serie_version = os.path.basename(serie_path)

        # Étape 2 : extraction du texte
        txt_map = self.extractor.extract_texts(
            serie_version=serie_version,
            overwrite=overwrite
        )

        # Étape 3 : découpage en chunks
        all_chunks = {}
        self.chunker.chunk_size = chunk_size
        self.chunker.chunk_overlap = chunk_overlap
        for fname, meta in txt_map.items():
            with open(meta["path"], 'r', encoding='utf-8') as f:
                text = f.read()
            if chunk_method == "character":
                chunks = self.chunker.character_split(text)
            elif chunk_method == "sentence":
                chunks = self.chunker.sentence_split(text)
            elif chunk_method == "paragraph":
                chunks = self.chunker.paragraph_split(text)
            elif chunk_method == "line":
                chunks = self.chunker.line_split(text)
            elif chunk_method == "recursive":
                chunks = self.chunker.recursive_split(text)
            else:
                raise ValueError(f"Méthode de chunking inconnue : {chunk_method}")
            all_chunks[fname] = chunks

        return {
            "serie_version": serie_version,
            "extracted_texts": txt_map,
            "chunks": all_chunks
        }
