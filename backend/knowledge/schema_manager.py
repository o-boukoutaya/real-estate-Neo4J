class GraphSchemaManager:
    """Application ou suggestion de schémas (placeholder)."""

    @staticmethod
    def apply_cypher(session, cypher_code: str):
        session.run(cypher_code)

    @staticmethod
    def suggest_schema_from_text(text: str):
        # Renvoie un schema fictif – à remplacer par appel LLM
        return {"label": "Document", "properties": ["text", "embedding"]}