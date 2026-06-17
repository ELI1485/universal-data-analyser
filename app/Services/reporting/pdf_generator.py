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
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd
from matplotlib.patches import Circle, FancyBboxPatch
from xhtml2pdf import pisa

from config.settings import EXPORT_DIR
from app.Services.llm_service import LLMService
from app.Services.reporting.chart_factory import generate_charts as _factory_generate_charts

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fonts (Poppins) and brand palette
# ---------------------------------------------------------------------------
# The project's bundled Poppins .ttf files. xhtml2pdf cannot load Google Fonts
# via @import, so we embed the local files via @font-face (absolute paths) for
# the HTML body, and register them with matplotlib for the rendered cover.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_FONT_DIR = _PROJECT_ROOT / "assets" / "fonts"
_FONT_FILES = {
    "regular": _FONT_DIR / "Poppins-Regular.ttf",
    "light": _FONT_DIR / "Poppins-Light.ttf",
    "medium": _FONT_DIR / "Poppins-Medium.ttf",
    "semibold": _FONT_DIR / "Poppins-SemiBold.ttf",
    "bold": _FONT_DIR / "Poppins-Bold.ttf",
}

# Brand palette for the premium cover / report design.
_NAVY = "#0A1628"
_NAVY_LIGHT = "#142840"
_ACCENT_BLUE = "#3B82F6"
_ACCENT_GREEN = "#10B981"
_INK_LIGHT = "#E5EDF7"
_MUTED = "#8FA3BF"


def _font(weight: str = "regular") -> fm.FontProperties:
    """Return a matplotlib FontProperties for the given Poppins weight.

    Falls back to the default sans-serif family if the .ttf file is missing.
    """
    path = _FONT_FILES.get(weight, _FONT_FILES["regular"])
    if path.exists():
        return fm.FontProperties(fname=str(path))
    return fm.FontProperties(family="sans-serif")


def _register_matplotlib_fonts() -> None:
    """Register all bundled Poppins weights with matplotlib's font manager."""
    for path in _FONT_FILES.values():
        try:
            if path.exists():
                fm.fontManager.addfont(str(path))
        except Exception as e:  # pragma: no cover - defensive
            logger.debug("Police non enregistrée (%s): %s", path, e)


def _build_font_face_css() -> str:
    """Build a <style> block embedding Poppins via @font-face for xhtml2pdf.

    Uses absolute file paths because xhtml2pdf resolves @font-face ``src`` URLs
    against the local filesystem and does NOT support Google Fonts @import.
    Also sets sensible Poppins-based defaults and styled tables so the whole
    report keeps a consistent, modern look even if the LLM markup is sparse.
    """
    def _src(weight: str) -> str:
        p = _FONT_FILES[weight]
        return p.resolve().as_uri() if p.exists() else ""

    return f"""
    <style>
    @font-face {{
        font-family: 'Poppins';
        src: url('{_src("regular")}');
        font-weight: 400;
    }}
    @font-face {{
        font-family: 'Poppins';
        src: url('{_src("medium")}');
        font-weight: 500;
    }}
    @font-face {{
        font-family: 'Poppins';
        src: url('{_src("semibold")}');
        font-weight: 600;
    }}
    @font-face {{
        font-family: 'Poppins';
        src: url('{_src("bold")}');
        font-weight: 700;
    }}
    @font-face {{
        font-family: 'Poppins';
        src: url('{_src("light")}');
        font-weight: 300;
    }}
    body, p, td, th, li, h1, h2, h3, h4, h5, span, div {{
        font-family: 'Poppins', sans-serif;
    }}
    body {{ color: #1f2937; }}
    h1, h2, h3, h4 {{ color: {_NAVY}; font-weight: 700; }}
    h2 {{ border-bottom: 2px solid {_ACCENT_GREEN}; padding-bottom: 4px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
    th {{
        background-color: {_NAVY}; color: #ffffff; font-weight: 600;
        padding: 7px 9px; text-align: left;
    }}
    td {{ padding: 6px 9px; border-bottom: 1px solid #e5e7eb; }}
    tr:nth-child(even) td {{ background-color: #f3f6fb; }}
    h3.chart-title {{
        color: {_NAVY}; font-weight: 600; font-size: 14px;
        margin: 14px 0 6px 0;
    }}
    </style>
    """


