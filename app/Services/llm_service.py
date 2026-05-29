"""LLM service using OpenAI-compatible client for Groq insight generation.

Supports Groq as the LLM provider (using Llama 3). Generates analytical
insights in French based on dataset context.

This module is deliberately verbose with its error reporting: when the
service is unavailable, the precise reason is captured on the instance 
and surfaced through the public API.
"""

from __future__ import annotations

import logging

from config.settings import (
    LLM_PROVIDER,
    GROQ_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
)

logger = logging.getLogger(__name__)


class LLMUnavailableError(RuntimeError):
    """Raised internally when an LLM call cannot be made."""


class LLMService:
    """Service for generating AI-powered analytical insights.

    Uses the OpenAI Python client configured for Groq to generate
    French-language analytical insights from dataset statistics.
    """

    def __init__(self) -> None:
        """Initialize the LLM service."""
        self._client = None
        self._initialized = False
        self._last_error: str = ""

        provider = (LLM_PROVIDER or "groq").lower().strip()
        if provider != "groq":
            logger.warning(
                "Fournisseur LLM inconnu: '%s'. Utilisation de groq.", provider
            )
        self._init_groq()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------
    def _init_groq(self) -> None:
        """Initialize the OpenAI client for Groq.

        On failure the precise reason is recorded in ``self._last_error``.
        """
        # 1. Check for the API key
        if not GROQ_API_KEY or GROQ_API_KEY.strip() in (
            "",
            "votre_cle_api_groq_ici",
        ):
            self._last_error = (
                "Clé API Groq manquante. Définissez GROQ_API_KEY "
                "dans le fichier .env."
            )
            logger.warning("Service LLM non initialisé: %s", self._last_error)
            return

        # 2. Check the SDK is installed
        try:
            import openai
        except ImportError as e:
            self._last_error = (
                "Module 'openai' introuvable. Installez-le avec "
                "`pip install openai` "
                f"(detail: {e})."
            )
            logger.error("Service LLM non initialisé: %s", self._last_error)
            return

        # 3. Configure the SDK
        try:
            self._client = openai.OpenAI(
                api_key=GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1",
            )
            self._initialized = True
            self._last_error = ""
            logger.info(
                "Service LLM Groq initialisé avec modèle: %s", LLM_MODEL
            )
        except Exception as e:
            self._last_error = (
                f"Échec d'initialisation du client OpenAI pour Groq: "
                f"{type(e).__name__}: {e}"
            )
            logger.error("Service LLM non initialisé: %s", self._last_error)
            self._initialized = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def is_available(self) -> bool:
        """``True`` when a Groq call can be attempted."""
        return self._initialized and self._client is not None

    @property
    def last_error(self) -> str:
        """The most recent init or call error, or an empty string."""
        return self._last_error

    def generer_insights(self, context: dict) -> str:
        """Generate analytical insights from a dataset context.

        Args:
            context: A dictionary with dataset stats.

        Returns:
            A French-language string with the AI insights, or a fallback message.
        """
        if not self.is_available:
            return self._fallback_message()

        prompt = self._build_prompt(context)

        try:
            response = self._client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "Tu es un expert en analyse de données. Réponds uniquement en français de manière professionnelle et structurée."},
                    {"role": "user", "content": prompt}
                ],
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS,
            )
            
            content = response.choices[0].message.content
            if content:
                logger.info("Insights IA générés avec succès via Groq.")
                return content

            self._last_error = "La réponse de Groq est vide."
            logger.warning(self._last_error)
            return self._fallback_message()
            
        except Exception as e:
            self._last_error = (
                f"Erreur lors de l'appel Groq API: {type(e).__name__}: {e}"
            )
            logger.error(self._last_error)
            return self._fallback_message()

    def generer_rapport_html(self, context: dict) -> str:
        """Generate a full HTML report from a dataset context.

        Args:
            context: A dictionary with dataset stats.

        Returns:
            A string containing the AI-generated HTML report.
        """
        if not self.is_available:
            return f"<h1>Erreur</h1><p>{self._fallback_message()}</p>"

        prompt = self._build_html_prompt(context)

        try:
            # We allow more tokens for a full HTML report
            response = self._client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "Tu es un data scientist expert. Réponds UNIQUEMENT avec du code HTML valide. Ne mets pas de balises Markdown (comme ```html)."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2, # Lower temp for strict structural adherence
                max_tokens=4000,
            )
            
            content = response.choices[0].message.content
            if content:
                # Strip markdown blocks if the LLM ignores instructions
                content = content.replace("```html", "").replace("```", "").strip()
                logger.info("Rapport HTML généré avec succès via Groq.")
                return content

            self._last_error = "La réponse de Groq est vide."
            logger.warning(self._last_error)
            return f"<h1>Erreur</h1><p>{self._last_error}</p>"
            
        except Exception as e:
            self._last_error = (
                f"Erreur lors de l'appel Groq API (HTML): {type(e).__name__}: {e}"
            )
            logger.error(self._last_error)
            return f"<h1>Erreur</h1><p>{self._last_error}</p>"

    def test_connection(self) -> tuple[bool, str] :
        """Test the Groq API connection.

        Returns:
            ``(True, "")`` when the call succeeds, otherwise
            ``(False, error_message)`` with a French-language reason.
        """
        if not self.is_available:
            return False, self._last_error or "Service LLM non initialisé."

        try:
            response = self._client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": "Dis 'OK' en un mot."}],
                max_tokens=10,
            )
            content = response.choices[0].message.content
            if content:
                return True, ""
            
            self._last_error = "Réponse vide du modèle Groq."
            return False, self._last_error
            
        except Exception as e:
            self._last_error = (
                f"Échec du test de connexion Groq: {type(e).__name__}: {e}"
            )
            logger.error(self._last_error)
            return False, self._last_error

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _fallback_message(self) -> str:
        """Compose the user-visible French fallback message."""
        reason = self._last_error or "raison inconnue"
        return (
            "L'analyse par intelligence artificielle n'est pas disponible "
            f"pour le moment. Detail: {reason}"
        )

    def _build_prompt(self, context: dict) -> str:
        """Build a detailed French prompt for analytical insight generation."""
        dataset_name = context.get("dataset_name", "Dataset inconnu")
        nb_rows = context.get("nb_rows", "N/A")
        nb_cols = context.get("nb_cols", "N/A")
        stats_summary = context.get("stats_summary", "Non disponible")
        anomalies_count = context.get("anomalies_count", 0)
        top_anomalies = context.get("top_anomalies", [])
        correlations = context.get("correlations", [])

        # Format top anomalies
        if top_anomalies:
            anomalies_items = []
            for a in top_anomalies[:10]:
                anomalies_items.append(
                    f"  - Colonne '{a.get('colonne', '?')}', "
                    f"Ligne {a.get('ligne', '?')}, "
                    f"Score: {a.get('score', 0):.2f}, "
                    f"Algorithme: {a.get('type', '?')}"
                )
            anomalies_text = "\n".join(anomalies_items)
        else:
            anomalies_text = "  Aucune anomalie significative detectee."

        # Format correlations
        if correlations:
            corr_items = []
            for c in correlations[:10]:
                corr_items.append(
                    f"  - {c.get('col1', '?')} <-> {c.get('col2', '?')}: "
                    f"{c.get('value', 0):.3f}"
                )
            correlations_text = "\n".join(corr_items)
        else:
            correlations_text = "  Aucune correlation notable identifiee."

        return f"""Analyse les informations suivantes et fournis un rapport d'insights en francais, structure et professionnel.

=== CONTEXTE DU DATASET ===
Nom: {dataset_name}
Nombre de lignes: {nb_rows}
Nombre de colonnes: {nb_cols}

=== RESUME STATISTIQUE ===
{stats_summary}

=== ANOMALIES DETECTEES ({anomalies_count} au total) ===
{anomalies_text}

=== CORRELATIONS NOTABLES ===
{correlations_text}

=== INSTRUCTIONS ===
Fournis un rapport structure avec les sections suivantes:

1. **Resume Executif** (2-3 phrases resumant les principales conclusions)
2. **Constats Cles** (3-5 points importants observes dans les donnees)
3. **Anomalies et Risques** (interpretation des anomalies detectees)
4. **Recommandations** (3-5 actions concretes basees sur l'analyse)

Sois concis, professionnel et oriente tes recommandations vers la prise de decision.
"""

    def _build_html_prompt(self, context: dict) -> str:
        """Build a detailed prompt specifically requesting HTML output."""
        dataset_name = context.get("dataset_name", "Dataset inconnu")
        nb_rows = context.get("nb_rows", "N/A")
        nb_cols = context.get("nb_cols", "N/A")
        stats_summary = context.get("stats_summary", "Non disponible")
        anomalies_count = context.get("anomalies_count", 0)
        
        # Inject chart placeholders (these will be replaced by the PDF generator)
        # Note: We tell the AI to include these specific tags so we can swap them out later if needed,
        # or we just let the AI format the text and we append charts manually.
        # Actually, xhtml2pdf handles standard <img src="file:///...">. We will just tell the AI to structure the data.

        return f"""Analyse les statistiques suivantes et génère un rapport complet au format HTML.

=== CONTEXTE DU DATASET ===
Nom: {dataset_name}
Lignes: {nb_rows} | Colonnes: {nb_cols}

=== RESUME STATISTIQUE ===
{stats_summary}

=== ANOMALIES DETECTEES ({anomalies_count} au total) ===
(Voir les tableaux dans le rapport PDF pour le détail)

=== INSTRUCTIONS ===
1. Génère un document HTML complet avec les balises <html>, <head>, et <body>.
2. Dans le <head>, inclus un bloc <style> avec CSS pour un design professionnel, moderne et propre (utilise des polices sans-serif comme Arial ou Helvetica, des couleurs professionnelles comme le bleu marine #1a237e).
3. Le <body> doit contenir:
   - Un titre principal <h1>
   - Une section "Résumé Exécutif"
   - Une section "Analyse de la Qualité des Données" (basé sur le nombre de lignes et les statistiques)
   - Une section "Insights Clés et Tendances"
   - Une section "Conclusion et Recommandations"
4. Utilise des tableaux HTML (<table>, <tr>, <td>) si tu veux résumer des chiffres importants.
5. NE RÉPONDS QU'AVEC DU CODE HTML. AUCUN TEXTE AVANT OU APRÈS LE CODE HTML.
"""
