"""PySide6 report widget — Streamlit-matching design."""

import os

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QRadioButton,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QButtonGroup,
    QMessageBox,
    QHeaderView,
    QProgressBar,
    QFileDialog,
    QScrollArea,
    QFrame,
    QCheckBox,
    QSpinBox,
)
from PySide6.QtCore import Qt, QThread, Signal

# Diagram options offered to the user (kept in sync with the Streamlit page).
CHART_OPTIONS = [
    "Histogramme de distribution",
    "Anomalies par algorithme",
    "Matrice de corrélation",
    "Boîte à moustaches (Boxplot)",
    "Distribution catégorielle",
]

from app.Http.Controllers.report_controller import ReportController
from app.Http.Controllers.upload_controller import UploadController
from resources.views.pyside.style_widgets import SectionTitle, SubSectionTitle, Separator


class ReportWorker(QThread):
    """Background worker thread for report generation."""

    finished = Signal(object)
    error = Signal(str)

    def __init__(
        self,
        dataset_id: int,
        user_id: int,
        format: str,
        selected_charts: list[str] | None = None,
        max_charts: int | None = None,
    ) -> None:
        super().__init__()
        self._dataset_id = dataset_id
        self._user_id = user_id
        self._format = format
        self._selected_charts = selected_charts
        self._max_charts = max_charts
        self._report_ctrl = ReportController()

    def run(self) -> None:
        """Generate report in background."""
        try:
            report = self._report_ctrl.generer(
                self._dataset_id,
                self._user_id,
                self._format,
                selected_charts=self._selected_charts,
                max_charts=self._max_charts,
            )
            self.finished.emit(report)
        except Exception as e:
            self.error.emit(str(e))


