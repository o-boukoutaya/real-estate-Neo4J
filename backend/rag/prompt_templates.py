from utils.logging import get_logger

logger = get_logger(__name__)

# Ce fichier doit contenir les prompts utilisés par les agents RAG.

def get_prompt_for_agent(agent_name):
    try:
        prompts = {
            "agent_1": "Prompt for agent 1",
            "agent_2": "Prompt for agent 2",
            # Ajoutez d'autres agents et leurs invites ici
        }
        return prompts.get(agent_name, "Aucun prompt trouvé pour cet agent.")
    except Exception as e:
        logger.error("Prompt retrieval failed for %s: %s", agent_name, e)
        return "Aucun prompt trouvé pour cet agent."
