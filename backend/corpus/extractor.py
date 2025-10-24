# corpus/extractor.py
from __future__ import annotations
import io, os
from pathlib import Path
from typing import List, Optional
from .storage import FileStorage
from .models import ExtractRequest, ExtractResult, ExtractResultItem

# Dépendances optionnelles / fallback
try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

try:
    import pytesseract
    from PIL import Image
except Exception:
    pytesseract, Image = None, None

try:
    import pandas as pd
except Exception:
    pd = None

try:
    import docx
except Exception:
    docx = None


class TextExtractor:
    """
    Extraction robuste et pragmatique :
    - PDF : PyMuPDF pour le texte ; si la page a peu de texte et comporte des images -> OCR (si disponible)
    - DOCX : concat des paragraphes ; OCR des images intégrées si possible
    - TXT : lecture brute (auto-utf-8)
    - CSV : pandas -> texte tabulaire
    - XLSX/XLS : pandas -> concat cellules 'object'
    N'extrait PAS les chunks. Écrit un .txt par fichier dans series/text/.
    """
    # Initialization : define the storage
    def __init__(self, storage: FileStorage):
        self.storage = storage

    # Extract text from a series
    def extract_series(self, req: ExtractRequest) -> ExtractResult:
        sid = req.series_id
        out_items: List[ExtractResultItem] = []

        for src in self.storage.list_raw(sid):
            text, pages, used_ocr_pages = self._extract_one(src, req)
            text_dir = self.storage.text_dir(sid)
            text_dir.mkdir(parents=True, exist_ok=True)
            out_path = text_dir / (src.stem + ".txt")
            out_path.write_text(text, encoding="utf-8")
            out_items.append(
                ExtractResultItem(
                    filename=src.name,
                    text_path=str(out_path),
                    char_count=len(text),
                    pages=pages,
                    used_ocr_pages=used_ocr_pages,
                )
            )
        return ExtractResult(series_id=sid, items=out_items)

    # -------- impl détaillées --------

    # Extraction of text from a file
    def _extract_one(self, path: Path, req: ExtractRequest) -> tuple[str, Optional[int], int]:
        ext = path.suffix.lower()
        if ext == ".pdf":
            return self._pdf_to_text(path, req)
        if ext == ".txt":
            return self._txt_to_text(path), None, 0
        if ext == ".csv":
            return self._csv_to_text(path), None, 0
        if ext in (".xlsx", ".xls"):
            return self._xls_to_text(path), None, 0
        if ext == ".docx":
            return self._docx_to_text(path, req), None, 0
        # fallback brut
        return self._txt_to_text(path), None, 0

    # Fallback to text extraction
    def _txt_to_text(self, path: Path) -> str:
        # essaye utf-8 puis latin-1
        for enc in ("utf-8", "utf-8-sig", "cp1252", "latin1"):
            try:
                return path.read_text(encoding=enc)
            except Exception:
                continue
        # binaire improbable
        return path.read_bytes().decode("utf-8", errors="ignore")

    # CSV extraction
    def _csv_to_text(self, path: Path) -> str:
        if pd is None:
            return path.read_text(encoding="utf-8", errors="ignore")
        try:
            df = pd.read_csv(path, dtype=str, encoding="utf-8", sep=None, engine="python")
        except Exception:
            df = pd.read_csv(path, dtype=str, encoding_errors="ignore")
        df = df.fillna("")
        # petite heuristique : si 2 colonnes -> key: value
        if df.shape[1] == 2:
            lines = [f"{r[0]}: {r[1]}".strip() for r in df.itertuples(index=False)]
            return "\n".join(lines)
        return df.to_csv(index=False)

    # XLSX/XLS extraction
    def _xls_to_text(self, path: Path) -> str:
        if pd is None:
            return ""
        try:
            df_all = pd.read_excel(path, sheet_name=None, dtype=str, engine=None)
        except Exception:
            return ""
        texts = []
        for name, df in df_all.items():
            df = df.fillna("")
            texts.append(f"# Sheet: {name}")
            texts.append(df.to_csv(index=False))
        return "\n".join(texts)

    # DOCX extraction
    def _docx_to_text(self, path: Path, req: ExtractRequest) -> str:
        if docx is None:
            return ""
        try:
            doc = docx.Document(str(path))
        except Exception:
            return ""
        lines = []
        for p in doc.paragraphs:
            t = p.text.strip()
            if t:
                lines.append(t)

        # OCR des images si possible
        if req.ocr and pytesseract and Image:
            for rel in getattr(doc.part, "related_parts", {}).values():
                try:
                    if rel.content_type.startswith("image/"):
                        bio = io.BytesIO(rel.blob)
                        img = Image.open(bio)
                        txt = pytesseract.image_to_string(img, lang=req.ocr_langs)
                        if txt.strip():
                            lines.append(txt.strip())
                except Exception:
                    pass
        return "\n".join(lines)

    # PDF extraction
    def _pdf_to_text(self, path: Path, req: ExtractRequest) -> tuple[str, int, int]:
        if fitz is None:
            # fallback faible
            return path.read_text(encoding="utf-8", errors="ignore"), 0, 0

        text_parts, used_ocr_pages = [], 0
        doc = fitz.open(str(path))
        for i, page in enumerate(doc):
            # 1) extraction texte via blocs (préserve mieux l’ordre visuel)
            blocks = page.get_text("blocks") or []
            blocks.sort(key=lambda b: (b[1], b[0]))  # tri top-left -> bottom-right
            txt = "\n".join([b[4] for b in blocks if isinstance(b, (list, tuple)) and len(b) > 4]).strip()

            need_ocr = False
            if req.ocr and pytesseract and Image:
                # heuristique : très peu de texte -> OCR si image présente
                if len(txt) < req.min_text_chars:
                    # page contient-elle une image ?
                    try:
                        img_list = page.get_images(full=True)
                        if img_list:
                            need_ocr = True
                    except Exception:
                        pass

            if need_ocr:
                used_ocr_pages += 1
                # rasteriser la page
                try:
                    pix = page.get_pixmap(dpi=220)  # assez pour l'arabe
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    ocr_txt = pytesseract.image_to_string(img, lang=req.ocr_langs)
                    txt = (txt + "\n" + ocr_txt).strip() if txt else ocr_txt.strip()
                except Exception:
                    pass

            if txt:
                text_parts.append(txt)

        return ("\n\n".join(text_parts), len(doc), used_ocr_pages)
