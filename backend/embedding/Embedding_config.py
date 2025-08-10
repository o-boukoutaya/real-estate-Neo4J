@dataclass
class EmbeddingConfig:
    provider: Literal["openai","gemini","huggingface"]
    model: str | None = None
    api_key: str | None = None
    api_base: str | None = None   # Azure
    api_type: str | None = None   # "azure" ou ""
    api_version: str | None = None
    deployment_name: str | None = None   # Azure
    batch_size: int = 32
    normalize: bool = False
