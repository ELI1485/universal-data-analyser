"""PySide6 analytics widget for running and displaying analyses."""

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
)
from PySide6.QtCore import Qt, QThread, Signal

from controllers.analytics_controller import AnalyticsController
from controllers.upload_controller import UploadController
from services.llm_service import LLMService
from services.visualization.visualization_service import histogramme_mpl, heatmap_mpl


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
        self._datasets = []
        self._results = None
        self._worker = None
        self._setup_ui()
        self._load_datasets()

    def _setup_ui(self) -> None:
        """Set up the widget UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Title
        title = QLabel("📈 Analyses")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Dataset selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Dataset:"))
        self._dataset_combo = QComboBox()
        selector_layout.addWidget(self._dataset_combo, stretch=1)

        self._run_btn = QPushButton("🚀 Lancer l'analyse")
        self._run_btn.setStyleSheet(
            "QPushButton { background-color: #1a237e; color: white; "
            "padding: 6px 16px; border-radius: 4px; font-weight: bold; }"
        )
        self._run_btn.clicked.connect(self._on_run_analysis)
        selector_layout.addWidget(self._run_btn)
        layout.addLayout(selector_layout)

        # Progress
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        # Results tabs
        self._tabs = QTabWidget()

        # Tab 1: Statistics
        self._stats_table = QTableWidget()
        self._stats_table.setColumnCount(8)
        self._stats_table.setHorizontalHeaderLabels(
            ["Colonne", "Moyenne", "Médiane", "Écart-type", "Min", "Max", "Q25", "Q75"]
        )
        self._stats_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._tabs.addTab(self._stats_table, "📊 Statistiques")

        # Tab 2: Anomalies
        self._anomalies_table = QTableWidget()
        self._anomalies_table.setColumnCount(5)
        self._anomalies_table.setHorizontalHeaderLabels(
            ["Ligne", "Colonne", "Score", "Algorithme", "Valeur"]
        )
        self._anomalies_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._tabs.addTab(self._anomalies_table, "⚠️ Anomalies")

        # Tab 3: Insights
        self._insights_text = QTextEdit()
        self._insights_text.setReadOnly(True)
        self._tabs.addTab(self._insights_text, "🤖 Insights IA")

        layout.addWidget(self._tabs)

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

    def _on_run_analysis(self) -> None:
        """Handle run analysis button click."""
        idx = self._dataset_combo.currentIndex()
        if idx < 0:
            QMessageBox.warning(self, "Attention", "Sélectionnez un dataset.")
            return

        dataset_id = self._dataset_combo.currentData()

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

    def _on_analysis_error(self, error_msg: str) -> None:
        """Handle analysis error."""
        self._progress.setVisible(False)
        self._run_btn.setEnabled(True)
        QMessageBox.critical(self, "Erreur d'analyse", error_msg)

    def _display_statistics(self, analytics: dict) -> None:
        """Populate the statistics table."""
        stats = analytics.get("statistiques", {}).get("colonnes", {})
        self._stats_table.setRowCount(len(stats))

        for row, (col_name, col_stats) in enumerate(stats.items()):
            self._stats_table.setItem(row, 0, QTableWidgetItem(col_name))
            self._stats_table.setItem(row, 1, QTableWidgetItem(self._fmt(col_stats.get("mean"))))
            self._stats_table.setItem(row, 2, QTableWidgetItem(self._fmt(col_stats.get("median"))))
            self._stats_table.setItem(row, 3, QTableWidgetItem(self._fmt(col_stats.get("std"))))
            self._stats_table.setItem(row, 4, QTableWidgetItem(self._fmt(col_stats.get("min"))))
            self._stats_table.setItem(row, 5, QTableWidgetItem(self._fmt(col_stats.get("max"))))
            self._stats_table.setItem(row, 6, QTableWidgetItem(self._fmt(col_stats.get("q25"))))
            self._stats_table.setItem(row, 7, QTableWidgetItem(self._fmt(col_stats.get("q75"))))

    def _display_anomalies(self, anomalies: dict) -> None:
        """Populate the anomalies table."""
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
        self._insights_text.setText("Génération des insights IA en cours...")
        try:
            llm = LLMService()
            analytics = results.get("analytics", {})
            anomalies = results.get("anomalies", {})

            stats_data = analytics.get("statistiques", {}).get("colonnes", {})
            stats_summary = ""
            for col_name, col_stats in list(stats_data.items())[:5]:
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
            self._insights_text.setText(f"Erreur génération insights: {e}")

    @staticmethod
    def _fmt(value) -> str:
        """Format a numeric value for display."""
        if value is None:
            return "N/A"
        if isinstance(value, float):
            return f"{value:.4f}"
        return str(value)
