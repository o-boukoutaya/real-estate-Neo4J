from utils.logging import get_logger

logger = get_logger(__name__)

class GraphSchemaManager:
    """Application ou suggestion de schémas (placeholder)."""

    @staticmethod
    def apply_cypher(session, cypher_code: str):
        try:
            session.run(cypher_code)
        except Exception as e:
            logger.error("Cypher execution failed: %s", e)
            raise

    @staticmethod
    def suggest_schema_from_text(text: str):
        try:
            return {"label": "Document", "properties": ["text", "embedding"]}
        except Exception as e:
            logger.error("Schema suggestion failed: %s", e)
            return {}

