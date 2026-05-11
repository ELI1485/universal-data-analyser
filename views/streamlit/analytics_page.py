"""Streamlit analytics page for running and viewing analyses."""

import pandas as pd
import streamlit as st

from controllers.analytics_controller import AnalyticsController
from controllers.upload_controller import UploadController
from services.llm_service import LLMService
from services.visualization.visualization_service import (
    histogramme,
    heatmap_correlation,
    boxplot,
    anomalies_chart,
    courbe_tendance,
)

_analytics_ctrl = AnalyticsController()
_upload_ctrl = UploadController()


def render(user_id: int, role: str) -> None:
    """Render the analytics page with dataset selection and analysis results.

    Args:
        user_id: Current user's ID.
        role: Current user's role.
    """
    st.markdown("## 📈 Analyses")
    st.markdown("---")

    # Dataset selector
    try:
        datasets = _upload_ctrl.lister_datasets(user_id, role)
    except Exception as e:
        st.error(f"Erreur chargement datasets: {e}")
        return

    if not datasets:
        st.info("Aucun dataset disponible. Importez d'abord un fichier de données.")
        return

    dataset_options = {f"{ds.nom} (ID: {ds.id})": ds.id for ds in datasets}
    selected_label = st.selectbox("Sélectionnez un dataset", list(dataset_options.keys()))
    selected_id = dataset_options[selected_label]

    # Run analysis button
    if st.button("🚀 Lancer l'analyse complète", use_container_width=True):
        try:
            with st.spinner("Analyse en cours (statistiques, anomalies, clustering)..."):
                results = _analytics_ctrl.executer_analyses(selected_id, user_id)
                st.session_state["analysis_results"] = results
                st.session_state["analysis_dataset_id"] = selected_id
            st.success("✅ Analyse terminée avec succès!")
        except Exception as e:
            st.error(f"❌ Erreur lors de l'analyse: {str(e)}")
            return

    # Display results if available
    if (
        "analysis_results" in st.session_state
        and st.session_state.get("analysis_dataset_id") == selected_id
    ):
        results = st.session_state["analysis_results"]
        analytics = results.get("analytics", {})
        anomalies = results.get("anomalies", {})

        _display_results(analytics, anomalies, selected_id)


def _display_results(analytics: dict, anomalies: dict, dataset_id: int) -> None:
    """Display analysis results in tabs.

    Args:
        analytics: Analytics results dictionary.
        anomalies: Anomaly detection results.
        dataset_id: The analyzed dataset's ID.
    """
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Statistiques", "📉 Visualisations", "⚠️ Anomalies", "🤖 Insights IA"]
    )

    # Tab 1: Statistics
    with tab1:
        _render_statistics_tab(analytics)

    # Tab 2: Visualizations
    with tab2:
        _render_visualizations_tab(analytics, dataset_id)

    # Tab 3: Anomalies
    with tab3:
        _render_anomalies_tab(anomalies)

    # Tab 4: AI Insights
    with tab4:
        _render_insights_tab(analytics, anomalies, dataset_id)


def _render_statistics_tab(analytics: dict) -> None:
    """Render the statistics tab content."""
    st.markdown("### Statistiques descriptives")

    # KPI cards
    kpis = analytics.get("kpis", {})
    if kpis:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Lignes", kpis.get("total_rows", "N/A"))
        with col2:
            st.metric("Colonnes", kpis.get("total_columns", "N/A"))
        with col3:
            st.metric("Complétude", f"{kpis.get('completeness_rate', 0):.1f}%")
        with col4:
            st.metric("Mémoire", f"{kpis.get('memory_usage_mb', 0):.2f} Mo")

    # Statistics table
    stats_data = analytics.get("statistiques", {}).get("colonnes", {})
    if stats_data:
        st.markdown("#### Détails par colonne")
        df_stats = pd.DataFrame(stats_data).T
        st.dataframe(df_stats, use_container_width=True)

    # Top correlations
    top_pairs = kpis.get("top_correlated_pairs", [])
    if top_pairs:
        st.markdown("#### Corrélations fortes (>0.7)")
        corr_df = pd.DataFrame(top_pairs)
        st.dataframe(corr_df, use_container_width=True)