def _generate_cover_image(
    dataset_name: str,
    nb_rows,
    nb_cols,
    user_label: str,
    date_str: str,
    export_dir: Path,
) -> str | None:
    """Render a premium, full-page A4 cover as a PNG using matplotlib.

    Rendering the cover as an image (rather than relying on xhtml2pdf's very
    limited CSS) guarantees the modern annual-report look — dark navy
    background, blue/green decorative curved shapes, and Poppins typography —
    is preserved exactly in the final PDF.

    Args:
        dataset_name: Name of the analysed dataset.
        nb_rows: Row count (int or "N/A").
        nb_cols: Column count (int or "N/A").
        user_label: Human-readable author/user string.
        date_str: Pre-formatted generation date.
        export_dir: Directory to write the cover image into.

    Returns:
        The path to the generated cover PNG, or ``None`` on failure.
    """
    try:
        _register_matplotlib_fonts()

        # A4 portrait proportions.
        fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
        ax = fig.add_axes([0, 0, 1, 1])
        W, H = 100.0, 141.4
        ax.set_xlim(0, W)
        ax.set_ylim(0, H)
        ax.axis("off")

        # Background
        ax.add_patch(plt.Rectangle((0, 0), W, H, color=_NAVY, zorder=0))

        # Decorative curved shapes — soft overlapping circles forming a
        # blue→green gradient glow in two corners.
        def _glow(cx, cy, base_r, color, rings=7, max_alpha=0.18):
            for i in range(rings, 0, -1):
                r = base_r * (i / rings)
                ax.add_patch(
                    Circle(
                        (cx, cy), r, color=color,
                        alpha=max_alpha * (1 - i / (rings + 1)) + 0.02,
                        zorder=1, linewidth=0,
                    )
                )

        _glow(96, 120, 46, _ACCENT_BLUE)
        _glow(8, 18, 50, _ACCENT_GREEN)
        # Crisp accent ring (curved shape) bottom-right.
        ax.add_patch(Circle((100, 8), 30, fill=False, ec=_ACCENT_GREEN,
                            lw=1.2, alpha=0.5, zorder=2))
        ax.add_patch(Circle((2, 132), 24, fill=False, ec=_ACCENT_BLUE,
                            lw=1.2, alpha=0.5, zorder=2))

        # Brand row: small bar-chart logo glyph + wordmark.
        bx, by = 12, 122
        bar_heights = [3.0, 5.2, 4.0, 6.4]
        for i, bh in enumerate(bar_heights):
            col = _ACCENT_GREEN if i % 2 == 0 else _ACCENT_BLUE
            ax.add_patch(plt.Rectangle((bx + i * 1.9, by), 1.4, bh,
                                       color=col, zorder=4))
        ax.text(bx + 9.5, by + 2.2, "Universal Data Analyzer",
                fontproperties=_font("semibold"), fontsize=13,
                color=_INK_LIGHT, va="center", zorder=4)

        # Thin accent divider under the brand.
        ax.add_patch(plt.Rectangle((12, 116), 30, 0.5, color=_ACCENT_GREEN,
                                   zorder=4))

        # Main title.
        ax.text(12, 84, "Rapport", fontproperties=_font("bold"), fontsize=54,
                color="#FFFFFF", va="bottom", zorder=4)
        ax.text(12, 71, "d'Analyse", fontproperties=_font("bold"), fontsize=54,
                color=_ACCENT_GREEN, va="bottom", zorder=4)

        # Subtitle: dataset name.
        ax.text(12, 64, "Analyse de données — Intelligence Artificielle",
                fontproperties=_font("light"), fontsize=13, color=_MUTED,
                va="center", zorder=4)

        # Metadata card.
        card = FancyBboxPatch(
            (12, 26), 76, 26,
            boxstyle="round,pad=0.6,rounding_size=2.2",
            linewidth=1, edgecolor=_NAVY_LIGHT, facecolor=_NAVY_LIGHT,
            alpha=0.9, zorder=3,
        )
        ax.add_patch(card)

        meta = [
            ("Jeu de données", str(dataset_name)),
            ("Dimensions", f"{nb_rows} lignes  ×  {nb_cols} colonnes"),
            ("Généré par", str(user_label)),
            ("Date", str(date_str)),
        ]
        y0 = 47
        for label, value in meta:
            ax.text(16, y0, label.upper(), fontproperties=_font("medium"),
                    fontsize=8, color=_ACCENT_BLUE, va="center", zorder=4)
            ax.text(44, y0, value, fontproperties=_font("semibold"),
                    fontsize=10.5, color=_INK_LIGHT, va="center", zorder=4)
            y0 -= 6.2

        # Footer.
        ax.text(12, 10, "Document généré automatiquement",
                fontproperties=_font("light"), fontsize=9, color=_MUTED,
                va="center", zorder=4)

        cover_path = str(export_dir / "cover_page.png")
        fig.savefig(cover_path, dpi=150, facecolor=_NAVY)
        plt.close(fig)
        return cover_path
    except Exception as e:  # pragma: no cover - defensive
        logger.warning("Échec de génération de la page de couverture: %s", e)
        plt.close("all")
        return None


