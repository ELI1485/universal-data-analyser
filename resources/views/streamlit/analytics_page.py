"""Streamlit analytics page for running and viewing analyses."""

import os

import pandas as pd
import streamlit as st

from app.Http.Controllers.analytics_controller import AnalyticsController
from app.Http.Controllers.upload_controller import UploadController
from app.Services.llm_service import LLMService
from app.Services.visualization.visualization_service import (
    histogramme,
    heatmap_correlation,
    boxplot,
    anomalies_chart,
    bar_categorical_frequency,
    pie_categorical,
)
from resources.views.streamlit.style_utils import render_metric_card

_analytics_ctrl = AnalyticsController()
_upload_ctrl = UploadController()


def render(user_id: int, role: str) -> None:
    """Render the analytics page with dataset selection and analysis results.

    Args:
        user_id: Current user's ID.
        role: Current user's role.
    """
    st.markdown(
        "<h2 style='display: flex; align-items: center; gap: 10px;'>"
        "<i class='fa-solid fa-magnifying-glass-chart'></i> Analyses</h2>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # Dataset selector
    try:
        datasets = _upload_ctrl.lister_datasets(user_id, role)
    except Exception as e:
        st.error(f"Erreur chargement datasets: {e}")
        return

    if not datasets:
        st.info("Aucun dataset disponible. Importez d'abord un fichier de donnees.")
        return

    dataset_options = {f"{ds.nom} (ID: {ds.id})": ds.id for ds in datasets}
    selected_label = st.selectbox("Selectionnez un dataset", list(dataset_options.keys()))
    selected_id = dataset_options[selected_label]

    # Apercu des donnees : permet de verifier le contenu avant de lancer
    # une analyse complete (evite de perdre du temps sur des donnees erronees).
    with st.expander("Apercu des donnees (10 premieres lignes)", expanded=False):
        from app.Repositories.dataset_repository import DatasetRepository

        _ds_repo = DatasetRepository()
        dataset = _ds_repo.find_by_id(selected_id)
        if dataset and os.path.exists(dataset.chemin_fichier):
            try:
                if str(dataset.chemin_fichier).lower().endswith((".xlsx", ".xls")):
                    preview_df = pd.read_excel(dataset.chemin_fichier, nrows=10)
                else:
                    preview_df = pd.read_csv(dataset.chemin_fichier, nrows=10)
                st.dataframe(preview_df, use_container_width=True)
                st.caption(f"Affichage de 10 lignes sur {dataset.nb_lignes}")
            except Exception as e:
                st.warning(f"Impossible de lire l'apercu: {e}")
        else:
            st.warning("Fichier introuvable. Veuillez re-importer le dataset.")

    if st.button(
        "Lancer l'analyse complete",
        use_container_width=True,
        icon=":material/rocket_launch:",
    ):
        try:
            with st.spinner("Analyse en cours (statistiques, anomalies, clustering)..."):
                results = _analytics_ctrl.executer_analyses(selected_id, user_id)
                st.session_state["analysis_results"] = results
                st.session_state["analysis_dataset_id"] = selected_id
            st.success("Analyse terminee avec succes.")
        except Exception as e:
            st.error(f"Erreur lors de l'analyse: {str(e)}")
            return

    if (
        "analysis_results" in st.session_state
        and st.session_state.get("analysis_dataset_id") == selected_id
    ):
        results = st.session_state["analysis_results"]
        analytics = results.get("analytics", {})
        anomalies = results.get("anomalies", {})

        _display_results(analytics, anomalies, selected_id)


def _display_results(analytics: dict, anomalies: dict, dataset_id: int) -> None:
    """Display analysis results in tabs."""
    # Inject custom CSS for tabs
    st.markdown("""
        <style>
        /* Add spacing and custom styling to Streamlit tabs */
        div[data-baseweb="tab-list"] {
            gap: 20px;
            margin-bottom: 10px;
        }
        button[data-baseweb="tab"] {
            font-size: 16px !important;
            font-weight: 500 !important;
            padding: 10px 15px !important;
            border-radius: 6px 6px 0 0 !important;
            transition: all 0.3s ease;
        }
        button[data-baseweb="tab"]:hover {
            background-color: rgba(147, 220, 92, 0.1) !important;
            color: #93DC5C !important;
        }
        
        /* FontAwesome CSS Icons for Tabs */
        button[data-baseweb="tab"] div[data-testid="stMarkdownContainer"] p::before {
            font-family: "Font Awesome 6 Free";
            font-weight: 900;
            margin-right: 8px;
            color: #93DC5C;
        }
        /* Tab 1: Statistiques */
        button[data-baseweb="tab"]:nth-child(1) div[data-testid="stMarkdownContainer"] p::before {
            content: "\\f080";
        }
        /* Tab 2: Visualisations */
        button[data-baseweb="tab"]:nth-child(2) div[data-testid="stMarkdownContainer"] p::before {
            content: "\\f201";
        }
        /* Tab 3: Anomalies */
        button[data-baseweb="tab"]:nth-child(3) div[data-testid="stMarkdownContainer"] p::before {
            content: "\\f071";
        }
        /* Tab 4: Correlations */
        button[data-baseweb="tab"]:nth-child(4) div[data-testid="stMarkdownContainer"] p::before {
            content: "\\f0c1";
        }
        /* Tab 5: Insights IA */
        button[data-baseweb="tab"]:nth-child(5) div[data-testid="stMarkdownContainer"] p::before {
            content: "\\f544";
        }
        </style>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Statistiques", 
        "Visualisations", 
        "Anomalies", 
        "Corrélations", 
        "Insights IA"
    ])

    with tab1:
        _render_statistics_tab(analytics)
    with tab2:
        _render_visualizations_tab(analytics, dataset_id)
    with tab3:
        _render_anomalies_tab(anomalies)
    with tab4:
        _render_correlations_tab(analytics, dataset_id)
    with tab5:
        _render_insights_tab(analytics, anomalies, dataset_id)


# ---------------------------------------------------------------------------
# Statistics tab
# ---------------------------------------------------------------------------
def _render_statistics_tab(analytics: dict) -> None:
    """Render the statistics tab content."""
    st.markdown("### Statistiques descriptives")

    # Multi-sheet (Excel) breakdown, when the import combined several feuilles.
    sheet_breakdown = analytics.get("sheet_breakdown") or {}
    if len(sheet_breakdown) > 1:
        noms = ", ".join(sheet_breakdown.keys())
        st.info(
            f"Ce fichier contient **{len(sheet_breakdown)} feuilles**: {noms}"
        )
        breakdown_df = pd.DataFrame(
            [
                {
                    "Feuille": nom,
                    "Lignes": infos.get("nb_lignes", 0),
                    "Colonnes": infos.get("nb_colonnes", 0),
                }
                for nom, infos in sheet_breakdown.items()
            ]
        )
        st.dataframe(breakdown_df, use_container_width=True, hide_index=True)

    kpis = analytics.get("kpis", {})
    if kpis:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            render_metric_card(
                "Total Lignes", str(kpis.get("total_rows", "N/A")), "fa-solid fa-list"
            )
        with col2:
            render_metric_card(
                "Total Colonnes", str(kpis.get("total_columns", "N/A")),
                "fa-solid fa-table-columns",
            )
        with col3:
            render_metric_card(
                "Completude", f"{kpis.get('completeness_rate', 0):.1f}%",
                "fa-solid fa-check-double",
            )
        with col4:
            render_metric_card(
                "Memoire", f"{kpis.get('memory_usage_mb', 0):.2f} Mo",
                "fa-solid fa-microchip",
            )

    stats = analytics.get("statistiques", {})
    cols_stats = stats.get("colonnes", {})

    # Split numeric vs categorical columns and render each in its own table
    numeric_rows = {}
    categorical_rows = {}
    for col_name, col_stats in cols_stats.items():
        kind = col_stats.get("_kind", "numeric")
        clean = {k: v for k, v in col_stats.items() if k != "_kind"}
        if kind == "categorical":
            # Drop the heavy nested "top_values" lists for the table view
            clean.pop("top_values", None)
            clean.pop("top_values_pct", None)
            categorical_rows[col_name] = clean
        else:
            numeric_rows[col_name] = clean

    if numeric_rows:
        st.markdown(
            "<h4><i class='fa-solid fa-calculator'></i> Colonnes numeriques</h4>",
            unsafe_allow_html=True,
        )
        st.dataframe(pd.DataFrame(numeric_rows).T, use_container_width=True)

    if categorical_rows:
        st.markdown(
            "<h4><i class='fa-solid fa-list-ul'></i> Colonnes categorielles</h4>",
            unsafe_allow_html=True,
        )
        st.dataframe(pd.DataFrame(categorical_rows).T, use_container_width=True)

    if not numeric_rows and not categorical_rows:
        st.info("Aucune statistique a afficher.")

    # Top correlations
    top_pairs = kpis.get("top_correlated_pairs", [])
    if top_pairs:
        st.markdown(
            "<h4><i class='fa-solid fa-link'></i> Correlations fortes (>0.7)</h4>",
            unsafe_allow_html=True,
        )
        st.dataframe(pd.DataFrame(top_pairs), use_container_width=True)


# ---------------------------------------------------------------------------
# Visualisations tab
# ---------------------------------------------------------------------------
def _render_visualizations_tab(analytics: dict, dataset_id: int) -> None:
    """Render the visualizations tab with interactive charts.

    Supports both numeric data (histogram, heatmap, boxplot) and
    categorical data (frequency bar chart, donut chart). When the
    dataset has no numeric columns the page still renders categorical
    charts instead of bailing out with a generic warning.
    """
    st.markdown("### Visualisations interactives")

    from app.Repositories.dataset_repository import DatasetRepository
    _ds_repo = DatasetRepository()
    dataset = _ds_repo.find_by_id(dataset_id)

    if not dataset:
        st.warning("Dataset introuvable.")
        return

    try:
        df = pd.read_csv(dataset.chemin_fichier, encoding="utf-8")
    except Exception as e:
        st.warning(f"Impossible de charger les donnees: {e}")
        return

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(
        include=["object", "category", "string", "bool"]
    ).columns.tolist()

    if not numeric_cols and not categorical_cols:
        st.info("Aucune colonne exploitable pour les visualisations.")
        return

    # ── Numeric visualisations ──
    if numeric_cols:
        st.markdown(
            "<h4><i class='fa-solid fa-chart-column'></i> Donnees numeriques</h4>",
            unsafe_allow_html=True,
        )

        # Histogram
        hist_col = st.selectbox(
            "Colonne pour l'histogramme", numeric_cols, key="vis_hist_col"
        )
        if hist_col:
            fig_hist = histogramme(df, hist_col)
            st.plotly_chart(
                fig_hist,
                use_container_width=True,
                key=f"vis_hist_{hist_col}",
            )

        # Correlation heatmap
        if len(numeric_cols) >= 2:
            st.markdown("**Matrice de correlation**")
            fig_corr = heatmap_correlation(df)
            st.plotly_chart(
                fig_corr,
                use_container_width=True,
                key="heatmap_vis",  # Unique key — fix for the duplicate-id bug
            )

        # Boxplot
        box_col = st.selectbox(
            "Colonne pour la boite a moustaches", numeric_cols, key="vis_box_col"
        )
        if box_col:
            fig_box = boxplot(df, box_col)
            st.plotly_chart(
                fig_box,
                use_container_width=True,
                key=f"vis_box_{box_col}",
            )
    else:
        st.info(
            "Aucune colonne numerique detectee. Affichage des visualisations "
            "categorielles ci-dessous."
        )

    # ── Categorical visualisations ──
    if categorical_cols:
        st.markdown(
            "<h4><i class='fa-solid fa-tags'></i> Donnees categorielles</h4>",
            unsafe_allow_html=True,
        )
        st.caption(
            "Selectionnez une colonne textuelle (ex: filiere, departement, "
            "categorie) pour voir la repartition des valeurs."
        )

        # Surface dominant categorical fields first (mode covers >=30% of values
        # AND <=50 unique values) so the most insightful charts are on top.
        stats_cols = analytics.get("statistiques", {}).get("colonnes", {})
        dominant = [
            c for c in categorical_cols
            if stats_cols.get(c, {}).get("is_dominant")
        ]
        ordered_cols = dominant + [c for c in categorical_cols if c not in dominant]

        cat_col = st.selectbox(
            "Colonne categorielle", ordered_cols, key="vis_cat_col"
        )

        if cat_col:
            stats = stats_cols.get(cat_col, {})
            unique_count = stats.get("unique_count", df[cat_col].nunique())
            mode_value = stats.get("mode") or "N/A"
            mode_pct = stats.get("mode_frequency_pct", 0.0)

            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                render_metric_card(
                    "Valeurs uniques", str(unique_count),
                    "fa-solid fa-fingerprint",
                )
            with mc2:
                render_metric_card(
                    "Valeur dominante", str(mode_value),
                    "fa-solid fa-crown",
                )
            with mc3:
                render_metric_card(
                    "Part de la dominante", f"{mode_pct:.1f}%",
                    "fa-solid fa-chart-pie",
                )

            fig_bar = bar_categorical_frequency(df, cat_col, top_n=15)
            st.plotly_chart(
                fig_bar,
                use_container_width=True,
                key=f"vis_cat_bar_{cat_col}",
            )

            fig_pie = pie_categorical(df, cat_col, top_n=8)
            st.plotly_chart(
                fig_pie,
                use_container_width=True,
                key=f"vis_cat_pie_{cat_col}",
            )


# ---------------------------------------------------------------------------
# Anomalies tab
# ---------------------------------------------------------------------------
def _render_anomalies_tab(anomalies: dict) -> None:
    """Render the anomalies tab with filtering."""
    st.markdown("### Anomalies detectees")

    total = anomalies.get("total", 0)
    resume = anomalies.get("resume", {})

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card(
            "Total Anomalies", str(total), "fa-solid fa-circle-exclamation"
        )
    with col2:
        render_metric_card(
            "Z-Score", str(resume.get("zscore_count", 0)), "fa-solid fa-chart-bar"
        )
    with col3:
        render_metric_card(
            "IQR", str(resume.get("iqr_count", 0)),
            "fa-solid fa-magnifying-glass-chart",
        )
    with col4:
        render_metric_card(
            "Isolation Forest", str(resume.get("isolation_count", 0)),
            "fa-solid fa-tree",
        )

    algo_filter = st.selectbox(
        "Filtrer par algorithme",
        ["Tous", "zscore", "iqr", "isolation_forest"],
        key="anom_algo_filter",
    )

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

        fig = anomalies_chart(all_anomalies)
        st.plotly_chart(
            fig,
            use_container_width=True,
            key=f"anom_chart_{algo_filter}",
        )
    else:
        st.info("Aucune anomalie detectee avec ce filtre.")


# ---------------------------------------------------------------------------
# Insights tab
# ---------------------------------------------------------------------------
def _render_insights_tab(analytics: dict, anomalies: dict, dataset_id: int) -> None:
    """Render the AI insights tab."""
    st.markdown(
        "<h3><i class='fa-solid fa-robot'></i> Insights IA (Gemini)</h3>",
        unsafe_allow_html=True,
    )

    if st.button(
        "Generer des insights IA",
        key="generate_insights_btn",
        icon=":material/auto_awesome:",
    ):
        try:
            with st.spinner("Generation des insights par IA en cours..."):
                from app.Repositories.dataset_repository import DatasetRepository
                _ds_repo = DatasetRepository()
                dataset = _ds_repo.find_by_id(dataset_id)

                llm = LLMService()

                # Build context (handles both numeric and categorical stats)
                stats_data = analytics.get("statistiques", {}).get("colonnes", {})
                stats_summary = ""
                for col_name, col_stats in list(stats_data.items())[:5]:
                    kind = col_stats.get("_kind", "numeric")
                    if kind == "categorical":
                        stats_summary += (
                            f"  {col_name} (categoriel): "
                            f"{col_stats.get('unique_count')} valeurs uniques, "
                            f"mode='{col_stats.get('mode')}' "
                            f"({col_stats.get('mode_frequency_pct')}%)\n"
                        )
                    else:
                        stats_summary += (
                            f"  {col_name}: moy={col_stats.get('mean')}, "
                            f"med={col_stats.get('median')}, "
                            f"std={col_stats.get('std')}\n"
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

                # Surface init/call diagnostics if the LLM was unavailable.
                if not llm.is_available and llm.last_error:
                    st.warning(
                        "Le service IA n'est pas pleinement disponible. "
                        f"Detail: {llm.last_error}"
                    )

            st.success("Insights generes.")

        except Exception as e:
            st.error(f"Erreur: {e}")

    if "ai_insights" in st.session_state:
        st.markdown("---")
        st.markdown(st.session_state["ai_insights"])


# ---------------------------------------------------------------------------
# Correlations tab
# ---------------------------------------------------------------------------
def _render_correlations_tab(analytics: dict, dataset_id: int) -> None:
    """Render the correlations analysis tab."""
    st.markdown(
        "<h3><i class='fa-solid fa-link'></i> Analyse des correlations</h3>",
        unsafe_allow_html=True,
    )

    correlations = analytics.get("correlations", {})
    multicollinearite = analytics.get("multicollinearite", [])

    if not correlations or correlations.get("message"):
        st.info(correlations.get("message", "Donnees de correlation non disponibles."))
        return

    distribution = correlations.get("distribution", {})
    if distribution:
        st.markdown("#### Distribution des forces de correlation")
        cols = st.columns(min(5, len(distribution)) or 1)
        labels = list(distribution.keys())
        values = list(distribution.values())
        for i, col in enumerate(cols):
            with col:
                if i < len(labels):
                    render_metric_card(labels[i], str(values[i]), "fa-solid fa-link")

    top_pos = correlations.get("top_paires_positives", [])
    if top_pos:
        st.markdown(
            "<h4><i class='fa-solid fa-arrow-trend-up'></i> "
            "Top correlations positives</h4>",
            unsafe_allow_html=True,
        )
        df_pos = pd.DataFrame(top_pos)
        display_cols = ["col1", "col2", "correlation", "force"]
        available = [c for c in display_cols if c in df_pos.columns]
        st.dataframe(df_pos[available], use_container_width=True)

    top_neg = correlations.get("top_paires_negatives", [])
    if top_neg:
        st.markdown(
            "<h4><i class='fa-solid fa-arrow-trend-down'></i> "
            "Top correlations negatives</h4>",
            unsafe_allow_html=True,
        )
        df_neg = pd.DataFrame(top_neg)
        display_cols = ["col1", "col2", "correlation", "force"]
        available = [c for c in display_cols if c in df_neg.columns]
        st.dataframe(df_neg[available], use_container_width=True)

    if multicollinearite:
        st.markdown(
            "<h4><i class='fa-solid fa-triangle-exclamation'></i> "
            "Alertes de multicolinearite</h4>",
            unsafe_allow_html=True,
        )
        st.warning(
            f"{len(multicollinearite)} paire(s) avec correlation >= 0.9 detectee(s). "
            "Cela peut poser probleme pour les modeles de machine learning."
        )
        for pair in multicollinearite:
            st.markdown(
                f"- **{pair['col1']}** <-> **{pair['col2']}**: "
                f"`{pair['correlation']:.3f}` — {pair['recommandation']}"
            )

    # Interactive heatmap
    st.markdown(
        "<h4><i class='fa-solid fa-map'></i> "
        "Matrice de correlation interactive</h4>",
        unsafe_allow_html=True,
    )
    from app.Repositories.dataset_repository import DatasetRepository
    _ds_repo = DatasetRepository()
    dataset = _ds_repo.find_by_id(dataset_id)
    if dataset:
        try:
            df = pd.read_csv(dataset.chemin_fichier, encoding="utf-8")
            fig_corr = heatmap_correlation(df)
            st.plotly_chart(
                fig_corr,
                use_container_width=True,
                key="heatmap_corr",  # Unique key — distinct from "heatmap_vis"
            )
        except Exception as e:
            st.warning(f"Impossible de charger la heatmap: {e}")
