# Ce fichier doit être déplacé ici depuis la racine si ce n'est pas déjà fait.
# Ce fichier a été déplacé dans ingestion/ pour respecter l'architecture modulaire.

import os
import fitz  # PyMuPDF
import shutil
from datetime import datetime
from typing import Union, Callable, List
from utils.logging import get_logger

logger = get_logger(__name__)


class DocumentLoader:
    def __init__(self, splitter: Union[str, Callable] = "character", chunk_size: int = 1000, chunk_overlap: int = 100, separators: List[str] = None):
        self.splitter = splitter
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n", ".", "•", "،"]
        self.prov_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'provfiles')
        os.makedirs(self.prov_dir, exist_ok=True)

    def save_uploaded_files(self, files: list, serie_version: str = None, tags: str = None, description: str = None) -> dict:
        """
        Enregistre les fichiers uploadés dans un sous-dossier data/provfiles/serie_version (timestamp par défaut).
        Retourne un dict avec le chemin du dossier créé, la liste des fichiers et leurs métadonnées, et les erreurs éventuelles.
        Optionnellement, ajoute tags/description à la série (stockés dans un fichier meta.json).
        """
        import json
        if not serie_version:
            serie_version = f"serie_{datetime.now().strftime('%d%m%y-%H%M%S')}"
        else:
            serie_version = f"serie_{serie_version}" if not serie_version.startswith("serie_") else serie_version
        serie_path = os.path.join(self.prov_dir, serie_version)
        os.makedirs(serie_path, exist_ok=True)
        metadata = []
        errors = []
        for file in files:
            filename = getattr(file, 'filename', None) or getattr(file, 'name', None)
            if not filename:
                errors.append({'file': str(file), 'error': 'No filename detected'})
                continue
            ext = os.path.splitext(filename)[1].lower()
            if ext not in ['.pdf', '.txt', '.csv', '.docx', '.xlsx', '.xls']:
                errors.append({'file': filename, 'error': f'Unsupported file type: {ext}'})
                continue
            file_path = os.path.join(serie_path, filename)
            try:
                if hasattr(file, 'file'):
                    with open(file_path, 'wb') as f:
                        shutil.copyfileobj(file.file, f)
                elif isinstance(file, str) and os.path.exists(file):
                    shutil.copy(file, file_path)
                else:
                    errors.append({'file': filename, 'error': 'Unsupported file object'})
                    continue

                # Validation après écriture
                if os.path.getsize(file_path) == 0:
                    errors.append({'file': filename, 'error': 'File written is empty'})
                    os.remove(file_path)
                    continue

                stat = os.stat(file_path)
                metadata.append({
                    'name': filename,
                    'format': ext,
                    'size_bytes': stat.st_size,
                    'date': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except Exception as e:
                logger.error("Erreur lors de l'enregistrement de %s: %s", filename, e); errors.append({'file': filename, 'error': str(e)})
        # Save meta.json if tags/description provided
        if tags or description:
            meta = {'tags': tags, 'description': description, 'created': datetime.now().isoformat()}
            with open(os.path.join(serie_path, 'meta.json'), 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
        return {
            'serie_version': serie_version,
            'serie_path': serie_path,
            'files': metadata,
            'errors': errors
        }

    def list_series(self) -> list:
        """Liste tous les dossiers serie_version dans data/provfiles."""
        return [d for d in os.listdir(self.prov_dir) if os.path.isdir(os.path.join(self.prov_dir, d))]

    def get_latest_serie(self) -> str:
        """Retourne le chemin du dernier dossier serie_version (par date)."""
        series = self.list_series()
        if not series:
            return None
        latest = sorted(series)[-1]
        return os.path.join(self.prov_dir, latest)

    def clear_all_series(self):
        """Supprime tous les dossiers data/provfiles/serie_version."""
        for d in self.list_series():
            shutil.rmtree(os.path.join(self.prov_dir, d))

    def clear_serie(self, serie_version: str):
        """Supprime un dossier serie_version spécifique."""
        path = os.path.join(self.prov_dir, serie_version)
        if os.path.exists(path):
            shutil.rmtree(path)

    def extract_text_from_pdf(self, pdf_path, start_page=0, end_page=None):
        """ Extrait le texte d'un PDF entre start_page et end_page (0-indexé).
        Si end_page est None, extrait jusqu'à la dernière page."""
        doc = fitz.open(pdf_path)
        if end_page is None:
            end_page = len(doc)
        text = "\n".join([doc[i].get_text() for i in range(start_page, end_page)])
        doc.close()
        return text

    def extract_text_from_txt(self, txt_path):
        with open(txt_path, 'r', encoding='utf-8') as f:
            return f.read()

    def save_text(self, text, out_path):
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(text)

    def split_text(self, text, method=None):
        # Méthodes de découpage : character, recursive, sentence, paragraph, line
        if method == "character":
            return [text[i:i+self.chunk_size] for i in range(0, len(text), self.chunk_size - self.chunk_overlap)]
        elif method == "sentence":
            import re
            sentences = re.split(r'(?<=[.!?]) +', text)
            return [" ".join(sentences[i:i+1]) for i in range(0, len(sentences), 1)]
        elif method == "paragraph":
            paragraphs = text.split("\n\n")
            return [p for p in paragraphs if p.strip()]
        elif method == "line":
            return [l for l in text.splitlines() if l.strip()]
        elif method == "recursive":
            # Découpage intelligent (simplifié)
            import re
            chunks = re.split(r'[\n\r•،]+', text)
            return [c for c in chunks if c.strip()]
        else:
            return [text]

    def import_files(self, file_paths: List[str]) -> List[str]:
        """Charge le contenu de plusieurs fichiers (PDF, TXT, CSV, DOCX, XLSX)."""
        all_texts = []
        for path in file_paths:
            ext = os.path.splitext(path)[1].lower()
            if ext == ".pdf":
                all_texts.append(self._import_pdf(path))
            elif ext == ".txt":
                all_texts.append(self._import_txt(path))
            elif ext == ".csv":
                all_texts.append(self._import_csv(path))
            elif ext in [".docx"]:
                all_texts.append(self._import_docx(path))
            elif ext in [".xlsx", ".xls"]:
                all_texts.append(self._import_excel(path))
            else:
                raise ValueError(f"Unsupported file type: {ext}")
        return all_texts

    def _import_docx(self, path: str) -> str:
        from docx import Document
        doc = Document(path)
        return "\n".join([p.text for p in doc.paragraphs])

    def _import_excel(self, path: str) -> str:
        import pandas as pd
        df = pd.read_excel(path)
        return df.to_csv(index=False)