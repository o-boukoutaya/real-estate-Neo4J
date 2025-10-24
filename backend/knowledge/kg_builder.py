# knowledge/kg_builder.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Iterable, List, Sequence, Tuple, Union

from app.core.logging import log_step
from .graph_builder import GraphBuilder

TripletLike = Union[
    Tuple[str, str, str],                # ("subject","relation","object")
    dict,                                # {"subject":...,"relation":...,"object":...}
    object,                              # objet avec .subject/.relation/.object
]

@dataclass
class Triplet:
    subject: str
    relation: str
    object: str
    confidence: float = 1.0

    @classmethod
    def from_any(cls, t: TripletLike) -> "Triplet":
        # tuple
        if isinstance(t, tuple) and len(t) == 3:
            s, r, o = t
            return cls(str(s).strip(), str(r).strip(), str(o).strip())
        # dict
        if isinstance(t, dict):
            s = t.get("subject")
            r = t.get("relation")
            o = t.get("object") or t.get("object_")
            if s and r and o:
                return cls(str(s).strip(), str(r).strip(), str(o).strip(), float(t.get("confidence", 1.0)))
        # objet duck-typed
        if all(hasattr(t, k) for k in ("subject", "relation", "object")):
            return cls(str(t.subject).strip(), str(t.relation).strip(), str(t.object).strip(),
                       float(getattr(t, "confidence", 1.0)))
        raise TypeError(f"Unsupported triplet format: {type(t)!r}")

class KGBuilder:
    def __init__(self, *, llm: GraphBuilder | None = None, **kwargs):
        self.chain = llm or GraphBuilder(**kwargs)

    @log_step("kg_build_from_text")
    def build_from_text(self, text: str) -> List[dict]:
        raw = self.chain.extract_relations(text)
        triples: List[Triplet] = [Triplet.from_any(t) for t in raw]
        # Ici tu peux insérer l’écriture dans Neo4j si besoin.
        return [asdict(t) for t in triples]

    @log_step("kg_build_from_chunks")
    def build_from_chunks(self, chunks: Sequence[str]) -> List[dict]:
        # batch simple → concat
        return self.build_from_text("\n".join(chunks))

    @log_step("kg_build_from_series")
    def build_from_series(self, series_text: str | Iterable[str]) -> List[dict]:
        """
        - Si 'series_text' est déjà une *grosse* chaîne -> traite telle quelle.
        - Si c'est un itérable de petits textes -> concat et traite.
        """
        if isinstance(series_text, str):
            return self.build_from_text(series_text)
        return self.build_from_chunks(list(series_text))
