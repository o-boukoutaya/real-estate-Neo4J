import re
from typing import List
import os
from datetime import datetime

class Chunker:
    def __init__(self, chunk_size=1000, chunk_overlap=100, extracted_dir=None):
        """ Initialise le Chunker avec la taille de chunk et le chevauchement."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.extracted_dir = extracted_dir or os.path.join(os.path.dirname(__file__), '..', 'data', 'extracted')

    # Retrouver le fichier texte à découper dans la série extraite
    def get_text_file(self, serie_version: str, fname: str, fext: str) -> str:
        """ Récupère le chemin du fichier texte à découper dans la série extraite."""
        if not serie_version:
            raise ValueError("Aucune série de fichiers trouvée.")
        if not fname or not fext:
            raise ValueError("Nom de fichier et extension requis pour le découpage par caractères.")

        serie_path = os.path.join(self.extracted_dir, serie_version)
        in_path = os.path.normpath(os.path.join(serie_path, fname + '.' + fext))

        # Log le chemin construit
        print(f"Chemin construit : {in_path}")

        # Vérifier l'existence et les permissions du fichier
        abs_path = os.path.abspath(in_path)
        print(f"Chemin absolu : {abs_path}")
        if not os.path.exists(abs_path):
            print(f"Le fichier n'existe pas : {abs_path}")
            raise FileNotFoundError(f"Le fichier spécifié n'existe pas : {abs_path}")
        if not os.access(abs_path, os.R_OK):
            print(f"Le fichier n'est pas accessible en lecture : {abs_path}")
            raise PermissionError(f"Le fichier spécifié n'est pas accessible en lecture : {abs_path}")

        with open(abs_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return text

    def character_split(self, text: str) -> List[str]:
        """ Découpe le texte en chunks de taille fixe avec chevauchement."""
        chunks = []
        i = 0
        while i < len(text):
            chunks.append(text[i:i+self.chunk_size])
            i += self.chunk_size - self.chunk_overlap
        return chunks

    def sentence_split(self, text: str) -> List[str]:
        """ Découpe le texte en phrases, en utilisant la ponctuation comme séparateur."""
        sentences = re.split(r'(?<=[.!?]) +', text)
        return self._merge_chunks(sentences)

    def paragraph_split(self, text: str) -> List[str]:
        """ Découpe le texte en paragraphes, en utilisant les sauts de ligne comme séparateur."""
        paragraphs = text.split('\n\n')
        return self._merge_chunks(paragraphs)

    def line_split(self, text: str) -> List[str]:
        """ Découpe le texte en lignes, en utilisant les sauts de ligne simples."""
        lines = text.splitlines()
        return self._merge_chunks(lines)

    def recursive_split(self, text: str, separators=None) -> List[str]:
        """ Découpe le texte en utilisant des séparateurs multiples (par défaut : \n, ., •, ،).
        Permet de gérer des textes complexes avec différents types de séparation."""
        separators = separators or ['\n', '.', '•', '،']
        pattern = '|'.join(map(re.escape, separators))
        splits = re.split(pattern, text)
        return self._merge_chunks(splits)

    def _merge_chunks(self, parts: List[str]) -> List[str]:
        """ Fusionne les parties en chunks de taille approximative chunk_size."""
        chunks = []
        chunk = ""
        for part in parts:
            if len(chunk) + len(part) < self.chunk_size:
                chunk += part + " "
            else:
                chunks.append(chunk.strip())
                chunk = part + " "
        if chunk:
            chunks.append(chunk.strip())
        return chunks

    def preview_chunking(self, text: str, methods=None) -> dict:
        """
        Prévoyez le nombre de chunks et la taille moyenne pour chaque méthode.
        """
        methods = methods or ["character", "sentence", "paragraph", "line", "recursive"]
        stats = {}
        for method in methods:
            if method == "character":
                chunks = self.character_split(text)
            elif method == "sentence":
                chunks = self.sentence_split(text)
            elif method == "paragraph":
                chunks = self.paragraph_split(text)
            elif method == "line":
                chunks = self.line_split(text)
            elif method == "recursive":
                chunks = self.recursive_split(text)
            else:
                continue
            stats[method] = {
                "n_chunks": len(chunks),
                "avg_size": sum(len(c) for c in chunks) // len(chunks) if chunks else 0
            }
        return stats

    def llm_suggest_chunking(self, text: str) -> str:
        """
        Placeholder : LLM suggère la meilleure méthode de chunking selon le texte.
        """
        # À brancher sur un vrai LLM plus tard
        if len(text) < 2000:
            return "sentence"
        elif len(text) < 10000:
            return "paragraph"
        else:
            return "recursive"

    def save_chunks_to_dir(self, chunks: List[str], out_dir: str, base_filename: str = "chunk") -> List[str]:
        """
        Sauvegarde chaque chunk dans un fichier texte distinct dans le dossier out_dir.
        Retourne la liste des chemins des fichiers créés.
        """
        os.makedirs(out_dir, exist_ok=True)
        paths = []
        for i, chunk in enumerate(chunks):
            fname = f"{base_filename}_{i+1}.txt"
            fpath = os.path.join(out_dir, fname)
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(chunk)
            paths.append(fpath)
        return paths

    def save_chunks(self, chunks: List[str], base_filename: str = "chunk") -> List[dict]:
        """
        Sauvegarde chaque chunk dans un fichier texte distinct dans le dossier data/chunks/<version>.
        Retourne la liste des chemins des fichiers créés avec la version incluse.
        """
        chunks_version = f"chunks_{datetime.now().strftime('%d%m%y-%H%M%S')}"
        version_dir = os.path.join(self.extracted_dir, '..', 'chunks', chunks_version)
        os.makedirs(version_dir, exist_ok=True)
        results = {"chunks_dir": version_dir, "chunks_vrsion": chunks_version, "paths":[]}
        for i, chunk in enumerate(chunks):
            fname = f"{base_filename}_{i+1}.txt"
            fpath = os.path.join(version_dir, fname)
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(chunk)
            # append item to paths in results
            results["paths"].append({"item": f"{base_filename}_{i+1}", "path": fpath})
        return results

    def build_chunk_metadata(self, chunks: List[str], source_doc: str, n: int = None, size_max: int = None) -> List[dict]:
        """
        Prépare la structure de retour pour chaque chunk : {id, text, start_char, end_char, source_doc}
        Permet de limiter à n chunks ou à une taille totale maximale (en caractères).
        """
        meta = []
        pos = 0
        total_size = 0
        for i, chunk in enumerate(chunks):
            if n is not None and i >= n:
                break
            if size_max is not None and total_size + len(chunk) > size_max:
                break
            start = pos
            end = pos + len(chunk)
            meta.append({
                "id": f"{os.path.basename(source_doc)}_chunk_{i+1}",
                "text": chunk,
                "start_char": start,
                "end_char": end,
                "source_doc": source_doc
            })
            pos = end
            total_size += len(chunk)
        return meta

    def build_version_chunk_metadata(self, chunks: List[str], version: str, n: int = None, size_max: int = None) -> List[dict]:
        """
        Prépare la structure de retour pour chaque chunk : {id, text, start_char, end_char, version}
        Permet de limiter à n chunks ou à une taille totale maximale (en caractères).
        """
        meta = []
        pos = 0
        total_size = 0
        for i, chunk in enumerate(chunks):
            if n is not None and i >= n:
                break
            if size_max is not None and total_size + len(chunk) > size_max:
                break
            start = pos
            end = pos + len(chunk)
            meta.append({
                "id": f"chunks_{version}_chunk_{i+1}",
                "text": chunk,
                "start_char": start,
                "end_char": end,
                "version": version
            })
            pos = end
            total_size += len(chunk)
        return meta
    
    # retourner les chunks d'une chunk version
    def get_chunks_by_version(self, version: str) -> List[str]:
        """
        Retourne les chunks d'une version spécifique.
        """
        version_dir = os.path.join(self.extracted_dir, '..', 'chunks', version)
        if not os.path.exists(version_dir):
            raise FileNotFoundError(f"Version de chunks non trouvée : {version}")
        
        chunks = []
        for fname in os.listdir(version_dir):
            if fname.endswith('.txt'):
                with open(os.path.join(version_dir, fname), 'r', encoding='utf-8') as f:
                    chunks.append(f.read())
        return chunks