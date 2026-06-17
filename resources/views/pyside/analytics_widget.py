"""PySide6 analytics widget — Streamlit-matching design."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import pandas as pd

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QMessageBox,
    QHeaderView,
    QProgressBar,
    QScrollArea,
    QFrame,
    QDialog,
)
from PySide6.QtCore import Qt, QThread, Signal

import os

from app.Http.Controllers.analytics_controller import AnalyticsController
from app.Http.Controllers.upload_controller import UploadController
from app.Services.llm_service import LLMService
from app.Repositories.dataset_repository import DatasetRepository
from app.Services.visualization.visualization_service import (
    histogramme_mpl,
    heatmap_mpl,
    boxplot_mpl,
    bar_categorical_mpl,
)
from resources.views.pyside.style_widgets import MetricCard, SectionTitle, SubSectionTitle, Separator


class AnalysisWorker(QThread):
    """Background worker thread for running analysis."""

    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, dataset_id: int, user_id: int) -> None:
        super().__init__()
        self._dataset_id = dataset_id
        self._user_id = user_id
        self._analytics_ctrl = AnalyticsController()

    def run(self) -> None:
        """Execute analysis in background."""
        try:
            results = self._analytics_ctrl.executer_analyses(
                self._dataset_id, self._user_id
            )
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class AnalyticsWidget(QWidget):
    """Widget for running analytics and viewing results.

    Provides dataset selection, analysis execution, and tabbed results view.
    """

    def __init__(self, user_id: int, role: str, parent=None) -> None:
        """Initialize the analytics widget.

        Args:
            user_id: Current user's ID.
            role: Current user's role.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._user_id = user_id
        self._role = role
        self._upload_ctrl = UploadController()
        self._ds_repo = DatasetRepository()
        self._datasets = []
        self._results = None
        self._worker = None
        self._viz_df = None  # DataFrame loaded for the Visualisations tab
        self._viz_figures = []  # Track matplotlib figures to close on refresh
        self._setup_ui()
        self._load_datasets()

    def _setup_ui(self) -> None:
        """Set up the widget UI components."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #f8f9fc; }")

        page = QWidget()
        page.setStyleSheet("background-color: #f8f9fc;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(12)

        # Title
        layout.addWidget(SectionTitle("Analyses", "📈"))
        layout.addWidget(Separator())

        # Dataset selector
        selector_layout = QHBoxLayout()
        ds_label = QLabel("Dataset:")
        ds_label.setStyleSheet("font-weight: bold; font-size: 14px; background: transparent; border: none;")
        selector_layout.addWidget(ds_label)

        self._dataset_combo = QComboBox()
        self._dataset_combo.setFixedHeight(40)
        selector_layout.addWidget(self._dataset_combo, stretch=1)

        # Preview button — lets the user inspect the raw data before analysis.
        self._preview_btn = QPushButton("Aperçu")
        self._preview_btn.setFixedHeight(40)
        self._preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._preview_btn.setToolTip("Afficher les 10 premières lignes du dataset")
        self._preview_btn.clicked.connect(self._on_preview)
        selector_layout.addWidget(self._preview_btn)

        self._run_btn = QPushButton("Lancer l'analyse")
        self._run_btn.setFixedHeight(40)
        self._run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._run_btn.clicked.connect(self._on_run_analysis)
        selector_layout.addWidget(self._run_btn)
        layout.addLayout(selector_layout)

        # Progress
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        self._progress.setFixedHeight(8)
        layout.addWidget(self._progress)

        layout.addWidget(Separator())

        # Results tabs
        self._tabs = QTabWidget()

        # Tab 1: Statistics
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setContentsMargins(10, 10, 10, 10)

        # Multi-sheet (Excel) breakdown banner — hidden until populated.
        self._sheet_label = QLabel("")
        self._sheet_label.setWordWrap(True)
        self._sheet_label.setStyleSheet(
            "QLabel { background-color: #EAF6E1; color: #2F6B17; "
            "border: 1px solid #93DC5C; border-radius: 6px; padding: 8px 12px; "
            "font-weight: 500; }"
        )
        self._sheet_label.setVisible(False)
        stats_layout.addWidget(self._sheet_label)

        # KPI cards placeholder
        self._kpi_layout = QHBoxLayout()
        self._kpi_layout.setSpacing(10)
        stats_layout.addLayout(self._kpi_layout)

        stats_layout.addWidget(SubSectionTitle("Colonnes numeriques", "🔢"))
        self._stats_table = QTableWidget()
        self._stats_table.setColumnCount(8)
        self._stats_table.setHorizontalHeaderLabels(
            ["Colonne", "Moyenne", "Mediane", "Ecart-type", "Min", "Max", "Q25", "Q75"]
        )
        self._stats_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._stats_table.setAlternatingRowColors(True)
        stats_layout.addWidget(self._stats_table)

        stats_layout.addWidget(SubSectionTitle("Colonnes categorielles", "🏷️"))
        self._cat_table = QTableWidget()
        self._cat_table.setColumnCount(4)
        self._cat_table.setHorizontalHeaderLabels(
            ["Colonne", "Valeurs uniques", "Mode", "Frequence mode (%)"]
        )
        self._cat_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._cat_table.setAlternatingRowColors(True)
        stats_layout.addWidget(self._cat_table)

        self._tabs.addTab(stats_widget, "Statistiques")

        # Tab 2: Anomalies
        anom_widget = QWidget()
        anom_layout = QVBoxLayout(anom_widget)
        anom_layout.setContentsMargins(10, 10, 10, 10)

        self._anom_kpi_layout = QHBoxLayout()
        self._anom_kpi_layout.setSpacing(10)
        anom_layout.addLayout(self._anom_kpi_layout)

        self._anomalies_table = QTableWidget()
        self._anomalies_table.setColumnCount(5)
        self._anomalies_table.setHorizontalHeaderLabels(
            ["Ligne", "Colonne", "Score", "Algorithme", "Valeur"]
        )
        self._anomalies_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._anomalies_table.setAlternatingRowColors(True)
        anom_layout.addWidget(self._anomalies_table)

        self._tabs.addTab(anom_widget, "Anomalies")

        # Tab 3: Insights
        insights_widget = QWidget()
        insights_layout = QVBoxLayout(insights_widget)
        insights_layout.setContentsMargins(10, 10, 10, 10)

        self._insights_text = QTextEdit()
        self._insights_text.setReadOnly(True)
        self._insights_text.setStyleSheet("border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; background: white;")
        insights_layout.addWidget(self._insights_text)

        self._tabs.addTab(insights_widget, "Insights IA")

        # Tab 4: Visualisations (charts — parity with the Streamlit app)
        self._tabs.addTab(self._build_visualizations_tab(), "Visualisations")

        layout.addWidget(self._tabs)
        layout.addStretch()

        scroll.setWidget(page)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _load_datasets(self) -> None:
        """Load available datasets into the combo box."""
        try:
            self._datasets = self._upload_ctrl.lister_datasets(
                self._user_id, self._role
            )
            self._dataset_combo.clear()
            for ds in self._datasets:
                self._dataset_combo.addItem(f"{ds.nom} (ID: {ds.id})", ds.id)
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur chargement datasets: {e}")

    @staticmethod
    def _read_dataframe(path: str, nrows: int | None = None) -> pd.DataFrame:
        """Read a dataset file (CSV or Excel) into a DataFrame.

        Args:
            path: Filesystem path to the dataset.
            nrows: Optional limit on the number of rows to read.

        Returns:
            The loaded DataFrame.
        """
        if str(path).lower().endswith((".xlsx", ".xls")):
            return pd.read_excel(path, nrows=nrows)
        return pd.read_csv(path, nrows=nrows)

    def _selected_dataset(self):
        """Return the currently selected Dataset model, or None."""
        dataset_id = self._dataset_combo.currentData()
        if dataset_id is None:
            return None
        return self._ds_repo.find_by_id(dataset_id)

    def _on_preview(self) -> None:
        """Show the first 10 rows of the selected dataset in a popup table."""
        dataset = self._selected_dataset()
        if not dataset:
            QMessageBox.warning(self, "Attention", "Sélectionnez un dataset.")
            return
        if not dataset.chemin_fichier or not os.path.exists(dataset.chemin_fichier):
            QMessageBox.warning(
                self, "Fichier introuvable",
                "Le fichier est introuvable. Veuillez ré-importer le dataset.",
            )
            return
        try:
            df = self._read_dataframe(dataset.chemin_fichier, nrows=10)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de lire l'aperçu: {e}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Aperçu — {dataset.nom}")
        dialog.resize(820, 360)
        dlg_layout = QVBoxLayout(dialog)

        caption = QLabel(f"Affichage de {len(df)} lignes sur {dataset.nb_lignes}")
        caption.setStyleSheet("font-weight: bold; padding: 4px;")
        dlg_layout.addWidget(caption)

        table = QTableWidget()
        table.setColumnCount(len(df.columns))
        table.setRowCount(len(df))
        table.setHorizontalHeaderLabels([str(c) for c in df.columns])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setAlternatingRowColors(True)
        for r in range(len(df)):
            for c in range(len(df.columns)):
                table.setItem(r, c, QTableWidgetItem(str(df.iat[r, c])))
        dlg_layout.addWidget(table)
        dialog.exec()

    def _on_run_analysis(self) -> None:
        """Handle run analysis button click."""
        idx = self._dataset_combo.currentIndex()
        if idx < 0:
            QMessageBox.warning(self, "Attention", "Sélectionnez un dataset.")
            return

        dataset_id = self._dataset_combo.currentData()
        self._current_dataset_id = dataset_id

        self._run_btn.setEnabled(False)
        self._progress.setVisible(True)

        self._worker = AnalysisWorker(dataset_id, self._user_id)
        self._worker.finished.connect(self._on_analysis_complete)
        self._worker.error.connect(self._on_analysis_error)
        self._worker.start()

    def _on_analysis_complete(self, results: dict) -> None:
        """Handle analysis completion."""
        self._progress.setVisible(False)
        self._run_btn.setEnabled(True)
        self._results = results

        self._display_statistics(results.get("analytics", {}))
        self._display_anomalies(results.get("anomalies", {}))
        self._display_insights(results)
        self._populate_visualizations(getattr(self, "_current_dataset_id", None))

    def _on_analysis_error(self, error_msg: str) -> None:
        """Handle analysis error."""
        self._progress.setVisible(False)
        self._run_btn.setEnabled(True)
        QMessageBox.critical(self, "Erreur d'analyse", error_msg)

    def _display_statistics(self, analytics: dict) -> None:
        """Populate the statistics tables and KPI cards."""
        # Multi-sheet breakdown banner
        sheet_breakdown = analytics.get("sheet_breakdown") or {}
        if len(sheet_breakdown) > 1:
            details = ", ".join(
                f"{nom} ({infos.get('nb_lignes', 0)} lignes)"
                for nom, infos in sheet_breakdown.items()
            )
            self._sheet_label.setText(
                f"Ce fichier contient {len(sheet_breakdown)} feuilles : {details}"
            )
            self._sheet_label.setVisible(True)
        else:
            self._sheet_label.setVisible(False)

        # KPI cards
        self._clear_layout(self._kpi_layout)
        kpis = analytics.get("kpis", {})
        if kpis:
            self._kpi_layout.addWidget(MetricCard("Total Lignes", str(kpis.get("total_rows", "N/A")), "📋"))
            self._kpi_layout.addWidget(MetricCard("Total Colonnes", str(kpis.get("total_columns", "N/A")), "📊"))
            self._kpi_layout.addWidget(MetricCard("Completude", f"{kpis.get('completeness_rate', 0):.1f}%", "✅"))
            self._kpi_layout.addWidget(MetricCard("Memoire", f"{kpis.get('memory_usage_mb', 0):.2f} Mo", "💾"))

        stats = analytics.get("statistiques", {}).get("colonnes", {})

        # Split numeric vs categorical
        numeric_rows = {}
        categorical_rows = {}
        for col_name, col_stats in stats.items():
            kind = col_stats.get("_kind", "numeric")
            if kind == "categorical":
                categorical_rows[col_name] = col_stats
            else:
                numeric_rows[col_name] = col_stats

        # Numeric table
        self._stats_table.setRowCount(len(numeric_rows))
        for row, (col_name, col_stats) in enumerate(numeric_rows.items()):
            self._stats_table.setItem(row, 0, QTableWidgetItem(col_name))
            self._stats_table.setItem(row, 1, QTableWidgetItem(self._fmt(col_stats.get("mean"))))
            self._stats_table.setItem(row, 2, QTableWidgetItem(self._fmt(col_stats.get("median"))))
            self._stats_table.setItem(row, 3, QTableWidgetItem(self._fmt(col_stats.get("std"))))
            self._stats_table.setItem(row, 4, QTableWidgetItem(self._fmt(col_stats.get("min"))))
            self._stats_table.setItem(row, 5, QTableWidgetItem(self._fmt(col_stats.get("max"))))
            self._stats_table.setItem(row, 6, QTableWidgetItem(self._fmt(col_stats.get("q25"))))
            self._stats_table.setItem(row, 7, QTableWidgetItem(self._fmt(col_stats.get("q75"))))

        # Categorical table
        self._cat_table.setRowCount(len(categorical_rows))
        for row, (col_name, col_stats) in enumerate(categorical_rows.items()):
            self._cat_table.setItem(row, 0, QTableWidgetItem(col_name))
            self._cat_table.setItem(row, 1, QTableWidgetItem(str(col_stats.get("unique_count", "N/A"))))
            self._cat_table.setItem(row, 2, QTableWidgetItem(str(col_stats.get("mode", "N/A"))))
            self._cat_table.setItem(row, 3, QTableWidgetItem(self._fmt(col_stats.get("mode_frequency_pct"))))

    def _display_anomalies(self, anomalies: dict) -> None:
        """Populate the anomalies table and KPI cards."""
        # KPI cards
        self._clear_layout(self._anom_kpi_layout)
        total = anomalies.get("total", 0)
        resume = anomalies.get("resume", {})

        self._anom_kpi_layout.addWidget(MetricCard("Total Anomalies", str(total), "⚠️"))
        self._anom_kpi_layout.addWidget(MetricCard("Z-Score", str(resume.get("zscore_count", 0)), "📊"))
        self._anom_kpi_layout.addWidget(MetricCard("IQR", str(resume.get("iqr_count", 0)), "🔍"))
        self._anom_kpi_layout.addWidget(MetricCard("Isolation Forest", str(resume.get("isolation_count", 0)), "🌳"))

        all_anom = (
            anomalies.get("zscore", [])
            + anomalies.get("iqr", [])
            + anomalies.get("isolation", [])
        )
        all_anom.sort(key=lambda x: x.get("score", 0), reverse=True)
        display_anom = all_anom[:200]

        self._anomalies_table.setRowCount(len(display_anom))
        for row, a in enumerate(display_anom):
            self._anomalies_table.setItem(row, 0, QTableWidgetItem(str(a.get("ligne", ""))))
            self._anomalies_table.setItem(row, 1, QTableWidgetItem(str(a.get("colonne", ""))))
            self._anomalies_table.setItem(row, 2, QTableWidgetItem(f"{a.get('score', 0):.3f}"))
            self._anomalies_table.setItem(row, 3, QTableWidgetItem(a.get("type", "")))
            self._anomalies_table.setItem(row, 4, QTableWidgetItem(self._fmt(a.get("valeur"))))

    def _display_insights(self, results: dict) -> None:
        """Generate and display AI insights."""
        self._insights_text.setText("Generation des insights IA en cours...")
        try:
            llm = LLMService()
            analytics = results.get("analytics", {})
            anomalies = results.get("anomalies", {})

            stats_data = analytics.get("statistiques", {}).get("colonnes", {})
            stats_summary = ""
            for col_name, col_stats in list(stats_data.items())[:5]:
                kind = col_stats.get("_kind", "numeric")
                if kind == "categorical":
                    stats_summary += (
                        f"  {col_name} (categoriel): "
                        f"{col_stats.get('unique_count')} valeurs uniques, "
                        f"mode='{col_stats.get('mode')}'\n"
                    )
                else:
                    stats_summary += f"  {col_name}: moy={col_stats.get('mean')}\n"

            context = {
                "dataset_name": analytics.get("dataset_info", {}).get("nom", "Inconnu"),
                "nb_rows": analytics.get("dataset_info", {}).get("nb_lignes", 0),
                "nb_cols": analytics.get("dataset_info", {}).get("nb_colonnes", 0),
                "stats_summary": stats_summary,
                "anomalies_count": anomalies.get("total", 0),
                "top_anomalies": (anomalies.get("zscore", []) + anomalies.get("iqr", []))[:5],
                "correlations": analytics.get("kpis", {}).get("top_correlated_pairs", []),
            }

            insights = llm.generer_insights(context)
            self._insights_text.setText(insights)
        except Exception as e:
            self._insights_text.setText(f"Erreur generation insights: {e}")

    # ------------------------------------------------------------------
    # Visualisations tab (charts) — parity with the Streamlit app
    # ------------------------------------------------------------------
    def _build_visualizations_tab(self) -> QWidget:
        """Build the Visualisations tab (column selectors + chart area)."""
        viz_widget = QWidget()
        viz_layout = QVBoxLayout(viz_widget)
        viz_layout.setContentsMargins(10, 10, 10, 10)
        viz_layout.setSpacing(10)

        # Column selectors
        controls = QHBoxLayout()
        num_lbl = QLabel("Colonne numérique:")
        num_lbl.setStyleSheet("font-weight: bold; background: transparent; border: none;")
        controls.addWidget(num_lbl)
        self._viz_num_combo = QComboBox()
        self._viz_num_combo.setMinimumWidth(180)
        self._viz_num_combo.currentIndexChanged.connect(self._refresh_visualizations)
        controls.addWidget(self._viz_num_combo)

        cat_lbl = QLabel("Colonne catégorielle:")
        cat_lbl.setStyleSheet("font-weight: bold; background: transparent; border: none;")
        controls.addWidget(cat_lbl)
        self._viz_cat_combo = QComboBox()
        self._viz_cat_combo.setMinimumWidth(180)
        self._viz_cat_combo.currentIndexChanged.connect(self._refresh_visualizations)
        controls.addWidget(self._viz_cat_combo)
        controls.addStretch()
        viz_layout.addLayout(controls)

        # Placeholder / chart container
        self._viz_placeholder = QLabel(
            "Lancez une analyse pour afficher les visualisations."
        )
        self._viz_placeholder.setStyleSheet("color: #888; padding: 20px;")
        self._viz_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        viz_layout.addWidget(self._viz_placeholder)

        self._viz_charts_layout = QVBoxLayout()
        self._viz_charts_layout.setSpacing(16)
        viz_layout.addLayout(self._viz_charts_layout)
        viz_layout.addStretch()

        return viz_widget

    def _make_chart_frame(self, title: str, fig) -> QFrame:
        """Wrap a matplotlib figure in a titled, white-background frame."""
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame { background-color: white; border: 1px solid #e0e0e0; "
            "border-radius: 8px; }"
        )
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(12, 10, 12, 12)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: #1a237e; "
            "background: transparent; border: none;"
        )
        fl.addWidget(title_lbl)
        canvas = FigureCanvas(fig)
        canvas.setMinimumHeight(320)
        fl.addWidget(canvas)
        self._viz_figures.append(fig)
        return frame

    def _populate_visualizations(self, dataset_id) -> None:
        """Load the dataset and populate the visualisation column selectors."""
        self._viz_df = None
        if dataset_id is None:
            return
        try:
            dataset = self._ds_repo.find_by_id(dataset_id)
            if not dataset or not dataset.chemin_fichier or not os.path.exists(
                dataset.chemin_fichier
            ):
                self._viz_placeholder.setText(
                    "Fichier introuvable. Impossible d'afficher les visualisations."
                )
                self._viz_placeholder.setVisible(True)
                return
            self._viz_df = self._read_dataframe(dataset.chemin_fichier)
        except Exception as e:
            self._viz_placeholder.setText(f"Erreur de chargement des données: {e}")
            self._viz_placeholder.setVisible(True)
            return

        df = self._viz_df
        numeric_cols = list(df.select_dtypes(include=["number"]).columns)
        categorical_cols = [c for c in df.columns if c not in numeric_cols]

        # Block signals while repopulating to avoid premature refreshes.
        self._viz_num_combo.blockSignals(True)
        self._viz_cat_combo.blockSignals(True)
        self._viz_num_combo.clear()
        self._viz_num_combo.addItems([str(c) for c in numeric_cols])
        self._viz_cat_combo.clear()
        self._viz_cat_combo.addItems([str(c) for c in categorical_cols])
        self._viz_num_combo.blockSignals(False)
        self._viz_cat_combo.blockSignals(False)

        self._refresh_visualizations()

    def _refresh_visualizations(self) -> None:
        """Render the four charts based on the current column selections."""
        if self._viz_df is None:
            return

        # Close previous figures and clear the chart container.
        for fig in self._viz_figures:
            try:
                plt.close(fig)
            except Exception:
                pass
        self._viz_figures = []
        self._clear_layout(self._viz_charts_layout)
        self._viz_placeholder.setVisible(False)

        df = self._viz_df
        num_col = self._viz_num_combo.currentText()
        cat_col = self._viz_cat_combo.currentText()

        try:
            if num_col and num_col in df.columns:
                self._viz_charts_layout.addWidget(
                    self._make_chart_frame(
                        f"Histogramme — {num_col}", histogramme_mpl(df, num_col)
                    )
                )
                self._viz_charts_layout.addWidget(
                    self._make_chart_frame(
                        f"Boîte à moustaches — {num_col}", boxplot_mpl(df, num_col)
                    )
                )

            if len(df.select_dtypes(include=["number"]).columns) >= 2:
                self._viz_charts_layout.addWidget(
                    self._make_chart_frame(
                        "Matrice de corrélation", heatmap_mpl(df)
                    )
                )

            if cat_col and cat_col in df.columns:
                self._viz_charts_layout.addWidget(
                    self._make_chart_frame(
                        f"Fréquence — {cat_col}", bar_categorical_mpl(df, cat_col)
                    )
                )
        except Exception as e:
            err = QLabel(f"Erreur lors du rendu des graphiques: {e}")
            err.setStyleSheet("color: #e53935; padding: 10px;")
            self._viz_charts_layout.addWidget(err)

    def _clear_layout(self, layout):
        """Remove all widgets from a layout."""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    @staticmethod
    def _fmt(value) -> str:
        """Format a numeric value for display."""
        if value is None:
            return "N/A"
        if isinstance(value, float):
            return f"{value:.4f}"
        return str(value)
