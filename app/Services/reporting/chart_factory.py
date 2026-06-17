"""Shared chart factory for report generation.

Builds matplotlib chart images that can be embedded in both the PDF and
Excel reports. Centralising the chart logic here lets the PDF and Excel
generators share the exact same diagrams and the exact same
user-selection / max-count rules.

Available chart types (the keys are the French labels exposed in the UI):
    - "Histogramme de distribution"
    - "Anomalies par algorithme"
    - "Matrice de corrélation"
    - "Boîte à moustaches (Boxplot)"
    - "Distribution catégorielle"
"""

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from config.settings import EXPORT_DIR

logger = logging.getLogger(__name__)

# Canonical chart labels (must match the options shown in the UI).
CHART_HISTOGRAM = "Histogramme de distribution"
CHART_ANOMALIES = "Anomalies par algorithme"
CHART_CORRELATION = "Matrice de corrélation"
CHART_BOXPLOT = "Boîte à moustaches (Boxplot)"
CHART_CATEGORICAL = "Distribution catégorielle"

# The default order in which charts appear when no explicit selection is made.
DEFAULT_CHART_ORDER = [
    CHART_HISTOGRAM,
    CHART_ANOMALIES,
    CHART_CORRELATION,
    CHART_BOXPLOT,
    CHART_CATEGORICAL,
]

# Display titles used as headings in the exported report (can differ slightly
# from the selection label for clarity).
_CHART_TITLES = {
    CHART_HISTOGRAM: "Histogramme de distribution",
    CHART_ANOMALIES: "Répartition des anomalies par algorithme",
    CHART_CORRELATION: "Matrice de corrélation",
    CHART_BOXPLOT: "Boîte à moustaches (Boxplot)",
    CHART_CATEGORICAL: "Distribution catégorielle",
}


def _normalize_selection(selected_charts, max_charts) -> list[str]:
    """Resolve the ordered list of chart labels to generate.

    Args:
        selected_charts: User-selected chart labels, or None for "all".
        max_charts: Maximum number of charts to keep, or None for "no limit".

    Returns:
        An ordered, de-duplicated list of valid chart labels to build.
    """
    if selected_charts:
        # Keep only known labels, preserving the canonical display order.
        wanted = set(selected_charts)
        ordered = [c for c in DEFAULT_CHART_ORDER if c in wanted]
    else:
        ordered = list(DEFAULT_CHART_ORDER)

    if max_charts is not None:
        try:
            limit = int(max_charts)
            if limit >= 0:
                ordered = ordered[:limit]
        except (TypeError, ValueError):
            logger.warning("max_charts invalide (%r), ignoré.", max_charts)

    return ordered


def generate_charts(
    analytics: dict,
    anomalies: dict,
    selected_charts: list[str] | None = None,
    max_charts: int | None = None,
) -> list[tuple[str, str]]:
    """Generate the requested chart images for embedding in a report.

    Args:
        analytics: Analytics results dictionary.
        anomalies: Anomalies results dictionary.
        selected_charts: Chart labels chosen by the user. When None, all
            available charts are generated (backward-compatible default).
        max_charts: Maximum number of charts to export. When None, no limit.

    Returns:
        A list of (title, filepath) tuples for the generated charts. Only
        charts that could actually be built (data available) are returned.
    """
    wanted = _normalize_selection(selected_charts, max_charts)
    if not wanted:
        return []

    export_dir = Path(EXPORT_DIR) / "temp_charts"
    export_dir.mkdir(parents=True, exist_ok=True)

    builders = {
        CHART_HISTOGRAM: _build_histogram,
        CHART_ANOMALIES: _build_anomalies_bar,
        CHART_CORRELATION: _build_correlation_heatmap,
        CHART_BOXPLOT: _build_boxplot,
        CHART_CATEGORICAL: _build_categorical_distribution,
    }

    charts: list[tuple[str, str]] = []
    for label in wanted:
        builder = builders.get(label)
        if builder is None:
            continue
        try:
            result = builder(analytics, anomalies, export_dir)
            if result is not None:
                charts.append((_CHART_TITLES.get(label, label), result))
        except Exception as e:  # pragma: no cover - defensive
            logger.warning("Erreur génération du graphique '%s': %s", label, e)
            plt.close("all")

    return charts


