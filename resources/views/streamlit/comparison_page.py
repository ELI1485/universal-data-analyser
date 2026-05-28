"""Streamlit comparison page for side-by-side dataset analysis."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.Http.Controllers.comparison_controller import ComparisonController
from app.Http.Controllers.upload_controller import UploadController
from resources.views.streamlit.style_utils import render_metric_card

_comparison_ctrl = ComparisonController()
_upload_ctrl = UploadController()


def render(user_id: int, role: str) -> None:
    """Render the dataset comparison page.

    Args:
        user_id: Current user's ID.
        role: Current user's role.
    """
    st.markdown(
        "<h2 style='display: flex; align-items: center; gap: 10px;'>"
        "<i class='fa-solid fa-code-compare'></i> Comparaison de datasets</h2>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # Load datasets
    try:
        datasets = _upload_ctrl.lister_datasets(user_id, role)
    except Exception as e:
        st.error(f"Erreur chargement datasets: {e}")
        return

    if len(datasets) < 2:
        st.info(
            "Vous devez avoir au moins 2 datasets importes pour effectuer "
            "une comparaison. Importez d'abord vos fichiers de donnees."
        )
        return

    dataset_options = {f"{ds.nom} (ID: {ds.id})": ds.id for ds in datasets}
    options_list = list(dataset_options.keys())

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            "<h4><i class='fa-solid fa-folder'></i> Dataset de reference (ancien)</h4>",
            unsafe_allow_html=True,
        )
        selected_ancien = st.selectbox(
            "Dataset ancien", options_list, key="comp_ancien"
        )
    with col2:
        st.markdown(
            "<h4><i class='fa-solid fa-folder-plus'></i> Dataset actuel (nouveau)</h4>",
            unsafe_allow_html=True,
        )
        default_idx = min(1, len(options_list) - 1)
        selected_nouveau = st.selectbox(
            "Dataset nouveau", options_list, index=default_idx, key="comp_nouveau"
        )

    id_ancien = dataset_options[selected_ancien]
    id_nouveau = dataset_options[selected_nouveau]

    if id_ancien == id_nouveau:
        st.warning("Veuillez selectionner deux datasets differents.")
        return

    if st.button(
        "Comparer les datasets",
        use_container_width=True,
        icon=":material/compare_arrows:",
    ):
        try:
            with st.spinner("Comparaison en cours..."):
                result = _comparison_ctrl.comparer(
                    id_ancien, id_nouveau, user_id, role
                )
                st.session_state["comparison_result"] = result
            st.success("Comparaison terminee.")
        except Exception as e:
            st.error(f"Erreur: {str(e)}")
            return

    if "comparison_result" in st.session_state:
        _display_comparison(st.session_state["comparison_result"])


def _display_comparison(result: dict) -> None:
    """Display comparison results in organized sections."""
    schema = result["schema_changes"]
    taille = result["taille_changes"]
    drift = result["drift_statistique"]
    anomalies = result["anomalies_comparison"]

    # Overview cards
    st.markdown(
        "<h3><i class='fa-solid fa-chart-pie'></i> Vue d'ensemble</h3>",
        unsafe_allow_html=True,
    )
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        diff_sign = "+" if taille["diff_lignes"] >= 0 else ""
        render_metric_card(
            "Diff. lignes",
            f"{diff_sign}{taille['diff_lignes']}",
            "fa-solid fa-arrows-up-down",
        )
    with col2:
        diff_sign = "+" if taille["diff_colonnes"] >= 0 else ""
        render_metric_card(
            "Diff. colonnes",
            f"{diff_sign}{taille['diff_colonnes']}",
            "fa-solid fa-table-columns",
        )
    with col3:
        render_metric_card(
            "Colonnes ajoutees",
            str(schema["nb_ajoutees"]),
            "fa-solid fa-plus",
        )
    with col4:
        render_metric_card(
            "Colonnes supprimees",
            str(schema["nb_supprimees"]),
            "fa-solid fa-minus",
        )

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(
        ["Schema", "Drift statistique", "Anomalies"]
    )

    with tab1:
        _render_schema_tab(schema)

    with tab2:
        _render_drift_tab(drift)

    with tab3:
        _render_anomaly_comparison_tab(anomalies)


def _render_schema_tab(schema: dict) -> None:
    """Render schema comparison details."""
    st.markdown(
        "<h3><i class='fa-solid fa-screwdriver-wrench'></i> Changements de schema</h3>",
        unsafe_allow_html=True,
    )

    if schema["colonnes_ajoutees"]:
        st.markdown(
            "<h4><i class='fa-solid fa-circle-plus'></i> Colonnes ajoutees</h4>",
            unsafe_allow_html=True,
        )
        for col in schema["colonnes_ajoutees"]:
            st.markdown(f"- `{col}`")

    if schema["colonnes_supprimees"]:
        st.markdown(
            "<h4><i class='fa-solid fa-circle-minus'></i> Colonnes supprimees</h4>",
            unsafe_allow_html=True,
        )
        for col in schema["colonnes_supprimees"]:
            st.markdown(f"- `{col}`")

    if schema["types_modifies"]:
        st.markdown(
            "<h4><i class='fa-solid fa-arrows-rotate'></i> Types modifies</h4>",
            unsafe_allow_html=True,
        )
        df_types = pd.DataFrame(schema["types_modifies"])
        st.dataframe(df_types, use_container_width=True)

    if (
        not schema["colonnes_ajoutees"]
        and not schema["colonnes_supprimees"]
        and not schema["types_modifies"]
    ):
        st.success("Aucun changement de schema detecte.")


def _render_drift_tab(drift: list) -> None:
    """Render statistical drift analysis."""
    st.markdown(
        "<h3><i class='fa-solid fa-chart-line'></i> Drift statistique</h3>",
        unsafe_allow_html=True,
    )

    if not drift:
        st.info("Aucune colonne numerique commune pour analyser le drift.")
        return

    significant = [d for d in drift if d.get("drift_significatif")]
    if significant:
        st.warning(
            f"{len(significant)} colonne(s) avec drift significatif detecte(s) "
            "(shift de la moyenne > 1 ecart-type)."
        )

    drift_rows = []
    for d in drift:
        row = {
            "Colonne": d["colonne"],
            "Moy. ancien": round(d["ancien"]["mean"], 2) if d["ancien"]["mean"] is not None else "N/A",
            "Moy. nouveau": round(d["nouveau"]["mean"], 2) if d["nouveau"]["mean"] is not None else "N/A",
            "Drift (abs)": round(d["mean_drift"], 2) if d["mean_drift"] is not None else "N/A",
            "% Changement": f"{d['mean_pct_change']:.1f}%",
            "Significatif": "Oui" if d["drift_significatif"] else "Non",
        }
        drift_rows.append(row)

    df_drift = pd.DataFrame(drift_rows)
    st.dataframe(df_drift, use_container_width=True)

    if drift:
        cols_with_drift = [d["colonne"] for d in drift if d["mean_drift"] is not None]
        drift_vals = [d["mean_pct_change"] for d in drift if d["mean_drift"] is not None]

        if cols_with_drift:
            colors = ["#e74c3c" if abs(v) > 10 else "#27ae60" for v in drift_vals]
            fig = go.Figure(
                data=[
                    go.Bar(
                        x=cols_with_drift,
                        y=drift_vals,
                        marker_color=colors,
                    )
                ]
            )
            fig.update_layout(
                title="Variation de la moyenne par colonne (%)",
                xaxis_title="Colonne",
                yaxis_title="% Changement",
                template="plotly_white",
            )
            st.plotly_chart(
                fig, use_container_width=True, key="comparison_drift_chart"
            )


def _render_anomaly_comparison_tab(anomalies: dict) -> None:
    """Render anomaly comparison."""
    st.markdown(
        "<h3><i class='fa-solid fa-triangle-exclamation'></i> "
        "Comparaison des anomalies</h3>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        render_metric_card(
            "Anomalies (ancien)",
            str(anomalies["ancien_total"]),
            "fa-solid fa-circle-exclamation",
        )
    with col2:
        render_metric_card(
            "Anomalies (nouveau)",
            str(anomalies["nouveau_total"]),
            "fa-solid fa-circle-exclamation",
        )
    with col3:
        if anomalies.get("amelioration"):
            render_metric_card(
                "Evolution",
                f"-{abs(anomalies['diff'])}",
                "fa-solid fa-arrow-trend-down",
            )
        else:
            diff_sign = "+" if anomalies["diff"] > 0 else ""
            render_metric_card(
                "Evolution",
                f"{diff_sign}{anomalies['diff']}",
                "fa-solid fa-arrow-trend-up",
            )

    if anomalies.get("amelioration"):
        st.success(
            f"Amelioration: {abs(anomalies['diff'])} anomalies en moins "
            "dans le nouveau dataset."
        )
    elif anomalies["diff"] > 0:
        st.warning(
            f"Attention: {anomalies['diff']} anomalies supplementaires "
            "detectees dans le nouveau dataset."
        )
    else:
        st.info("Nombre d'anomalies stable entre les deux versions.")