def _generate_cover_page_html(cover_image_path: str | None) -> str:
    """Return the HTML for the premium cover page.

    The cover is embedded as a single full-page image (rendered by
    :func:`_generate_cover_image`) followed by a page break so the AI report
    body starts on a fresh page.

    Args:
        cover_image_path: Path to the rendered cover PNG, or ``None``.

    Returns:
        An HTML fragment for the cover page (empty string if no image).
    """
    if not cover_image_path:
        return ""
    abs_path = os.path.abspath(cover_image_path).replace("\\", "/")
    return (
        "<div style='page-break-after: always; text-align: center; margin: 0; padding: 0;'>"
        f"<img src='{abs_path}' style='width: 100%; height: auto;' />"
        "</div>"
    )


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

    # 2b. Render the premium cover page image (navy + Poppins).
    cover_dir = Path(EXPORT_DIR) / "temp_charts"
    cover_dir.mkdir(parents=True, exist_ok=True)
    user_label = dataset_info.get("user_nom") or f"Utilisateur #{user_id}"
    cover_path = _generate_cover_image(
        dataset_name=dataset_name,
        nb_rows=nb_rows,
        nb_cols=nb_cols,
        user_label=user_label,
        date_str=datetime.now().strftime("%d/%m/%Y"),
        export_dir=cover_dir,
    )
    cover_html = _generate_cover_page_html(cover_path)

    # Inject the cover right after the opening <body> tag.
    if cover_html:
        if "<body>" in html_content:
            html_content = html_content.replace("<body>", f"<body>{cover_html}", 1)
        elif "<body" in html_content:
            # <body ...> with attributes — insert after the tag close.
            idx = html_content.find("<body")
            close = html_content.find(">", idx)
            if close != -1:
                html_content = (
                    html_content[: close + 1] + cover_html + html_content[close + 1 :]
                )
        else:
            html_content = cover_html + html_content

    # 3. Generate Charts and append them to the HTML
    chart_images = _generate_charts(analytics, anomalies, selected_charts, max_charts)

    if chart_images:
        charts_html = "<div style='page-break-before: always;'><h2>Visualisations</h2>"
        for title, path in chart_images:
            # xhtml2pdf requires absolute paths for local images
            abs_path = os.path.abspath(path).replace("\\", "/")
            charts_html += f"<h3 class='chart-title'>{title}</h3>"
            charts_html += f"<img src='{abs_path}' style='width: 600px; max-width: 100%; margin-bottom: 20px;' />"
        charts_html += "</div>"

        # Inject charts right before the closing </body> tag
        if "</body>" in html_content:
            html_content = html_content.replace("</body>", f"{charts_html}</body>")
        else:
            html_content += charts_html

    # 3b. Embed Poppins (@font-face) + base styling into the <head>.
    font_css = _build_font_face_css()
    if "</head>" in html_content:
        html_content = html_content.replace("</head>", f"{font_css}</head>", 1)
    elif "<head>" in html_content:
        html_content = html_content.replace("<head>", f"<head>{font_css}", 1)
    else:
        html_content = font_css + html_content

    # Ensure encoding header is present for xhtml2pdf
    if "<meta charset=" not in html_content.lower():
        if "<head>" in html_content:
            html_content = html_content.replace("<head>", "<head><meta charset='UTF-8'>")
        else:
            html_content = "<meta charset='UTF-8'>" + html_content

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

    # 5. Clean up chart image files (and the temporary cover image)
    for _, chart_path in chart_images:
        try:
            os.remove(chart_path)
        except OSError:
            pass
    if cover_path:
        try:
            os.remove(cover_path)
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
