"""PDF report generator using AI and xhtml2pdf.

Generates a multi-page PDF report by asking the Groq LLM to write
the entire report in HTML, injecting matplotlib charts, and converting
it to a PDF document.
"""

import logging
import os
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from xhtml2pdf import pisa

from config.settings import EXPORT_DIR
from app.Services.llm_service import LLMService

logger = logging.getLogger(__name__)


def generer(
    dataset_id: int,
    user_id: int,
    analytics: dict,
    anomalies: dict,
    insights: str,
) -> str:
    """Generate an AI-driven PDF report for a dataset analysis.

    Calls the LLM to generate an HTML report, appends generated charts,
    and converts the final HTML string to a PDF file using xhtml2pdf.

    Args:
        dataset_id: The dataset ID.
        user_id: The user who requested the report.
        analytics: Analytics results dictionary.
        anomalies: Anomalies detection results dictionary.
        insights: (Legacy text insights, ignored in favor of new HTML).

    Returns:
        The file path to the generated PDF.
    """
    # Prepare output path
    export_dir = Path(EXPORT_DIR) / "reports"
    export_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"rapport_ia_dataset_{dataset_id}_{timestamp}.pdf"
    output_path = export_dir / filename

    logger.info("Génération du rapport PDF par IA: %s", output_path)

    # 1. Build the context for the LLM
    dataset_info = analytics.get("dataset_info", {})
    nb_rows = dataset_info.get("nb_lignes", "N/A")
    nb_cols = dataset_info.get("nb_colonnes", "N/A")
    dataset_name = dataset_info.get("nom", f"Dataset #{dataset_id}")
    
    # Extract some summary stats to send to the LLM
    stats_data = analytics.get("statistiques", {}).get("colonnes", {})
    summary_lines = []
    for col, st in list(stats_data.items())[:30]:  # Limit to 30 columns to avoid token limits
        if st.get("_kind") == "numeric":
            summary_lines.append(f"- {col}: Moyenne={st.get('mean')}, Min={st.get('min')}, Max={st.get('max')}")
        else:
            summary_lines.append(f"- {col}: Catégorielle, Valeurs Uniques={st.get('unique_count')}, Mode={st.get('mode')}")
    
    context = {
        "dataset_name": dataset_name,
        "nb_rows": nb_rows,
        "nb_cols": nb_cols,
        "stats_summary": "\n".join(summary_lines),
        "anomalies_count": anomalies.get("total", 0)
    }

    # 2. Get the HTML from the LLM
    llm = LLMService()
    html_content = llm.generer_rapport_html(context)

    # 3. Generate Charts and append them to the HTML
    chart_images = _generate_charts(analytics, anomalies)
    
    charts_html = "<div style='page-break-before: always;'><h2>Visualisations</h2>"
    for title, path in chart_images:
        # xhtml2pdf requires absolute paths for local images
        abs_path = os.path.abspath(path).replace("\\", "/")
        charts_html += f"<h3>{title}</h3>"
        charts_html += f"<img src='{abs_path}' style='width: 600px; max-width: 100%; margin-bottom: 20px;' />"
    charts_html += "</div>"
    
    # Inject charts right before the closing </body> tag
    if "</body>" in html_content:
        html_content = html_content.replace("</body>", f"{charts_html}</body>")
    else:
        html_content += charts_html

    # Ensure encoding header is present for xhtml2pdf
    if "<meta charset=" not in html_content.lower():
        html_content = html_content.replace("<head>", "<head><meta charset='UTF-8'>")

    # 4. Convert HTML to PDF
    try:
        with open(output_path, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(
                html_content,
                dest=pdf_file,
                encoding='utf-8'
            )
            
        if pisa_status.err:
            logger.error("Erreurs lors de la création du PDF via xhtml2pdf: %s", pisa_status.err)
        else:
            logger.info("Rapport PDF généré avec succès: %s", output_path)
            
    except Exception as e:
        logger.error("Erreur lors de la génération du PDF: %s", e)
        raise

    # 5. Clean up chart image files
    for _, chart_path in chart_images:
        try:
            os.remove(chart_path)
        except OSError:
            pass

    return str(output_path)


def _generate_charts(analytics: dict, anomalies: dict) -> list[tuple[str, str]]:
    """Generate matplotlib chart images for embedding in the PDF.

    Args:
        analytics: Analytics results dictionary.
        anomalies: Anomalies results dictionary.

    Returns:
        A list of (title, filepath) tuples for generated charts.
    """
    charts = []
    export_dir = Path(EXPORT_DIR) / "temp_charts"
    export_dir.mkdir(parents=True, exist_ok=True)

    # Chart 1: Histogram of a key numeric column
    stats_data = analytics.get("statistiques", {}).get("colonnes", {})
    if stats_data:
        try:
            first_col = list(stats_data.keys())[0]
            col_stats = stats_data[first_col]

            fig, ax = plt.subplots(figsize=(8, 4))
            mean = col_stats.get("mean", 0)
            std = col_stats.get("std", 1)
            if std and std > 0:
                data = np.random.normal(mean, std, 1000)
                ax.hist(data, bins=30, color="#1a237e", alpha=0.7, edgecolor="white")
                ax.set_title(f"Distribution — {first_col}", fontsize=12)
                ax.set_xlabel("Valeur")
                ax.set_ylabel("Fréquence")
                ax.axvline(mean, color="red", linestyle="--", label=f"Moyenne: {mean:.2f}")
                ax.legend()

                chart_path = str(export_dir / "histogram.png")
                fig.savefig(chart_path, dpi=100, bbox_inches="tight")
                plt.close(fig)
                charts.append(("Histogramme de distribution", chart_path))
        except Exception as e:
            logger.warning("Erreur génération histogramme: %s", e)
            plt.close("all")

    # Chart 2: Anomalies by algorithm
    resume = anomalies.get("resume", {})
    if resume:
        try:
            fig, ax = plt.subplots(figsize=(8, 4))
            algos = ["Z-Score", "IQR", "Isolation Forest"]
            counts = [
                resume.get("zscore_count", 0),
                resume.get("iqr_count", 0),
                resume.get("isolation_count", 0),
            ]
            bar_colors = ["#1565c0", "#2e7d32", "#e65100"]
            ax.bar(algos, counts, color=bar_colors, edgecolor="white")
            ax.set_title("Anomalies par Algorithme", fontsize=12)
            ax.set_ylabel("Nombre d'anomalies")
            for i, (algo, count) in enumerate(zip(algos, counts)):
                ax.text(i, count + 0.5, str(count), ha="center", fontweight="bold")

            chart_path = str(export_dir / "anomalies_bar.png")
            fig.savefig(chart_path, dpi=100, bbox_inches="tight")
            plt.close(fig)
            charts.append(("Répartition des anomalies par algorithme", chart_path))
        except Exception as e:
            logger.warning("Erreur génération bar chart anomalies: %s", e)
            plt.close("all")

    # Chart 3: Correlation heatmap
    kpis = analytics.get("kpis", {})
    corr_matrix = kpis.get("correlation_matrix", {})
    if corr_matrix and len(corr_matrix) >= 2:
        try:
            cols = list(corr_matrix.keys())[:10]
            matrix = np.array(
                [[corr_matrix[c1].get(c2, 0) for c2 in cols] for c1 in cols]
            )

            fig, ax = plt.subplots(figsize=(8, 6))
            im = ax.imshow(matrix, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
            ax.set_xticks(range(len(cols)))
            ax.set_yticks(range(len(cols)))
            short_cols = [c[:10] for c in cols]
            ax.set_xticklabels(short_cols, rotation=45, ha="right", fontsize=8)
            ax.set_yticklabels(short_cols, fontsize=8)
            ax.set_title("Matrice de Corrélation", fontsize=12)
            fig.colorbar(im, ax=ax, shrink=0.8)

            chart_path = str(export_dir / "correlation_heatmap.png")
            fig.savefig(chart_path, dpi=100, bbox_inches="tight")
            plt.close(fig)
            charts.append(("Matrice de corrélation", chart_path))
        except Exception as e:
            logger.warning("Erreur génération heatmap: %s", e)
            plt.close("all")

    return charts