def _render_visualizations_tab(analytics: dict, dataset_id: int) -> None:
    """Render the visualizations tab with interactive charts."""
    st.markdown("### Visualisations interactives")

    # Load data for charts
    from repositories.dataset_repository import DatasetRepository
    _ds_repo = DatasetRepository()
    dataset = _ds_repo.find_by_id(dataset_id)

    if not dataset:
        st.warning("Dataset introuvable.")
        return

    try:
        df = pd.read_csv(dataset.chemin_fichier, encoding="utf-8")
    except Exception as e:
        st.warning(f"Impossible de charger les données: {e}")
        return

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if not numeric_cols:
        st.info("Aucune colonne numérique pour les visualisations.")
        return

    # Histogram
    st.markdown("#### Histogramme")
    hist_col = st.selectbox("Colonne", numeric_cols, key="hist_col")
    if hist_col:
        fig = histogramme(df, hist_col)
        st.plotly_chart(fig, use_container_width=True)

    # Correlation heatmap
    if len(numeric_cols) >= 2:
        st.markdown("#### Matrice de corrélation")
        fig_corr = heatmap_correlation(df)
        st.plotly_chart(fig_corr, use_container_width=True)

    # Boxplot
    st.markdown("#### Boîte à moustaches")
    box_col = st.selectbox("Colonne", numeric_cols, key="box_col")
    if box_col:
        fig_box = boxplot(df, box_col)
        st.plotly_chart(fig_box, use_container_width=True)


def _render_anomalies_tab(anomalies: dict) -> None:
    """Render the anomalies tab with filtering."""
    st.markdown("### Anomalies détectées")

    total = anomalies.get("total", 0)
    resume = anomalies.get("resume", {})

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total", total)
    with col2:
        st.metric("Z-Score", resume.get("zscore_count", 0))
    with col3:
        st.metric("IQR", resume.get("iqr_count", 0))
    with col4:
        st.metric("Isolation Forest", resume.get("isolation_count", 0))

    # Filter by algorithm
    algo_filter = st.selectbox(
        "Filtrer par algorithme",
        ["Tous", "zscore", "iqr", "isolation_forest"],
    )

    # Combine all anomalies
    all_anomalies = (
        anomalies.get("zscore", [])
        + anomalies.get("iqr", [])
        + anomalies.get("isolation", [])
    )

    if algo_filter != "Tous":
        all_anomalies = [a for a in all_anomalies if a.get("type") == algo_filter]

    all_anomalies.sort(key=lambda x: x.get("score", 0), reverse=True)

    if all_anomalies:
        df_anom = pd.DataFrame(all_anomalies[:200])
        st.dataframe(df_anom, use_container_width=True)

        # Anomalies chart
        fig = anomalies_chart(all_anomalies)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune anomalie détectée avec ce filtre.")


def _render_insights_tab(analytics: dict, anomalies: dict, dataset_id: int) -> None:
    """Render the AI insights tab."""
    st.markdown("### 🤖 Insights IA (Gemini)")

    if st.button("Générer des insights IA"):
        try:
            with st.spinner("Génération des insights par IA en cours..."):
                from repositories.dataset_repository import DatasetRepository
                _ds_repo = DatasetRepository()
                dataset = _ds_repo.find_by_id(dataset_id)

                llm = LLMService()

                # Build context
                stats_data = analytics.get("statistiques", {}).get("colonnes", {})
                stats_summary = ""
                for col_name, col_stats in list(stats_data.items())[:5]:
                    stats_summary += (
                        f"  {col_name}: moy={col_stats.get('mean')}, "
                        f"med={col_stats.get('median')}, std={col_stats.get('std')}\n"
                    )

                all_anom = (
                    anomalies.get("zscore", [])
                    + anomalies.get("iqr", [])
                    + anomalies.get("isolation", [])
                )
                all_anom.sort(key=lambda x: x.get("score", 0), reverse=True)

                kpis = analytics.get("kpis", {})

                context = {
                    "dataset_name": dataset.nom if dataset else "Inconnu",
                    "nb_rows": dataset.nb_lignes if dataset else 0,
                    "nb_cols": dataset.nb_colonnes if dataset else 0,
                    "stats_summary": stats_summary,
                    "anomalies_count": anomalies.get("total", 0),
                    "top_anomalies": all_anom[:5],
                    "correlations": kpis.get("top_correlated_pairs", []),
                }

                insights = llm.generer_insights(context)
                st.session_state["ai_insights"] = insights

            st.success("Insights générés!")

        except Exception as e:
            st.error(f"Erreur: {e}")

    # Display insights
    if "ai_insights" in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state["ai_insights"])
