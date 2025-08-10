# Ce fichier doit contenir l'interface commune pour les embedders (OpenAI, HF, Gemini...)
"""Interface + implémentations d’embedders."""
from abc import ABC, abstractmethod
from typing import List

class EmbedderInterface:
    @property
    @abstractmethod
    def dimension(self) -> int: ...

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Prend un texte en entrée et retourne une liste de flottants représentant l'embedding."""
        raise NotImplementedError("La méthode 'embed' doit être implémentée par la sous-classe.")

    @abstractmethod
    def batch_embed(self, texts: List[str]) -> List[List[float]]:
        """Prend une liste de textes en entrée et retourne une liste d'embeddings correspondants."""
        raise NotImplementedError("La méthode 'batch_embed' doit être implémentée par la sous-classe.")

    # Représentation lisible
    def __repr__(self):
        return f"{self.__class__.__name__}()"

# -------------------------- Hugging Face --------------------------
class HuggingFaceEmbedder(EmbedderInterface):
    """ Implémente l'interface d'embedding pour Hugging Face Transformers. """
    def __init__(self, model_name="sentence-transformers/all-mpnet-base-v2", *, batch_size: int = 32,
                 normalize_embeddings: bool = False):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self.batch_size = batch_size
        self.normalize = normalize_embeddings
    
    @property
    def dimension(self) -> int:
        """Retourne la dimension de l'embedding."""
        return self.model.get_sentence_embedding_dimension()

    def embed(self, text: str) -> List[float]:
        return self.model.encode(text, normalize_embeddings=self.normalize).tolist()

    def batch_embed(self, texts: List[str]) -> List[List[float]]:
        vecs = self.model.encode(texts, batch_size=self.batch_size, normalize_embeddings=self.normalize)
        return [v.tolist() for v in vecs]

# ----------------------------- OpenAI -----------------------------
# class OpenAIEmbedder(EmbedderInterface):
#     def __init__(self, api_key: str, model: str = "text-embedding-ada-002"):
#         import openai
#         from openai import AzureOpenAI
#         openai.api_key = api_key
#         self.client = openai
#         self.model = model

#     def embed(self, text: str) -> List[float]:
#         return self.client.embeddings.create(input=[text], model=self.model).data[0].embedding

#     def batch_embed(self, texts: List[str]) -> List[List[float]]:
#         return [d.embedding for d in self.client.embeddings.create(input=texts, model=self.model).data]

class OpenAIEmbedder(EmbedderInterface):
    def __init__(self, *, api_key: str,
                       model: str = "text-embedding-ada-002",
                       api_base: str | None = None,
                       api_type: str | None = None,
                       api_version: str | None = None,
                       deployment_name: str | None = None,
                       **_):
        from openai import OpenAI, AzureOpenAI

        if api_type == "azure":
            self.client = AzureOpenAI(
                api_key=api_key,
                azure_endpoint=api_base,
                api_version=api_version or "2023-07-01-preview"
            )
            # pour Azure, `model` = nom du *deployment*
            self.model = deployment_name or model
        else:
            self.client = OpenAI(api_key=api_key, base_url=api_base)
            self.model = model

    @property
    def dimension(self) -> int:
        """Retourne la dimension de l'embedding pour le modèle OpenAI."""
        # Pour ada-002, la dimension est 1536
        return 1536

    def embed(self, text: str) -> List[float]:
        return self.batch_embed([text])[0]

    def batch_embed(self, texts: List[str]) -> List[List[float]]:
        resp = self.client.embeddings.create(input=texts, model=self.model)
        return [d.embedding for d in resp.data]

    def dummy_vector(self) -> List[float]:
        # dimension fixe pour ada-002 = 1536
        return [0.0]*1536


# ----------------------------- Gemini -----------------------------
class GeminiEmbedder(EmbedderInterface):
    def __init__(self, api_key: str, model: str = "gemini-embedding-4096"):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.client = genai
        self.model = model
    
    @property
    def dimension(self) -> int:
        """Retourne la dimension de l'embedding pour le modèle Gemini."""
        # Pour gemini-embedding-4096, la dimension est 4096
        return 4096

    def embed(self, text: str) -> List[float]:
        return self.batch_embed([text])[0]

    def batch_embed(self, texts: List[str]) -> List[List[float]]:
        resp = self.client.embeddings.generate(model=self.model, texts=texts)
        return [e.values for e in resp.embeddings]