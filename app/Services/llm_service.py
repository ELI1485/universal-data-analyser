"""LLM service using strategy pattern for AI insight generation.

Supports Gemini (default) as the LLM provider. Generates analytical
insights in French based on dataset context.
"""

import logging
from typing import Optional

from config.settings import LLM_PROVIDER, GEMINI_API_KEY, LLM_MODEL, LLM_TEMPERATURE

logger = logging.getLogger(__name__)

_FALLBACK_MESSAGE = (
    "L'analyse par intelligence artificielle n'est pas disponible pour le moment. "
    "Veuillez réessayer ultérieurement ou vérifier la configuration de l'API."
)


class LLMService:
    """Service for generating AI-powered analytical insights.

    Uses the Gemini API (Google Generative AI) by default to generate
    French-language analytical insights from dataset statistics.
    """

    def __init__(self) -> None:
        """Initialize the LLM service based on configured provider."""
        self._model = None
        self._initialized = False

        provider = LLM_PROVIDER.lower()
        if provider == "gemini":
            self._init_gemini()
        else:
            logger.warning("Fournisseur LLM inconnu: '%s'. Utilisation de gemini.", provider)
            self._init_gemini()

    def _init_gemini(self) -> None:
        """Initialize the Google Gemini API client."""
        if not GEMINI_API_KEY or GEMINI_API_KEY == "your-gemini-api-key":
            logger.warning(
                "Clé API Gemini non configurée. Le service LLM sera indisponible."
            )
            return

        try:
            import google.generativeai as genai

            genai.configure(api_key=GEMINI_API_KEY)
            self._model = genai.GenerativeModel(
                model_name=LLM_MODEL,
                generation_config={
                    "temperature": LLM_TEMPERATURE,
                    "max_output_tokens": 1000,
                },
            )
            self._initialized = True
            logger.info("Service LLM Gemini initialisé avec modèle: %s", LLM_MODEL)
        except Exception as e:
            logger.error("Erreur d'initialisation du service Gemini: %s", e)
            self._initialized = False

    def generer_insights(self, context: dict) -> str:
        """Generate analytical insights from dataset context.

        Args:
            context: A dictionary containing dataset information:
                - dataset_name: Name of the dataset
                - nb_rows: Number of rows
                - nb_cols: Number of columns
                - stats_summary: Summary of descriptive statistics
                - anomalies_count: Total number of anomalies found
                - top_anomalies: List of most significant anomalies
                - correlations: Notable correlations between variables

        Returns:
            A French-language string containing the AI-generated insights,
            or a fallback message if the API is unavailable.
        """
        if not self._initialized or self._model is None:
            logger.warning("Service LLM non initialisé, retour du message par défaut.")
            return _FALLBACK_MESSAGE

        prompt = self._build_prompt(context)

        try:
            response = self._model.generate_content(prompt)
            if response and response.text:
                logger.info("Insights IA générés avec succès.")
                return response.text
            else:
                logger.warning("Réponse LLM vide.")
                return _FALLBACK_MESSAGE
        except Exception as e:
            logger.error("Erreur lors de la génération d'insights IA: %s", e)
            return _FALLBACK_MESSAGE

    def _build_prompt(self, context: dict) -> str:
        """Build a detailed French prompt for analytical insight generation.

        Args:
            context: The dataset context dictionary.

        Returns:
            A formatted prompt string in French.
        """
        dataset_name = context.get("dataset_name", "Dataset inconnu")
        nb_rows = context.get("nb_rows", "N/A")
        nb_cols = context.get("nb_cols", "N/A")
        stats_summary = context.get("stats_summary", "Non disponible")
        anomalies_count = context.get("anomalies_count", 0)
        top_anomalies = context.get("top_anomalies", [])
        correlations = context.get("correlations", [])

        # Format top anomalies
        anomalies_text = ""
        if top_anomalies:
            anomalies_items = []
            for a in top_anomalies[:10]:
                anomalies_items.append(
                    f"  - Colonne '{a.get('colonne', '?')}', "
                    f"Ligne {a.get('ligne', '?')}, "
                    f"Score: {a.get('score', '?'):.2f}, "
                    f"Algorithme: {a.get('type', '?')}"
                )
            anomalies_text = "\n".join(anomalies_items)
        else:
            anomalies_text = "  Aucune anomalie significative détectée."

        # Format correlations
        correlations_text = ""
        if correlations:
            corr_items = []
            for c in correlations[:10]:
                corr_items.append(
                    f"  - {c.get('col1', '?')} <-> {c.get('col2', '?')}: "
                    f"{c.get('value', 0):.3f}"
                )
            correlations_text = "\n".join(corr_items)
        else:
            correlations_text = "  Aucune corrélation notable identifiée."

        prompt = f"""Tu es un expert en analyse de données. Analyse les informations suivantes
et fournis un rapport d'insights en français, structuré et professionnel.

=== CONTEXTE DU DATASET ===
Nom: {dataset_name}
Nombre de lignes: {nb_rows}
Nombre de colonnes: {nb_cols}

=== RÉSUMÉ STATISTIQUE ===
{stats_summary}

=== ANOMALIES DÉTECTÉES ({anomalies_count} au total) ===
{anomalies_text}

=== CORRÉLATIONS NOTABLES ===
{correlations_text}

=== INSTRUCTIONS ===
Fournis un rapport structuré avec les sections suivantes:

1. **Résumé Exécutif** (2-3 phrases résumant les principales conclusions)
2. **Constats Clés** (3-5 points importants observés dans les données)
3. **Anomalies et Risques** (interprétation des anomalies détectées)
4. **Recommandations** (3-5 actions concrètes basées sur l'analyse)

Sois concis, professionnel et oriente tes recommandations vers la prise de décision.
Réponds uniquement en français.
"""
        return prompt

    def test_connection(self) -> bool:
        """Test if the LLM API connection is working.

        Returns:
            True if the API responds successfully, False otherwise.
        """
        if not self._initialized or self._model is None:
            return False

        try:
            response = self._model.generate_content("Dis 'OK' en un mot.")
            return response is not None and response.text is not None
        except Exception as e:
            logger.error("Test de connexion LLM échoué: %s", e)
            return False
