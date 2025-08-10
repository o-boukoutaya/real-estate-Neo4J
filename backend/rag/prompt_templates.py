# Ce fichier doit contenir les prompts utilisés par les agents RAG.

def get_prompt_for_agent(agent_name):
    prompts = {
        "agent_1": "Prompt for agent 1",
        "agent_2": "Prompt for agent 2",
        # Ajoutez d'autres agents et leurs invites ici
    }
    return prompts.get(agent_name, "Aucun prompt trouvé pour cet agent.")