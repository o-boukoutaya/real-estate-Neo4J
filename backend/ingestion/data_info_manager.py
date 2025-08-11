import os
import datetime
from typing import List, Dict, Optional
from utils.logging import get_logger

logger = get_logger(__name__)


class DataInfoManager:
    def __init__(self, prov_dir=None, extracted_dir=None):
        """ Initialise le gestionnaire d'informations sur les données avec les chemins des dossiers de provenance et d'extraction."""
        self.prov_dir = prov_dir or os.path.join(os.path.dirname(__file__), '..', 'data', 'provfiles')
        self.extracted_dir = extracted_dir or os.path.join(os.path.dirname(__file__), '..', 'data', 'extracted')

    def list_versions(self, which='provfiles') -> List[str]:
        """ Liste les versions disponibles dans le dossier spécifié (provfiles ou extracted).
        Retourne une liste de noms de dossiers (versions).  """
        base = self.prov_dir if which == 'provfiles' else self.extracted_dir
        return [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))]

    def version_info(self, version: str, which='provfiles') -> Dict:
        """ Récupère les informations sur une version spécifique (provfiles ou extracted). """
        base = self.prov_dir if which == 'provfiles' else self.extracted_dir
        vpath = os.path.join(base, version)
        if not os.path.exists(vpath):
            return {}
        files = [f for f in os.listdir(vpath) if os.path.isfile(os.path.join(vpath, f))]
        types = list(set([os.path.splitext(f)[1].lower() for f in files]))
        size = sum(os.path.getsize(os.path.join(vpath, f)) for f in files)
        dates = [os.path.getmtime(os.path.join(vpath, f)) for f in files]
        return {
            'version': version,
            'file_count': len(files),
            'types': types,
            'size_bytes': size,
            'last_modified': datetime.datetime.fromtimestamp(max(dates)) if dates else None,
            'files': [self.file_info(os.path.join(vpath, f)) for f in files]
        }

    def file_info(self, path: str) -> Dict:
        stat = os.stat(path)
        return {
            'name': os.path.basename(path),
            'type': os.path.splitext(path)[1].lower(),
            'size_bytes': stat.st_size,
            'last_modified': datetime.datetime.fromtimestamp(stat.st_mtime),
        }

    def all_versions_info(self, which='provfiles') -> List[Dict]:
        """ Récupère les informations sur toutes les versions disponibles (provfiles ou extracted)."""
        return [self.version_info(v, which) for v in self.list_versions(which)]

    def is_version_indexed(self, version: str, neo4j_config: dict = None) -> Optional[bool]:
        """
        Vérifie si une version (extracted) est indexée dans Neo4j via Neo4jVectorManager.
        neo4j_config doit contenir les paramètres nécessaires à Neo4jVectorManager.
        """
        if neo4j_config is None:
            return None
        try:
            from embedding.vector_store import Neo4jVectorManager
            manager = Neo4jVectorManager(**neo4j_config)
            # On suppose que chaque chunk/document indexé a une propriété 'version' ou similaire
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(manager.url, auth=(manager.username, manager.password))
            with driver.session(database=manager.database) as session:
                # Adaptez la requête Cypher selon votre modèle de noeud/indexation
                result = session.run(f"""
                    MATCH (n:{manager.node_label}) WHERE n.version = $version RETURN count(n) as count
                """, {"version": version})
                count = result.single()["count"]
            driver.close()
            return count > 0
        except Exception as e:
            logger.error("Neo4j check failed: %s", e)
            return None

    def summarize_versions_tree(self) -> dict:
        """
        Génère une vue d'ensemble arborescente des versions et fichiers pour dashboard/inspection.
        Retourne un dict : {provfiles: [...], extracted: [...]}, chaque entrée détaillant version, taille, nb docs, types, etc.
        """
        def summarize(which):
            versions = self.all_versions_info(which)
            return [
                {
                    'version': v['version'],
                    'file_count': v['file_count'],
                    'types': v['types'],
                    'size_bytes': v['size_bytes'],
                    'last_modified': v['last_modified'],
                    'files': v['files']
                } for v in versions
            ]
        return {
            'provfiles': summarize('provfiles'),
            'extracted': summarize('extracted')
        }
