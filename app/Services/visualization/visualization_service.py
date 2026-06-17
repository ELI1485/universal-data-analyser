"""Visualization service for generating Plotly and Matplotlib charts.

Provides functions for creating various chart types used in both
the Streamlit dashboard (Plotly) and PDF reports (Matplotlib).
"""

import logging

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

logger = logging.getLogger(__name__)


# ============================================================
# PLOTLY CHARTS (for Streamlit)
# ============================================================


def histogramme(df: pd.DataFrame, colonne: str) -> go.Figure:
    """Create a Plotly histogram for a numeric column.

    Args:
        df: The DataFrame containing the data.
        colonne: The column name to plot.

    Returns:
        A Plotly Figure object.
    """
    fig = px.histogram(
        df,
        x=colonne,
        nbins=30,
        title=f"Distribution — {colonne}",
        labels={colonne: colonne, "count": "Fréquence"},
        color_discrete_sequence=["#1a237e"],
    )
    fig.update_layout(
        xaxis_title=colonne,
        yaxis_title="Fréquence",
        template="plotly_white",
        showlegend=False,
    )
    # Add mean line
    mean_val = df[colonne].mean()
    fig.add_vline(
        x=mean_val,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Moyenne: {mean_val:.2f}",
    )
    return fig


def courbe_tendance(df: pd.DataFrame, colonne: str) -> go.Figure:
    """Create a Plotly trend line chart with rolling average.

    Args:
        df: The DataFrame containing the data.
        colonne: The numeric column to plot.

    Returns:
        A Plotly Figure object.
    """
    fig = go.Figure()

    # Raw data
    fig.add_trace(
        go.Scatter(
            x=list(range(len(df))),
            y=df[colonne],
            mode="lines",
            name="Données brutes",
            line=dict(color="#bbdefb", width=1),
            opacity=0.6,
        )
    )

    # Rolling average
    window = max(3, min(10, len(df) // 10))
    rolling_avg = df[colonne].rolling(window=window, min_periods=1).mean()
    fig.add_trace(
        go.Scatter(
            x=list(range(len(df))),
            y=rolling_avg,
            mode="lines",
            name=f"Moyenne mobile ({window})",
            line=dict(color="#1a237e", width=2),
        )
    )

    fig.update_layout(
        title=f"Tendance — {colonne}",
        xaxis_title="Index",
        yaxis_title=colonne,
        template="plotly_white",
    )
    return fig


def heatmap_correlation(df: pd.DataFrame) -> go.Figure:
    """Create a Plotly correlation heatmap for all numeric columns.

    Args:
        df: The DataFrame containing the data.

    Returns:
        A Plotly Figure object.
    """
    numeric_df = df.select_dtypes(include=["number"])
    corr_matrix = numeric_df.corr()

    fig = go.Figure(
        data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns.tolist(),
            y=corr_matrix.index.tolist(),
            colorscale="RdBu_r",
            zmin=-1,
            zmax=1,
            text=np.round(corr_matrix.values, 2),
            texttemplate="%{text}",
            textfont={"size": 9},
        )
    )
    fig.update_layout(
        title="Matrice de Corrélation",
        template="plotly_white",
        width=700,
        height=600,
    )
    return fig


def boxplot(df: pd.DataFrame, colonne: str) -> go.Figure:
    """Create a Plotly boxplot for a numeric column.

    Args:
        df: The DataFrame containing the data.
        colonne: The column name to plot.

    Returns:
        A Plotly Figure object.
    """
    fig = px.box(
        df,
        y=colonne,
        title=f"Boîte à moustaches — {colonne}",
        color_discrete_sequence=["#283593"],
    )
    fig.update_layout(
        yaxis_title=colonne,
        template="plotly_white",
        showlegend=False,
    )
    return fig


def bar_categorical_frequency(
    df: pd.DataFrame, colonne: str, top_n: int = 15
) -> go.Figure:
    """Create a horizontal bar chart of value frequencies for a categorical column.

    Used for "dominant field" visualisations such as the distribution
    of students across a ``filiere`` column or counts of orders per
    region. Categories beyond the top ``top_n`` are bucketed under
    ``"Autres"`` so the chart stays readable on high-cardinality columns.

    Args:
        df: The DataFrame containing the data.
        colonne: The categorical column to plot.
        top_n: Max number of distinct categories shown individually.

    Returns:
        A Plotly Figure object.
    """
    series = df[colonne].dropna().astype(str)
    counts = series.value_counts()
    total = int(counts.sum())

    if total == 0:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnee a afficher", showarrow=False)
        fig.update_layout(title=f"Frequence — {colonne}")
        return fig

    top = counts.head(top_n)
    if len(counts) > top_n:
        autres = int(counts.iloc[top_n:].sum())
        labels = top.index.tolist() + ["Autres"]
        values = top.values.tolist() + [autres]
    else:
        labels = top.index.tolist()
        values = top.values.tolist()

    percentages = [round(v / total * 100, 1) for v in values]
    text_labels = [f"{v} ({p}%)" for v, p in zip(values, percentages)]

    fig = go.Figure(
        data=[
            go.Bar(
                x=values,
                y=labels,
                orientation="h",
                marker_color="#93DC5C",
                text=text_labels,
                textposition="outside",
            )
        ]
    )
    fig.update_layout(
        title=f"Frequence des valeurs — {colonne}",
        xaxis_title="Nombre d'occurrences",
        yaxis_title=colonne,
        template="plotly_white",
        showlegend=False,
        yaxis={"categoryorder": "total ascending"},
        margin=dict(l=120),
    )
    return fig


def pie_categorical(df: pd.DataFrame, colonne: str, top_n: int = 8) -> go.Figure:
    """Create a Plotly donut chart for a categorical column.

    Args:
        df: The DataFrame containing the data.
        colonne: The categorical column to plot.
        top_n: Max number of slices; the rest are grouped as ``"Autres"``.

    Returns:
        A Plotly Figure object.
    """
    counts = df[colonne].dropna().astype(str).value_counts()
    if counts.empty:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnee a afficher", showarrow=False)
        fig.update_layout(title=f"Repartition — {colonne}")
        return fig

    top = counts.head(top_n)
    if len(counts) > top_n:
        autres = int(counts.iloc[top_n:].sum())
        labels = top.index.tolist() + ["Autres"]
        values = top.values.tolist() + [autres]
    else:
        labels = top.index.tolist()
        values = top.values.tolist()

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker=dict(
                    colors=[
                        "#93DC5C", "#4e732d", "#b8e986", "#6db33f",
                        "#a3d977", "#82c241", "#5b8a2e", "#3d5a1f",
                        "#cce8a8",
                    ]
                ),
            )
        ]
    )
    fig.update_layout(
        title=f"Repartition — {colonne}",
        template="plotly_white",
    )
    return fig


