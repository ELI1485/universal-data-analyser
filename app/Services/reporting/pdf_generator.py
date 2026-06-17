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


def _build_report_css() -> str:
    """Build the full premium <style> block for the PDF report.

    Covers the WHOLE document (not just the cover):
      * Embeds Poppins via @font-face with absolute file paths (xhtml2pdf does
        not support Google Fonts @import).
      * Two page templates: a full-bleed, margin-less page for the cover image
        and a ``content`` page with comfortable margins + a repeating branded
        footer (page numbers) for every report page.
      * A consistent, modern type system: hero <h1>, section <h2> with an
        accent underline + side bar, styled tables (navy headers, zebra rows),
        callout boxes and chart titles.
    """
    def _src(weight: str) -> str:
        p = _FONT_FILES[weight]
        return p.resolve().as_uri() if p.exists() else ""

    return f"""
    <style>
    /* xhtml2pdf only addresses @font-face by normal/bold, so we map the two
       weights actually used in the body. (The cover image uses the full set
       of weights directly via matplotlib.) */
    @font-face {{ font-family: 'Poppins'; src: url('{_src("regular")}'); }}
    @font-face {{ font-family: 'Poppins'; src: url('{_src("bold")}'); font-weight: bold; }}

    /* Page 1 (cover): full bleed, no margins. */
    @page {{ size: a4 portrait; margin: 0cm; }}

    /* Report content pages: margins + repeating branded footer. */
    @page content {{
        size: a4 portrait;
        margin: 1.7cm 1.5cm 2cm 1.5cm;
        @frame footer_frame {{
            -pdf-frame-content: footerContent;
            left: 1.5cm; right: 1.5cm; bottom: 0.9cm; height: 1cm;
        }}
    }}

    body, p, td, th, li, h1, h2, h3, h4, h5, span, div {{
        font-family: 'Poppins', sans-serif;
    }}
    body {{ color: #2b3440; font-size: 10.5pt; line-height: 1.55; }}

    h1 {{
        color: {_NAVY}; font-weight: 700; font-size: 21pt;
        margin: 0 0 4px 0; letter-spacing: -0.3px;
    }}
    h2 {{
        color: {_NAVY}; font-weight: 700; font-size: 14pt;
        margin: 20px 0 9px 0; padding: 3px 0 5px 10px;
        border-left: 4px solid {_ACCENT_GREEN};
        border-bottom: 1.5px solid #e3e9f2;
    }}
    h3 {{ color: {_NAVY}; font-weight: 600; font-size: 11.5pt; margin: 13px 0 5px 0; }}
    h4 {{ color: {_ACCENT_BLUE}; font-weight: 600; font-size: 10.5pt; margin: 10px 0 4px 0; }}
    p {{ margin: 6px 0; }}
    ul, ol {{ margin: 6px 0 6px 4px; }}
    li {{ margin: 3px 0; }}
    a {{ color: {_ACCENT_BLUE}; text-decoration: none; }}
    strong, b {{ color: {_NAVY}; }}

    /* Slim intro ribbon shown once at the top of the content (table-based so
       the navy background renders as one solid band in xhtml2pdf). */
    .report-head {{ width: 100%; margin: 0 0 16px 0; border-collapse: collapse; }}
    .report-head td {{
        background-color: {_NAVY}; color: #ffffff; border: 0;
        padding: 10px 16px; font-size: 9.5pt;
    }}
    .report-head .rh-name {{ color: #ffffff; font-weight: bold; }}
    .report-head .rh-bar {{ color: {_ACCENT_GREEN}; }}
    .report-head .rh-right {{ text-align: right; color: {_ACCENT_GREEN}; font-weight: bold; }}

    table {{ border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 9.5pt; }}
    th {{
        background-color: {_NAVY}; color: #ffffff; font-weight: 600;
        padding: 7px 9px; text-align: left;
    }}
    td {{ padding: 6px 9px; border-bottom: 1px solid #e5e7eb; }}
    tr:nth-child(even) td {{ background-color: #f3f6fb; }}

    h3.chart-title {{
        color: {_NAVY}; font-weight: 600; font-size: 11.5pt;
        margin: 14px 0 6px 0; padding-left: 8px;
        border-left: 3px solid {_ACCENT_BLUE};
    }}

    .footer {{
        border-top: 1px solid #d8e0ec; color: {_MUTED};
        font-size: 8pt; padding-top: 4px;
    }}
    .footer .brand {{ color: {_NAVY}; font-weight: 600; }}
    .footer .accent {{ color: {_ACCENT_GREEN}; }}
    </style>
    """


