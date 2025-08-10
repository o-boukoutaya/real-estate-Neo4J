# backend/rag/answer_synthesizer.py
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

_QA_PROMPT = PromptTemplate.from_template(
    """
CONTEXTE :
----------------
{context}
----------------

En te basant UNIQUEMENT sur ce contexte, réponds
à la question : {question}

- Style : argumentaire commercial professionnel, clair, factuel.
- Si l'information n'apparaît pas, dis : "Je n’ai pas la donnée."
"""
)


class AnswerSynthesizer:
    def __init__(self, llm=None, prompt: PromptTemplate | None = None):
        self.llm = llm or ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
        self.prompt = prompt or _QA_PROMPT

    # ------------------------------------------------------------------
    def synthesize(self, context: str, question: str) -> str:
        p = self.prompt.format(context=context, question=question)
        ans = self.llm.invoke(p)
        return ans.content if hasattr(ans, "content") else str(ans)
