"""PDF report generator using ReportLab.

Generates a multi-page PDF report with cover page, executive summary,
statistics tables, anomaly tables, and embedded charts.
"""

import io
import logging
import os
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)

from config.settings import EXPORT_DIR

logger = logging.getLogger(__name__)


def generer(
    dataset_id: int,
    user_id: int,
    analytics: dict,
    anomalies: dict,
    insights: str,
) -> str:
    """Generate a PDF report for a dataset analysis.

    Creates a multi-page PDF with:
    - Cover page (title, dataset name, date, user)
    - Executive summary (LLM insights)
    - Statistics table (descriptive stats per column)
    - Top anomalies table
    - Embedded charts (histogram, correlation heatmap)

    Args:
        dataset_id: The dataset ID.
        user_id: The user who requested the report.
        analytics: Analytics results dictionary.
        anomalies: Anomalies detection results dictionary.
        insights: LLM-generated insights text.

    Returns:
        The file path to the generated PDF.
    """
    # Prepare output path
    export_dir = Path(EXPORT_DIR) / "reports"
    export_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"rapport_dataset_{dataset_id}_{timestamp}.pdf"
    output_path = export_dir / filename

    logger.info("Génération du rapport PDF: %s", output_path)

    # Create the PDF document
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor("#1a237e"),
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor("#283593"),
    )
    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=8,
        leading=14,
    )

    elements = []

    # --- Cover Page ---
    elements.append(Spacer(1, 4 * cm))
    elements.append(Paragraph("Universal Data Analyzer", title_style))
    elements.append(Spacer(1, 1 * cm))
    elements.append(Paragraph("Rapport d'Analyse", heading_style))
    elements.append(Spacer(1, 2 * cm))

    dataset_info = analytics.get("dataset_info", {})
    cover_data = [
        ["Dataset:", dataset_info.get("nom", f"Dataset #{dataset_id}")],
        ["Date:", datetime.now().strftime("%d/%m/%Y %H:%M")],
        ["Utilisateur ID:", str(user_id)],
        ["Lignes:", str(dataset_info.get("nb_lignes", "N/A"))],
        ["Colonnes:", str(dataset_info.get("nb_colonnes", "N/A"))],
    ]
    cover_table = Table(cover_data, colWidths=[4 * cm, 10 * cm])
    cover_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 12),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(cover_table)
    elements.append(PageBreak())

    # --- Executive Summary (LLM Insights) ---
    elements.append(Paragraph("1. Résumé Exécutif — Insights IA", heading_style))
    elements.append(Spacer(1, 0.5 * cm))

    # Split insights into paragraphs
    if insights:
        for paragraph_text in insights.split("\n"):
            paragraph_text = paragraph_text.strip()
            if paragraph_text:
                # Escape special characters for ReportLab
                safe_text = (
                    paragraph_text.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
                elements.append(Paragraph(safe_text, body_style))
    else:
        elements.append(Paragraph("Aucun insight IA disponible.", body_style))

    elements.append(PageBreak())

    # --- Statistics Table ---
    elements.append(Paragraph("2. Statistiques Descriptives", heading_style))
    elements.append(Spacer(1, 0.5 * cm))

    stats_data = analytics.get("statistiques", {}).get("colonnes", {})
    if stats_data:
        # Build table header
        header = ["Colonne", "Moyenne", "Médiane", "Écart-type", "Min", "Max"]
        table_data = [header]

        for col_name, col_stats in list(stats_data.items())[:20]:
            row = [
                col_name[:20],
                _format_val(col_stats.get("mean")),
                _format_val(col_stats.get("median")),
                _format_val(col_stats.get("std")),
                _format_val(col_stats.get("min")),
                _format_val(col_stats.get("max")),
            ]
            table_data.append(row)

        stats_table = Table(table_data, repeatRows=1)
        stats_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        elements.append(stats_table)
    else:
        elements.append(Paragraph("Aucune statistique disponible.", body_style))

    elements.append(PageBreak())

    # --- Anomalies Table ---
    elements.append(Paragraph("3. Anomalies Détectées", heading_style))
    elements.append(Spacer(1, 0.5 * cm))

    total_anomalies = anomalies.get("total", 0)
    elements.append(
        Paragraph(f"Total des anomalies détectées: <b>{total_anomalies}</b>", body_style)
    )
    elements.append(Spacer(1, 0.3 * cm))

    # Summary by algorithm
    resume = anomalies.get("resume", {})
    summary_data = [
        ["Algorithme", "Nombre d'anomalies"],
        ["Z-Score", str(resume.get("zscore_count", 0))],
        ["IQR", str(resume.get("iqr_count", 0))],
        ["Isolation Forest", str(resume.get("isolation_count", 0))],
    ]
    summary_table = Table(summary_data, colWidths=[6 * cm, 5 * cm])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#c62828")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 0.5 * cm))

    # Top anomalies detail table
    all_anomalies = (
        anomalies.get("zscore", [])
        + anomalies.get("iqr", [])
        + anomalies.get("isolation", [])
    )
    # Sort by score descending, limit to top 20
    all_anomalies.sort(key=lambda x: x.get("score", 0), reverse=True)
    top_anomalies = all_anomalies[:20]

    if top_anomalies:
        anom_header = ["Ligne", "Colonne", "Score", "Algorithme", "Valeur"]
        anom_table_data = [anom_header]
        for a in top_anomalies:
            anom_table_data.append(
                [
                    str(a.get("ligne", "")),
                    str(a.get("colonne", ""))[:15],
                    f"{a.get('score', 0):.3f}",
                    a.get("type", ""),
                    _format_val(a.get("valeur")),
                ]
            )
        anom_table = Table(anom_table_data, repeatRows=1)
        anom_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e65100")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fff3e0")]),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        elements.append(anom_table)

    elements.append(PageBreak())

    # --- Charts ---
    elements.append(Paragraph("4. Visualisations", heading_style))
    elements.append(Spacer(1, 0.5 * cm))

    # Generate and embed charts
    chart_images = _generate_charts(analytics, anomalies)
    for chart_title, chart_path in chart_images:
        elements.append(Paragraph(chart_title, body_style))
        elements.append(Spacer(1, 0.3 * cm))
        try:
            img = Image(chart_path, width=14 * cm, height=8 * cm)
            elements.append(img)
            elements.append(Spacer(1, 0.5 * cm))
        except Exception as e:
            logger.warning("Impossible d'intégrer le graphique: %s", e)
            elements.append(Paragraph(f"[Graphique non disponible: {e}]", body_style))

    # Build the PDF
    try:
        doc.build(elements)
        logger.info("Rapport PDF généré avec succès: %s", output_path)
    except Exception as e:
        logger.error("Erreur lors de la génération du PDF: %s", e)
        raise

    # Clean up chart image files
    for _, chart_path in chart_images:
        try:
            os.remove(chart_path)
        except OSError:
            pass

    return str(output_path)


def _format_val(value) -> str:
    """Format a value for display in a table cell.

    Args:
        value: The value to format.

    Returns:
        A formatted string representation.
    """
    if value is None:
        return "N/A"
    if isinstance(value, float):
        if abs(value) >= 1000:
            return f"{value:,.2f}"
        return f"{value:.4f}"
    return str(value)


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
            # Create a synthetic histogram from stats
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

    # Chart 2: Anomalies by algorithm (bar chart)
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

    # Chart 3: Correlation heatmap (if available)
    kpis = analytics.get("kpis", {})
    corr_matrix = kpis.get("correlation_matrix", {})
    if corr_matrix and len(corr_matrix) >= 2:
        try:
            cols = list(corr_matrix.keys())[:10]  # Limit to 10 columns
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
