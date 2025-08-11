# backend/rag/query_generator.py
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from dotenv import load_dotenv
from utils.logging import get_logger

logger = get_logger(__name__)


load_dotenv()


_DEFAULT_PROMPT = PromptTemplate.from_template(
    """
Tu es un expert Neo4j. Génère une requête Cypher **lue-seule** répondant à la question :
QUESTION : {question}
ENTITÉS : {entities}

Réponds uniquement par la requête sans explication.
"""
)


class QueryGenerator:
    def __init__(self, llm=None, prompt: PromptTemplate | None = None):
        self.llm = llm or ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            # other params...
        )
        # self.llm = llm or ChatGoogleGenerativeAI(model="gemini-embedding-4096", temperature=0)
        self.prompt = prompt or _DEFAULT_PROMPT

    # ------------------------------------------------------------------
    def generate(self, question: str, entities: list[str]) -> str:
        try:
            p = self.prompt.format(question=question, entities=", ".join(entities))
            ans = self.llm.invoke(p)
            return ans.content.strip() if hasattr(ans, "content") else str(ans).strip()
        except Exception as e:
            logger.error("Cypher generation failed: %s", e)
            return ""


