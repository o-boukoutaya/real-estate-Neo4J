"""Simple GraphBuilder – convertit un texte en liste de triplets (subject, relation, object)
   en s’appuyant sur un LLM compatible LangChain.
"""
from __future__ import annotations
from typing import List, ClassVar, Pattern
import json, os, re
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser

# -------------------------------------------------------------------
class _Triplet:
    def __init__(self, subject: str, relation: str, object_: str):
        self.subject = subject
        self.relation = relation
        self.object = object_

    def __repr__(self):
        return f"<_Triplet {self.subject}-{self.relation}->{self.object}>"

# -------------------------------------------------------------------
class _JSONTripletParser(BaseOutputParser):
    """Nettoie le markdown ```json ... ``` puis parse le tableau de triplets."""
    FENCE_RE: ClassVar[Pattern[str]] = re.compile(r"```(?:json)?|```", re.IGNORECASE)

    # ----------------------------------------------------------------
    def _clean_fences(self, txt: str) -> str:
        txt = self.FENCE_RE.sub("", txt).strip()
        start, end = txt.find("["), txt.rfind("]") + 1
        return txt[start:end] if start != -1 else txt

    # ----------------------------------------------------------------
    def parse(self, text: str):
        raw = self._clean_fences(text)
        try:
            data = json.loads(raw)

            # ---- normalisation clé 'object' -> 'object_' --------------
            norm = []
            for t in data:
                if "object_" not in t and "object" in t:
                    t["object_"] = t.pop("object")
                norm.append(t)
            # -----------------------------------------------------------

            return [_Triplet(**t) for t in norm]

        except Exception as e:
            raise ValueError(f"Cannot parse triplets: {e}\n{raw}")