def scatter(df: pd.DataFrame, col_x: str, col_y: str) -> go.Figure:
    """Create a Plotly scatter plot for two numeric columns.

    Args:
        df: The DataFrame containing the data.
        col_x: The x-axis column name.
        col_y: The y-axis column name.

    Returns:
        A Plotly Figure object.
    """
    fig = px.scatter(
        df,
        x=col_x,
        y=col_y,
        title=f"Nuage de points — {col_x} vs {col_y}",
        color_discrete_sequence=["#1a237e"],
        opacity=0.6,
    )
    fig.update_layout(
        xaxis_title=col_x,
        yaxis_title=col_y,
        template="plotly_white",
    )
    # Add trendline
    if len(df) > 2:
        try:
            z = np.polyfit(df[col_x].dropna(), df[col_y].dropna(), 1)
            p = np.poly1d(z)
            x_range = np.linspace(df[col_x].min(), df[col_x].max(), 100)
            fig.add_trace(
                go.Scatter(
                    x=x_range,
                    y=p(x_range),
                    mode="lines",
                    name="Tendance linéaire",
                    line=dict(color="red", dash="dash"),
                )
            )
        except Exception:
            pass
    return fig


def anomalies_chart(anomalies: list) -> go.Figure:
    """Create a Plotly chart showing anomaly distribution by algorithm.

    Args:
        anomalies: List of anomaly dictionaries.

    Returns:
        A Plotly Figure object.
    """
    if not anomalies:
        fig = go.Figure()
        fig.add_annotation(text="Aucune anomalie détectée", showarrow=False)
        fig.update_layout(title="Anomalies Détectées")
        return fig

    # Count by algorithm
    algo_counts = {}
    for a in anomalies:
        algo = a.get("type", "inconnu")
        algo_counts[algo] = algo_counts.get(algo, 0) + 1

    fig = go.Figure(
        data=[
            go.Bar(
                x=list(algo_counts.keys()),
                y=list(algo_counts.values()),
                marker_color=["#1565c0", "#2e7d32", "#e65100"][: len(algo_counts)],
            )
        ]
    )
    fig.update_layout(
        title="Répartition des Anomalies par Algorithme",
        xaxis_title="Algorithme",
        yaxis_title="Nombre d'anomalies",
        template="plotly_white",
        showlegend=False,
    )
    return fig