def _build_histogram(analytics: dict, anomalies: dict, export_dir: Path) -> str | None:
    """Histogram of the first numeric column (synthetic from mean/std)."""
    stats_data = analytics.get("statistiques", {}).get("colonnes", {})
    numeric = [
        (name, st)
        for name, st in stats_data.items()
        if st.get("_kind", "numeric") == "numeric"
    ]
    if not numeric:
        return None

    first_col, col_stats = numeric[0]
    mean = col_stats.get("mean")
    std = col_stats.get("std")
    if mean is None or not std or std <= 0:
        return None

    fig, ax = plt.subplots(figsize=(8, 4))
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
    return chart_path


def _build_anomalies_bar(analytics: dict, anomalies: dict, export_dir: Path) -> str | None:
    """Bar chart of anomaly counts per detection algorithm."""
    resume = anomalies.get("resume", {})
    if not resume:
        return None

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
    for i, count in enumerate(counts):
        ax.text(i, count + 0.5, str(count), ha="center", fontweight="bold")

    chart_path = str(export_dir / "anomalies_bar.png")
    fig.savefig(chart_path, dpi=100, bbox_inches="tight")
    plt.close(fig)
    return chart_path


def _build_correlation_heatmap(analytics: dict, anomalies: dict, export_dir: Path) -> str | None:
    """Correlation matrix heatmap of numeric columns."""
    kpis = analytics.get("kpis", {})
    corr_matrix = kpis.get("correlation_matrix", {})
    if not corr_matrix or len(corr_matrix) < 2:
        return None

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
    return chart_path


def _build_boxplot(analytics: dict, anomalies: dict, export_dir: Path) -> str | None:
    """Boxplot built from each numeric column's five-number summary.

    Uses the precomputed min / Q25 / median / Q75 / max from the descriptive
    statistics so no raw data reload is required.
    """
    stats_data = analytics.get("statistiques", {}).get("colonnes", {})
    bxp_stats = []
    labels = []
    for name, st in stats_data.items():
        if st.get("_kind", "numeric") != "numeric":
            continue
        q1, med, q3 = st.get("q25"), st.get("median"), st.get("q75")
        lo, hi = st.get("min"), st.get("max")
        if None in (q1, med, q3, lo, hi):
            continue
        bxp_stats.append(
            {
                "label": name[:12],
                "whislo": lo,
                "q1": q1,
                "med": med,
                "q3": q3,
                "whishi": hi,
                "fliers": [],
            }
        )
        labels.append(name[:12])
        if len(bxp_stats) >= 8:  # keep the chart readable
            break

    if not bxp_stats:
        return None

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bp = ax.bxp(bxp_stats, showfliers=False, patch_artist=True)
    for patch in bp["boxes"]:
        patch.set_facecolor("#93DC5C")
        patch.set_alpha(0.7)
    for median in bp["medians"]:
        median.set_color("#16a34a")
        median.set_linewidth(2)
    ax.set_title("Boîte à moustaches — colonnes numériques", fontsize=12)
    ax.set_ylabel("Valeur")
    ax.tick_params(axis="x", labelrotation=45)

    chart_path = str(export_dir / "boxplot.png")
    fig.savefig(chart_path, dpi=100, bbox_inches="tight")
    plt.close(fig)
    return chart_path


def _build_categorical_distribution(
    analytics: dict, anomalies: dict, export_dir: Path
) -> str | None:
    """Bar chart of the top categories of the most relevant categorical column."""
    stats_data = analytics.get("statistiques", {}).get("colonnes", {})

    # Prefer a "dominant" categorical column; otherwise the first one with
    # usable top-value frequencies.
    candidates = [
        (name, st)
        for name, st in stats_data.items()
        if st.get("_kind") == "categorical" and st.get("top_values")
    ]
    if not candidates:
        return None

    candidates.sort(key=lambda kv: kv[1].get("is_dominant", False), reverse=True)
    col_name, col_stats = candidates[0]

    top_values = col_stats.get("top_values", [])[:10]
    if not top_values:
        return None

    labels = [str(item.get("value", ""))[:15] for item in top_values]
    counts = [item.get("count", 0) for item in top_values]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(labels, counts, color="#80C64A", edgecolor="white")
    ax.set_title(f"Distribution catégorielle — {col_name}", fontsize=12)
    ax.set_ylabel("Effectif")
    ax.tick_params(axis="x", labelrotation=45)
    for i, count in enumerate(counts):
        ax.text(i, count, str(count), ha="center", va="bottom", fontsize=8, fontweight="bold")

    fig.tight_layout()
    chart_path = str(export_dir / "categorical_distribution.png")
    fig.savefig(chart_path, dpi=100, bbox_inches="tight")
    plt.close(fig)
    return chart_path
