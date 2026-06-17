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
from app.Services.reporting.chart_factory import generate_charts as _factory_generate_charts

logger = logging.getLogger(__name__)


def generer(
    dataset_id: int,
    user_id: int,
    analytics: dict,
    anomalies: dict,
    insights: str,
    selected_charts: list[str] | None = None,
    max_charts: int | None = None,
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
        selected_charts: Chart labels chosen by the user. When None, all
            available charts are included (backward-compatible default).
        max_charts: Maximum number of charts to embed. When None, no limit.

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
    chart_images = _generate_charts(analytics, anomalies, selected_charts, max_charts)

    if chart_images:
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


def _generate_charts(
    analytics: dict,
    anomalies: dict,
    selected_charts: list[str] | None = None,
    max_charts: int | None = None,
) -> list[tuple[str, str]]:
    """Generate matplotlib chart images for embedding in the PDF.

    Delegates to the shared chart factory so the PDF and Excel reports
    stay in sync, while honouring the user's diagram selection and the
    maximum-diagram count.

    Args:
        analytics: Analytics results dictionary.
        anomalies: Anomalies results dictionary.
        selected_charts: Chart labels chosen by the user (None = all).
        max_charts: Maximum number of charts to keep (None = no limit).

    Returns:
        A list of (title, filepath) tuples for generated charts.
    """
    return _factory_generate_charts(
        analytics, anomalies, selected_charts, max_charts
    )