# ============================================================
# MATPLOTLIB CHARTS (for PDF embedding)
# ============================================================


def histogramme_mpl(df: pd.DataFrame, colonne: str) -> plt.Figure:
    """Create a Matplotlib histogram for a numeric column.

    Args:
        df: The DataFrame containing the data.
        colonne: The column name to plot.

    Returns:
        A Matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=(8, 4))
    data = df[colonne].dropna()
    ax.hist(data, bins=30, color="#1a237e", alpha=0.7, edgecolor="white")
    ax.set_title(f"Distribution — {colonne}", fontsize=12)
    ax.set_xlabel(colonne)
    ax.set_ylabel("Fréquence")

    mean_val = data.mean()
    ax.axvline(mean_val, color="red", linestyle="--", label=f"Moyenne: {mean_val:.2f}")
    ax.legend()
    plt.tight_layout()
    return fig


def heatmap_mpl(df: pd.DataFrame) -> plt.Figure:
    """Create a Matplotlib correlation heatmap.

    Args:
        df: The DataFrame containing the data.

    Returns:
        A Matplotlib Figure object.
    """
    numeric_df = df.select_dtypes(include=["number"])
    corr_matrix = numeric_df.corr()

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(corr_matrix.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")

    cols = [c[:12] for c in corr_matrix.columns.tolist()]
    ax.set_xticks(range(len(cols)))
    ax.set_yticks(range(len(cols)))
    ax.set_xticklabels(cols, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(cols, fontsize=8)

    # Add correlation values
    for i in range(len(corr_matrix)):
        for j in range(len(corr_matrix)):
            val = corr_matrix.values[i, j]
            color = "white" if abs(val) > 0.5 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=7, color=color)

    ax.set_title("Matrice de Corrélation", fontsize=12)
    fig.colorbar(im, ax=ax, shrink=0.8)
    plt.tight_layout()
    return fig


def boxplot_mpl(df: pd.DataFrame, colonne: str) -> plt.Figure:
    """Create a Matplotlib boxplot for a numeric column.

    Args:
        df: The DataFrame containing the data.
        colonne: The numeric column name to plot.

    Returns:
        A Matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=(8, 4))
    data = df[colonne].dropna()
    ax.boxplot(
        data,
        vert=False,
        patch_artist=True,
        boxprops=dict(facecolor="#93DC5C", color="#2F6B17"),
        medianprops=dict(color="#1a237e", linewidth=2),
        flierprops=dict(marker="o", markerfacecolor="#e53935", markersize=5, alpha=0.6),
    )
    ax.set_title(f"Boîte à moustaches — {colonne}", fontsize=12)
    ax.set_xlabel(colonne)
    ax.set_yticks([])
    plt.tight_layout()
    return fig


def bar_categorical_mpl(df: pd.DataFrame, colonne: str, top_n: int = 10) -> plt.Figure:
    """Create a Matplotlib bar chart of the top categories of a column.

    Args:
        df: The DataFrame containing the data.
        colonne: The categorical column name to plot.
        top_n: Maximum number of categories to display.

    Returns:
        A Matplotlib Figure object.
    """
    fig, ax = plt.subplots(figsize=(8, 4))
    counts = df[colonne].astype(str).value_counts().head(top_n)
    ax.bar(
        [str(i)[:18] for i in counts.index],
        counts.values,
        color="#1a237e",
        alpha=0.85,
        edgecolor="white",
    )
    ax.set_title(f"Fréquence — {colonne}", fontsize=12)
    ax.set_ylabel("Effectif")
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    plt.tight_layout()
    return fig
