# Ce fichier doit contenir la gestion des pages PDF, TXT, CSV.

import os
import fitz  # PyMuPDF
import shutil
from datetime import datetime
from utils.logging import get_logger

logger = get_logger(__name__)


class Extractor:
    def __init__(self, prov_dir=None, extracted_dir=None):
        """ Initialise l'Extractor avec les chemins des dossiers de provenance et d'extraction."""
        self.prov_dir = prov_dir or os.path.join(os.path.dirname(__file__), '..', 'data', 'provfiles')
        self.extracted_dir = extracted_dir or os.path.join(os.path.dirname(__file__), '..', 'data', 'extracted')
        os.makedirs(self.extracted_dir, exist_ok=True)

    def list_series(self):
        return [d for d in os.listdir(self.prov_dir) if os.path.isdir(os.path.join(self.prov_dir, d))]

    def get_latest_serie(self):
        series = self.list_series()
        if not series:
            return None
        latest = sorted(series)[-1]
        return latest

    def extract_texts(self, serie_version=None, files=None, page_ranges=None, txt_version=None, overwrite=False):
        """
        Extrait le texte de tous les fichiers d'une série (ou d'une sélection), avec gestion des pages PDF.
        - serie_version: dossier source (par défaut le dernier)
        - files: liste de fichiers à extraire (par défaut tous)
        - page_ranges: dict {filename: (start, end)} pour PDF
        - txt_version: nom du dossier de sortie (par défaut = serie_version)
        - overwrite: si False, ne pas écraser les fichiers déjà extraits
        """
        serie_version = serie_version or self.get_latest_serie()
        if not serie_version:
            raise ValueError("Aucune série de fichiers trouvée.")
        serie_path = os.path.join(self.prov_dir, serie_version)
        file_list = files or [f for f in os.listdir(serie_path) if os.path.isfile(os.path.join(serie_path, f))]
        txt_version = txt_version or serie_version
        out_dir = os.path.join(self.extracted_dir, txt_version)
        os.makedirs(out_dir, exist_ok=True)
        extracted = {}

        for fname in file_list:
            try:
                in_path = os.path.normpath(os.path.join(serie_path, fname))  # Normalisation du chemin
                ext = os.path.splitext(fname)[1].lower()
                base_name = os.path.splitext(fname)[0]  # Supprimer l'extension initiale
                out_path = os.path.normpath(os.path.join(out_dir, base_name + '.txt'))  # Normalisation du chemin

                # Vérification si le fichier est vide
                if os.path.getsize(in_path) == 0:
                    logger.warning("Le fichier est vide : %s", in_path)
                    extracted[fname] = {"error": "Fichier vide"}
                    continue

                if not overwrite and os.path.exists(out_path):
                    extracted[fname] = {
                        "path": out_path,
                        "char_count": len(text),
                        "pages": end - start if ext == ".pdf" else None
                    }  # Ne pas écraser, mais indiquer le chemin
                    continue  # skip si déjà extrait

                # Extraction
                if ext == '.pdf':
                    doc = fitz.open(in_path)
                    start, end = (0, len(doc))
                    if page_ranges and fname in page_ranges:
                        start, end = page_ranges[fname]
                    text = "\n".join([doc[i].get_text() for i in range(start, end)])
                    doc.close()
                elif ext == '.txt':
                    with open(in_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                elif ext == '.csv':
                    with open(in_path, newline='', encoding='utf-8') as csvfile:
                        import csv
                        reader = csv.reader(csvfile)
                        text = "\n".join([", ".join(row) for row in reader])
                elif ext == '.docx':
                    from docx import Document
                    doc = Document(in_path)
                    text = "\n".join([p.text for p in doc.paragraphs])
                elif ext in ['.xlsx', '.xls']:
                    import pandas as pd
                    df = pd.read_excel(in_path)
                    text = df.to_csv(index=False)
                else:
                    continue  # skip unsupported

                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(text)

                extracted[fname] = {
                    "path": out_path,
                    "char_count": len(text),
                    "pages": end - start if ext == ".pdf" else None
                }
            except Exception as e:
                logger.error("Erreur lors de l'extraction du fichier %s: %s", fname, e)

        return extracted

    def clear_extracted(self, txt_version=None):
        """Supprime un dossier d'extraction (txt_version) ou tout extracted."""
        if txt_version:
            path = os.path.join(self.extracted_dir, txt_version)
            if os.path.exists(path):
                shutil.rmtree(path)
        else:
            for d in os.listdir(self.extracted_dir):
                full = os.path.join(self.extracted_dir, d)
                if os.path.isdir(full):
                    shutil.rmtree(full)

    def list_extracted_versions(self):
        """Retourne toutes les versions présentes dans le dossier extracted."""
        return [
            d for d in os.listdir(self.extracted_dir)
            if os.path.isdir(os.path.join(self.extracted_dir, d))
        ]