def _build_footer_html(dataset_name: str) -> str:
    """Return the repeating page footer (pulled into the @page footer frame)."""
    safe = (str(dataset_name) or "")[:60]
    return (
        "<div id='footerContent'>"
        "<table class='footer' style='border:0; margin:0;'>"
        "<tr>"
        "<td style='border:0; background:transparent; text-align:left; padding:4px 0;'>"
        "<span class='brand'>Universal Data Analyzer</span> "
        f"<span class='accent'>&bull;</span> {safe}"
        "</td>"
        "<td style='border:0; background:transparent; text-align:right; padding:4px 0;'>"
        "Page <pdf:pagenumber> / <pdf:pagecount>"
        "</td>"
        "</tr></table>"
        "</div>"
    )


def _build_report_head_html(dataset_name: str, nb_rows, nb_cols, date_str: str) -> str:
    """Return the one-time slim intro ribbon shown at the top of the report."""
    return (
        "<table class='report-head'><tr>"
        "<td>"
        "<span class='rh-bar'>&#9608;</span> "
        f"<span class='rh-name'>{dataset_name}</span>"
        f"&nbsp;&nbsp;&middot;&nbsp;&nbsp; {nb_rows} lignes &times; {nb_cols} colonnes"
        f"&nbsp;&nbsp;&middot;&nbsp;&nbsp; {date_str}"
        "</td>"
        "<td class='rh-right'>Rapport d'Analyse</td>"
        "</tr></table>"
    )


def _resolve_user_label(user_id: int) -> str:
    """Resolve a human-readable author name for the cover from the user record.

    Falls back to ``Utilisateur #<id>`` if the user can't be loaded so the
    report never fails just because of a missing name.
    """
    try:
        from app.Repositories.user_repository import UserRepository

        user = UserRepository().find_by_id(user_id)
        if user and getattr(user, "nom", None):
            return str(user.nom)
    except Exception as e:  # pragma: no cover - defensive
        logger.debug("Impossible de résoudre le nom d'utilisateur %s: %s", user_id, e)
    return f"Utilisateur #{user_id}"


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
    # Full-bleed cover image. The page switch to the bordered "content"
    # template (with footer) is emitted separately by the caller.
    return (
        "<div style='text-align: center; margin: 0; padding: 0;'>"
        f"<img src='{abs_path}' style='width: 21cm; height: 29.7cm;' />"
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

    date_str = datetime.now().strftime("%d/%m/%Y")

    # 2b. Render the premium cover page image (navy + Poppins). The author name
    # is resolved dynamically from the user record (falls back gracefully).
    cover_dir = Path(EXPORT_DIR) / "temp_charts"
    cover_dir.mkdir(parents=True, exist_ok=True)
    user_label = _resolve_user_label(user_id)
    cover_path = _generate_cover_image(
        dataset_name=dataset_name,
        nb_rows=nb_rows,
        nb_cols=nb_cols,
        user_label=user_label,
        date_str=date_str,
        export_dir=cover_dir,
    )
    cover_html = _generate_cover_page_html(cover_path)

    # Build the report intro band (shown once at the top of the content pages).
    head_band = _build_report_head_html(dataset_name, nb_rows, nb_cols, date_str)

    # The cover lives on a full-bleed page; then we switch to the bordered
    # "content" page template (with the repeating footer) for everything else.
    if cover_html:
        body_prefix = (
            f"{cover_html}"
            "<pdf:nexttemplate name='content'>"
            "<pdf:nextpage>"
            f"{head_band}"
        )
    else:
        body_prefix = head_band

    if "<body>" in html_content:
        html_content = html_content.replace("<body>", f"<body>{body_prefix}", 1)
    elif "<body" in html_content:
        idx = html_content.find("<body")
        close = html_content.find(">", idx)
        if close != -1:
            html_content = (
                html_content[: close + 1] + body_prefix + html_content[close + 1 :]
            )
    else:
        html_content = body_prefix + html_content

    # 3. Generate Charts and append them to the HTML
    chart_images = _generate_charts(analytics, anomalies, selected_charts, max_charts)

    # Footer content (pulled into the @page footer frame on every content page).
    footer_html = _build_footer_html(dataset_name)

    tail_html = ""
    if chart_images:
        tail_html += "<div style='page-break-before: always;'><h2>Visualisations</h2>"
        for title, path in chart_images:
            # xhtml2pdf requires absolute paths for local images
            abs_path = os.path.abspath(path).replace("\\", "/")
            tail_html += f"<h3 class='chart-title'>{title}</h3>"
            tail_html += f"<img src='{abs_path}' style='width: 600px; max-width: 100%; margin-bottom: 20px;' />"
        tail_html += "</div>"
    tail_html += footer_html

    # Inject charts + footer right before the closing </body> tag
    if "</body>" in html_content:
        html_content = html_content.replace("</body>", f"{tail_html}</body>")
    else:
        html_content += tail_html

    # 3b. Embed Poppins (@font-face) + full premium template styling.
    font_css = _build_report_css()
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
