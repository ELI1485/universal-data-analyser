"""LLM service using strategy pattern for AI insight generation.

Supports Gemini (default) as the LLM provider. Generates analytical
insights in French based on dataset context.

This module is deliberately verbose with its error reporting: when the
service is unavailable, the precise reason (missing API key, missing
``google-generativeai`` package, model rejected, network error, etc.)
is captured on the instance and surfaced through the public API. The
old behaviour of swallowing all errors behind a generic French message
hid actionable diagnostics.
"""

from __future__ import annotations

import logging

from config.settings import (
    LLM_PROVIDER,
    GEMINI_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
)

logger = logging.getLogger(__name__)


class LLMUnavailableError(RuntimeError):
    """Raised internally when an LLM call cannot be made.

    The string representation is suitable for showing to operators and
    contains the real underlying cause (missing key, missing module,
    invalid model, etc.).
    """


class LLMService:
    """Service for generating AI-powered analytical insights.

    Uses the Gemini API (Google Generative AI) by default to generate
    French-language analytical insights from dataset statistics.

    Public surface:
        - ``generer_insights(context)`` -> str. Returns either the LLM
          output or, when the service is unavailable, a clear French
          fallback message that **includes the real reason** so it can
          be debugged from the UI/logs.
        - ``test_connection()`` -> tuple[bool, str]. Returns
          ``(success, error_message)``. ``error_message`` is empty
          when the connection succeeds.
        - ``is_available`` (property) -> bool.
        - ``last_error`` (property) -> str. The latest captured init or
          call error, or an empty string when none.
    """

    def __init__(self) -> None:
        """Initialize the LLM service based on the configured provider."""
        self._model = None
        self._initialized = False
        self._last_error: str = ""

        provider = (LLM_PROVIDER or "gemini").lower().strip()
        if provider != "gemini":
            logger.warning(
                "Fournisseur LLM inconnu: '%s'. Utilisation de gemini.", provider
            )
        self._init_gemini()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------
    def _init_gemini(self) -> None:
        """Initialize the Google Gemini API client.

        On failure the precise reason is recorded in ``self._last_error``
        rather than being silently swallowed.
        """
        # 1. Check for the API key
        if not GEMINI_API_KEY or GEMINI_API_KEY.strip() in (
            "",
            "your-gemini-api-key",
            "your-api-key",
        ):
            self._last_error = (
                "Cle API Gemini manquante. Definissez GEMINI_API_KEY "
                "(ou GOOGLE_API_KEY) dans le fichier .env."
            )
            logger.warning("Service LLM non initialise: %s", self._last_error)
            return

        # 2. Check the SDK is installed
        try:
            import google.generativeai as genai  # type: ignore[import-not-found]
        except ImportError as e:
            self._last_error = (
                "Module 'google-generativeai' introuvable. Installez-le avec "
                "`pip install google-generativeai>=0.7.0` "
                f"(detail: {e})."
            )
            logger.error("Service LLM non initialise: %s", self._last_error)
            return
        except Exception as e:  # pragma: no cover - defensive
            self._last_error = f"Erreur d'import google-generativeai: {e}"
            logger.error("Service LLM non initialise: %s", self._last_error)
            return

        # 3. Configure the SDK and instantiate the model
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            self._model = genai.GenerativeModel(
                model_name=LLM_MODEL,
                generation_config={
                    "temperature": LLM_TEMPERATURE,
                    "max_output_tokens": LLM_MAX_TOKENS,
                },
            )
            self._initialized = True
            self._last_error = ""
            logger.info(
                "Service LLM Gemini initialise avec modele: %s", LLM_MODEL
            )
        except Exception as e:
            self._last_error = (
                f"Echec d'initialisation du modele Gemini '{LLM_MODEL}': "
                f"{type(e).__name__}: {e}"
            )
            logger.error("Service LLM non initialise: %s", self._last_error)
            self._initialized = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def is_available(self) -> bool:
        """``True`` when a Gemini call can be attempted."""
        return self._initialized and self._model is not None

    @property
    def last_error(self) -> str:
        """The most recent init or call error, or an empty string."""
        return self._last_error

    def generer_insights(self, context: dict) -> str:
        """Generate analytical insights from a dataset context.

        Args:
            context: A dictionary with at least:
                - ``dataset_name``, ``nb_rows``, ``nb_cols``
                - ``stats_summary``, ``anomalies_count``, ``top_anomalies``
                - ``correlations``

        Returns:
            A French-language string with the AI insights, or — when the
            service is unavailable — a fallback message that **includes
            the real reason** so the bug can be debugged.
        """
        if not self.is_available:
            return self._fallback_message()

        prompt = self._build_prompt(context)

        try:
            response = self._model.generate_content(prompt)  # type: ignore[union-attr]
            if response and getattr(response, "text", None):
                logger.info("Insights IA generes avec succes.")
                return response.text

            self._last_error = (
                "La reponse de Gemini est vide. Verifiez les filtres de "
                "securite ou le quota du modele."
            )
            logger.warning(self._last_error)
            return self._fallback_message()
        except Exception as e:
            self._last_error = (
                f"Erreur lors de l'appel Gemini: {type(e).__name__}: {e}"
            )
            logger.error(self._last_error)
            return self._fallback_message()

    def test_connection(self) -> tuple[bool, str]:
        """Test the Gemini API connection.

        Returns:
            ``(True, "")`` when the call succeeds, otherwise
            ``(False, error_message)`` with a French-language reason.
        """
        if not self.is_available:
            return False, self._last_error or "Service LLM non initialise."

        try:
            response = self._model.generate_content("Dis 'OK' en un mot.")  # type: ignore[union-attr]
            if response is not None and getattr(response, "text", None):
                return True, ""
            self._last_error = "Reponse vide du modele Gemini."
            return False, self._last_error
        except Exception as e:
            self._last_error = (
                f"Echec du test de connexion Gemini: {type(e).__name__}: {e}"
            )
            logger.error(self._last_error)
            return False, self._last_error

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _fallback_message(self) -> str:
        """Compose the user-visible French fallback message.

        Always includes the real reason so the operator can debug — this
        is the explicit fix for the silent failure described in the bug
        report.
        """
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

        return f"""Tu es un expert en analyse de donnees. Analyse les informations suivantes
et fournis un rapport d'insights en francais, structure et professionnel.

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
Reponds uniquement en francais.
"""
