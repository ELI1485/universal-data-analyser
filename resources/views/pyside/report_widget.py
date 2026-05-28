"""PySide6 report widget for generating and managing reports."""

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
)
from PySide6.QtCore import Qt, QThread, Signal

from app.Http.Controllers.report_controller import ReportController
from app.Http.Controllers.upload_controller import UploadController


class ReportWorker(QThread):
    """Background worker thread for report generation."""

    finished = Signal(object)
    error = Signal(str)

    def __init__(self, dataset_id: int, user_id: int, format: str) -> None:
        super().__init__()
        self._dataset_id = dataset_id
        self._user_id = user_id
        self._format = format
        self._report_ctrl = ReportController()

    def run(self) -> None:
        """Generate report in background."""
        try:
            report = self._report_ctrl.generer(
                self._dataset_id, self._user_id, self._format
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
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Title
        title = QLabel("📄 Rapports")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Dataset selector
        ds_layout = QHBoxLayout()
        ds_layout.addWidget(QLabel("Dataset:"))
        self._dataset_combo = QComboBox()
        ds_layout.addWidget(self._dataset_combo, stretch=1)
        layout.addLayout(ds_layout)

        # Format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
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

        # Generate button
        self._generate_btn = QPushButton("📝 Générer le rapport")
        self._generate_btn.setStyleSheet(
            "QPushButton { background-color: #1a237e; color: white; "
            "padding: 8px; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background-color: #283593; }"
        )
        self._generate_btn.clicked.connect(self._on_generate)
        layout.addWidget(self._generate_btn)

        # Progress
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        # Download button
        self._download_btn = QPushButton("⬇️ Télécharger le dernier rapport")
        self._download_btn.setEnabled(False)
        self._download_btn.clicked.connect(self._on_download)
        layout.addWidget(self._download_btn)

        # Status
        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

        # Past reports table
        layout.addWidget(QLabel("📋 Rapports précédents:"))
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(
            ["Dataset", "Format", "Taille (Ko)", "Date"]
        )
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self._table)

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
                self._table.setItem(row, 1, QTableWidgetItem(report.format.upper()))
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

        self._generate_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._status_label.setText("Génération en cours...")

        self._worker = ReportWorker(dataset_id, self._user_id, format_val)
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
            f"✅ Rapport généré ({report.taille_ko:.1f} Ko)"
        )
        self._status_label.setStyleSheet("color: green;")
        self._load_reports()

    def _on_generate_error(self, error_msg: str) -> None:
        """Handle generation error."""
        self._progress.setVisible(False)
        self._generate_btn.setEnabled(True)
        self._status_label.setText(f"❌ Erreur: {error_msg}")
        self._status_label.setStyleSheet("color: red;")

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