class ReportWidget(QWidget):
    """Widget for generating and managing reports.

    Provides dataset selection, format choice, and report history.
    """

    def __init__(self, user_id: int, role: str, parent=None) -> None:
        """Initialize the report widget.

        Args:
            user_id: Current user's ID.
            role: Current user's role.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._user_id = user_id
        self._role = role
        self._upload_ctrl = UploadController()
        self._report_ctrl = ReportController()
        self._last_report_path = None
        self._worker = None
        self._setup_ui()
        self._load_data()

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
        layout.addWidget(SectionTitle("Rapports", "📄"))
        layout.addWidget(Separator())

        # Generate section
        layout.addWidget(SubSectionTitle("Generer un nouveau rapport"))

        # Dataset selector
        ds_label = QLabel("Dataset")
        ds_label.setStyleSheet("font-weight: bold; background: transparent; border: none;")
        layout.addWidget(ds_label)

        self._dataset_combo = QComboBox()
        self._dataset_combo.setFixedHeight(40)
        layout.addWidget(self._dataset_combo)

        # Format selection
        format_label = QLabel("Format du rapport")
        format_label.setStyleSheet("font-weight: bold; background: transparent; border: none; margin-top: 8px;")
        layout.addWidget(format_label)

        format_layout = QHBoxLayout()
        self._format_group = QButtonGroup(self)
        self._pdf_radio = QRadioButton("PDF")
        self._pdf_radio.setChecked(True)
        self._excel_radio = QRadioButton("Excel")
        self._format_group.addButton(self._pdf_radio)
        self._format_group.addButton(self._excel_radio)
        format_layout.addWidget(self._pdf_radio)
        format_layout.addWidget(self._excel_radio)
        format_layout.addStretch()
        layout.addLayout(format_layout)

        # Diagram selection
        charts_label = QLabel("Diagrammes à inclure")
        charts_label.setStyleSheet("font-weight: bold; background: transparent; border: none; margin-top: 8px;")
        layout.addWidget(charts_label)

        charts_frame = QFrame()
        charts_frame.setStyleSheet("QFrame { background: white; border-radius: 8px; border: 1px solid #e0e0e0; }")
        charts_layout = QVBoxLayout(charts_frame)
        charts_layout.setContentsMargins(15, 10, 15, 10)
        self._chart_checks: list[QCheckBox] = []
        for label in CHART_OPTIONS:
            cb = QCheckBox(label)
            cb.setChecked(True)
            charts_layout.addWidget(cb)
            self._chart_checks.append(cb)
        layout.addWidget(charts_frame)

        # Max diagrams
        max_layout = QHBoxLayout()
        max_label = QLabel("Nombre maximum de diagrammes")
        max_label.setStyleSheet("font-weight: bold; background: transparent; border: none;")
        max_layout.addWidget(max_label)
        self._max_charts_spin = QSpinBox()
        self._max_charts_spin.setRange(1, 10)
        self._max_charts_spin.setValue(min(5, len(CHART_OPTIONS)))
        self._max_charts_spin.setFixedWidth(80)
        max_layout.addWidget(self._max_charts_spin)
        max_layout.addStretch()
        layout.addLayout(max_layout)

        # Generate button
        self._generate_btn = QPushButton("Generer le rapport")
        self._generate_btn.setFixedHeight(45)
        self._generate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._generate_btn.clicked.connect(self._on_generate)
        layout.addWidget(self._generate_btn)

        # Progress
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        self._progress.setFixedHeight(8)
        layout.addWidget(self._progress)

        # Download button
        self._download_btn = QPushButton("Telecharger le dernier rapport")
        self._download_btn.setEnabled(False)
        self._download_btn.setStyleSheet("""
            QPushButton { background-color: #3b82f6; color: white; border-radius: 6px; padding: 10px; font-weight: bold; }
            QPushButton:hover { background-color: #2563eb; }
            QPushButton:disabled { background-color: #d0d0d0; color: #888; }
        """)
        self._download_btn.clicked.connect(self._on_download)
        layout.addWidget(self._download_btn)

        # Status
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self._status_label)

        layout.addWidget(Separator())

        # Past reports table
        layout.addWidget(SubSectionTitle("Rapports precedents", "📋"))

        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(
            ["Dataset", "Format", "Taille (Ko)", "Date"]
        )
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._table.setAlternatingRowColors(True)
        self._table.setMinimumHeight(200)
        layout.addWidget(self._table)

        layout.addStretch()

        scroll.setWidget(page)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _load_data(self) -> None:
        """Load datasets and past reports."""
        try:
            datasets = self._upload_ctrl.lister_datasets(self._user_id, self._role)
            self._dataset_combo.clear()
            for ds in datasets:
                self._dataset_combo.addItem(f"{ds.nom} (ID: {ds.id})", ds.id)
        except Exception:
            pass

        self._load_reports()

    def _load_reports(self) -> None:
        """Reload the reports table."""
        try:
            reports = self._report_ctrl.lister_rapports(self._user_id, self._role)
            self._table.setRowCount(len(reports))

            for row, report in enumerate(reports):
                self._table.setItem(row, 0, QTableWidgetItem(f"Dataset #{report.dataset_id}"))

                fmt_item = QTableWidgetItem(report.format.upper())
                self._table.setItem(row, 1, fmt_item)

                self._table.setItem(row, 2, QTableWidgetItem(f"{report.taille_ko:.1f}"))

                date_str = report.genere_le.strftime("%d/%m/%Y %H:%M") if report.genere_le else "N/A"
                self._table.setItem(row, 3, QTableWidgetItem(date_str))
        except Exception:
            pass

    def _on_generate(self) -> None:
        """Handle generate button click."""
        if self._dataset_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Attention", "Sélectionnez un dataset.")
            return

        dataset_id = self._dataset_combo.currentData()
        format_val = "pdf" if self._pdf_radio.isChecked() else "excel"

        selected_charts = [cb.text() for cb in self._chart_checks if cb.isChecked()]
        if not selected_charts:
            QMessageBox.warning(
                self, "Attention", "Sélectionnez au moins un diagramme à inclure."
            )
            return
        max_charts = self._max_charts_spin.value()

        self._generate_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._status_label.setText("Generation en cours...")
        self._status_label.setStyleSheet("color: #31333f; background: transparent; border: none;")

        self._worker = ReportWorker(
            dataset_id, self._user_id, format_val, selected_charts, max_charts
        )
        self._worker.finished.connect(self._on_generate_success)
        self._worker.error.connect(self._on_generate_error)
        self._worker.start()

    def _on_generate_success(self, report) -> None:
        """Handle successful report generation."""
        self._progress.setVisible(False)
        self._generate_btn.setEnabled(True)
        self._last_report_path = report.chemin_export
        self._download_btn.setEnabled(True)
        self._status_label.setText(
            f"Rapport genere ({report.taille_ko:.1f} Ko)"
        )
        self._status_label.setStyleSheet("color: #22c55e; font-weight: bold; background: transparent; border: none;")
        self._load_reports()

    def _on_generate_error(self, error_msg: str) -> None:
        """Handle generation error."""
        self._progress.setVisible(False)
        self._generate_btn.setEnabled(True)
        self._status_label.setText(f"Erreur: {error_msg}")
        self._status_label.setStyleSheet("color: #ef4444; font-weight: bold; background: transparent; border: none;")

    def _on_download(self) -> None:
        """Handle download button click — open file location."""
        if self._last_report_path and os.path.exists(self._last_report_path):
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Enregistrer le rapport",
                os.path.basename(self._last_report_path),
            )
            if save_path:
                import shutil
                shutil.copy2(self._last_report_path, save_path)
                QMessageBox.information(
                    self, "Succès", f"Rapport enregistré: {save_path}"
                )
        else:
            QMessageBox.warning(self, "Erreur", "Fichier de rapport non disponible.")