# -------------------------------------------------------------------
class GraphBuilder:
    # """Interface minimale attendue par KGBuilder.build_from_text."""
    # _PROMPT = PromptTemplate.from_template(
    #     """
    #     Tu es un expert en extraction d'information. À partir du passage suivant, extrait les relations sous
    #     forme de triplets JSON où chaque triplet possède *subject*, *relation*, *object*.

    #     Passage :\n\"\"\"{passage}\"\"\"\n

    #     Réponds uniquement avec un tableau JSON, sans commentaire ni explication.

    #     Exemple de sortie :
    #     [
    #     {{"subject": "Projet A", "relation": "LOCATED_IN", "object": "Casablanca"}}
    #     ]

    #     Note : LOCATED_IN est une relation parmi d'autres relations possibles
    #     """
    # )

    """
    Interface minimale attendue par KGBuilder.build_from_text.
    Cette version du prompt extrait des triplets variés (pas seulement LOCATED_IN),
    tolère un texte non structuré ou semi-structuré (JSON, liste à puces, phrases libres).
    """
    _PROMPT: PromptTemplate = PromptTemplate.from_template(
        """
        **Contexte**
        Tu es un moteur d’extraction de connaissances pour un Knowledge Graph
        sur l’immobilier (projets, biens, villes, équipements, contacts, prix, etc.).
        Le texte d’entrée peut être un bloc narratif, un pseudo-JSON ou un mélange.
        Ta tâche est d’identifier toutes les *relations sémantiquement pertinentes*,
        pas seulement la localisation.

        **Texte à analyser**
        « {passage} »

        **Règles de sortie**
        1. Produis **exclusivement** un tableau JSON, sans commentaire ;
           chaque élément est un objet ayant les clés `subject`, `relation`, `object`.
        2. Tous les libellés de relations sont en MAJUSCULES SnakeCase :
           - `LOCATED_IN`, `HAS_PRICE`, `HAS_EQUIPMENT`,  
           - `HAS_ROOM_COUNT`, `HAS_STANDING`, `HAS_CONTACT_PHONE`, etc.  
           Crée la relation la plus concise et sémantique ; si nécessaire, invente
           un libellé cohérent (en anglais, MAJUSCULE).
        3. **Subject** et **object** sont des chaînes « prêtes à nœud » :
           garde la casse d’origine et supprime guillemets/brackets inutiles.
        4. Pas de doublon ; un triplet = une information factuelle unique.
        5. Si aucune relation pertinente n’est détectée, renvoie `[]`.

        **Exemples**
        - Entrée : « Le projet *Al Abrar* est situé à Mediouna (Casablanca). »  
          Sortie : `[{{"subject":"Al Abrar","relation":"LOCATED_IN","object":"Mediouna"}}]`
        - Entrée : `{{"type":"Appartement F5","price":250000}}`  
          Sortie :  
          ```json
          [
            {{"subject":"Appartement F5","relation":"HAS_PRICE","object":"250000"}}
          ]
          ```
        - Entrée : « Le bien dispose d’un parking et d’un ascenseur. »  
          Sortie :  
          ```json
          [
            {{"subject":"Bien","relation":"HAS_EQUIPMENT","object":"Parking"}},
            {{"subject":"Bien","relation":"HAS_EQUIPMENT","object":"Ascenseur"}}
          ]
          ```

        **Production »**
        Génère maintenant la liste exhaustive des triplets détectés.
        """
    )

    # """
    # Interface minimale attendue par KGBuilder.build_from_text.
    # Chaque appel doit fournir un 'passage' qui peut être du texte libre,
    # du JSON partiel, ou un mélange des deux.
    # """

    # _PROMPT = PromptTemplate.from_template(
    #     """
    #     **Rôle**  
    #     Tu es un *extracteur expert* de connaissances structurées.
    #     Ton objectif est de parcourir le passage ci-dessous, d'en comprendre
    #     la signification implicite ou explicite, puis d'énumérer **toutes**
    #     les relations que l'on peut raisonnablement en déduire, sous forme
    #     de triplets ‹*subject*, *relation*, *object*›.

    #     **Règles de sortie**  
    #     1. Réponds avec **exclusivement** un tableau JSON valide, sans
    #        commentaire, sans markdown et sans ligne vide ; un élément par
    #        relation.  
    #     2. Les clés doivent être exactement `"subject"`, `"relation"`,
    #        `"object"`.  
    #     3. Les valeurs sont des chaînes **littérales** (pas de liste).  
    #     4. Le nom de la relation est un verbe ou groupe verbal en
    #        MAJUSCULES_SEPARÉ_PAR_DES_TIRETS_BAS décrivant la nature du lien
    #        (‘HAS_PRICE’, ‘HAS_ROOMS’, ‘OFFERS_EQUIPMENT’, ‘HAS_CONTACT_PHONE’,
    #        ‘LOCATED_IN’, ‘PART_OF_CITY’, etc.).  
    #     5. Génère **une relation par propriété ou fait** ; ne déduplique
    #        que si le triplet exact apparaît déjà dans la liste.  
    #     6. S'il manque une valeur dans le passage, ignore cette relation
    #        (ne pas inventer).  
    #     7. Respecte la casse des entités ; n’ajoute ni point final ni espace.  

    #     **Exemples de relations possibles** (non exhaustifs)  
    #     ─ Projet → Ville :              `LOCATED_IN`  
    #     ─ Projet → Quartier :           `LOCATED_IN`  
    #     ─ Projet → Type de bien :       `OFFERS_PROPERTY_TYPE`  
    #     ─ Type de bien → Prix :         `HAS_PRICE`  
    #     ─ Type de bien → Nombre de pièces : `HAS_ROOMS`  
    #     ─ Type de bien → Standing :     `HAS_STANDING`  
    #     ─ Type de bien → Équipement :   `HAS_EQUIPMENT`  
    #     ─ Projet → Téléphone contact :  `HAS_CONTACT_PHONE`  

    #     **Passage à analyser**  
    #     \"\"\"{passage}\"\"\"

    #     **Ta réponse (JSON uniquement)** :
    #     """
    # )


    def __init__(self, *, provider: str = "gemini", llm=None, **kwargs):
        """llm : objet LangChain LLM (ex. ChatOpenAI, ChatGoogleGenerativeAI…).
        S’il est None, on instancie ChatOpenAI avec OPENAI_API_KEY.
        """
        if llm is None:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(api_key=kwargs.get("api_key") or os.getenv("GOOGLE_API_KEY"),
                                            model=kwargs.get("model", "gemini-2.0-flash"),
                                            temperature=kwargs.get("temperature", 0))
        self.llm = llm
        self.parser = _JSONTripletParser()

    # ------------------------------------------------------------------
    def extract_relations(self, text: str) -> List[_Triplet]:
        print(f"Texte envoyé au LLM : {text}")
        prompt = self._PROMPT.format(passage=text)
        print(f"Prompt généré : {prompt}")
        response = self.llm.invoke(prompt) if callable(getattr(self.llm, "invoke", None)) else self.llm(prompt)
        txt = response.content if hasattr(response, "content") else str(response)
        print(f"Réponse du LLM : {txt}")
        return self.parser.parse(txt)