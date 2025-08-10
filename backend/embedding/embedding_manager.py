"""Factory + validation des embedders."""
from .embedder_base import HuggingFaceEmbedder, OpenAIEmbedder, GeminiEmbedder

class EmbeddingManager:
    _registry = {
        "huggingface": HuggingFaceEmbedder,
        "openai": OpenAIEmbedder,
        "gemini": GeminiEmbedder,
    }

    def __init__(self, provider: str, **kwargs):
        provider = provider.lower()
        if provider not in self._registry:
            raise ValueError(f"Provider inconnu : {provider}")
        self.provider = provider
        self.kwargs = kwargs
        self._embedder = None

    # ------------------------------------------------------------------
    def get_embedder(self):
        if self._embedder is None:
            self._embedder = self._registry[self.provider](**self.kwargs)
        return self._embedder

    # ------------------------------------------------------------------
    # def validate(self):
    #     emb = self.get_embedder().embed("ping")  # should not crash
    #     if not isinstance(emb, list):
    #         raise RuntimeError("Embedding retourné invalide")
    #     return True

    def validate(self) -> bool:
        """
        Chaque Embedder implémente dummy_vector() en renvoyant un vecteur zéro de la bonne dimension (768, 1536…).
        Pour un vrai health-check, lancez une tâche asynchrone en arrière-plan qui envoie un « ping » toutes les X minutes, 
        journalise l'état et ne bloque pas le lancement."""
        
        try:
            # test purement local : on n’appelle PAS l’API
            vec = self.get_embedder().dummy_vector()   # ← nouvelle méthode
            assert isinstance(vec, list) and all(isinstance(x, float) for x in vec)
        except Exception as e:
            raise RuntimeError("Embedding retourné invalide") from e
        return True


    # API pratique ------------------------------------------------------
    def embed_texts(self, texts):
        return self.get_embedder().batch_embed(texts)

    # ------------------------------------------------------------------
    def __str__(self):
        return f"EmbeddingManager(provider={self.provider})"