from langchain.tools import Tool
from rag.graphrag_core import GraphRAG

graphrag = GraphRAG()

KGSearchTool = Tool.from_function(
    name="KGSearch",
    func=graphrag.query,
    description="Recherche intelligente sur le Knowledge Graph et le vector store."
)

SuggestSchemaTool = Tool.from_function(
    name="SuggestSchema",
    func=graphrag.suggest_schema,
    description="Suggère un schéma de graphe à partir d'un texte."
)

# Ajoutez d'autres tools selon les besoins (add_document, etc.)
