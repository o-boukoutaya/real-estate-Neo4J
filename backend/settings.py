# backend/settings.py
import os, json

NEO4J_CFG = {
    "url":      os.getenv("NEO4J_URI",      "bolt://localhost:7687"),
    "username": os.getenv("NEO4J_USERNAME", "neo4j"),
    "password": os.getenv("NEO4J_PASSWORD", "123456789"),
    "database": os.getenv("NEO4J_DATABASE", "neo4j"),   # optionnel
    "index_name": os.getenv("NEO4J_INDEX_NAME", "chunk_vector"),  # nom de l'index vectoriel (index_110625_022017)
    "node_label": os.getenv("NEO4J_NODE_LABEL", "Chunk"),  # label des noeuds
    "embed_prop": os.getenv("NEO4J_EMBED_PROP", "embedding"),
}

EMBED_CFG = {
    "provider": os.getenv("EMBEDDER_PROVIDER", "huggingface"),
    "params":   json.loads(os.getenv("EMBEDDER_PARAMS", "{}"))
}

SERVER_OPTIONS = {
    "host":     os.getenv("HOST", "127.0.0.1"),
    "port":     int(os.getenv("PORT", 8050)),
    "port_snd": int(os.getenv("PORT_SND", 8443)),  # pour éviter qu’un second processus/boucle se lie au même couple host:port, d’où l’erreur.
    "transport": os.getenv("TRANSPORT", "sse"),  # sse | stdio
    "DEV_RELOAD" : bool(os.getenv("DEV_RELOAD", False))  # pour le rechargement automatique en dev
}

PROVIDERS = {
    "huggingface": "HuggingFace",
    "openai":      "OpenAI",
    "gemini":      "Google Gemini"
}

# GEMINI_TEXT_MODELS = {
#     "gemini-1.5-flash": "gemini-1.5-flash",
#     "gemini-1.5-pro":   "gemini-1.5-pro",
#     "gemini-1.0-flash": "gemini-1.0-flash",
#     "gemini-1.0-pro":   "gemini-1.0-pro"
# }

# OPENAI_TEXT_MODELS = {
#     "gpt-3.5-turbo":        "gpt-3.5-turbo",
#     "gpt-4":                "gpt-4",
#     "gpt-4-1106-preview":   "gpt-4-1106-preview"
# }

# HUGGINGFACE_TEXT_MODELS = {
#     "all-mpnet-base-v2": "all-mpnet-base-v2",
#     "sentence-transformers/all-MiniLM-L6-v2": "sentence-transformers/all-MiniLM-L6-v2",
#     "sentence-transformers/all-MiniLM-L12-v2": "sentence-transformers/all-MiniLM-L12-v2"
# }