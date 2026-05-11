"""PySide6 upload widget for dataset import."""

import os

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QMessageBox,
    QHeaderView,
)
from PySide6.QtCore import Qt, QThread, Signal

from controllers.upload_controller import UploadController


class ETLWorker(QThread):
    """Background worker thread for running the ETL pipeline."""

    finished = Signal(object)
    error = Signal(str)

    def __init__(self, file_path: str, dataset_name: str, user_id: int) -> None:
        super().__init__()
        self._file_path = file_path
        self._dataset_name = dataset_name
        self._user_id = user_id
        self._upload_ctrl = UploadController()

    def run(self) -> None:
        """Execute the ETL pipeline in the background."""
        try:
            dataset = self._upload_ctrl.importer_fichier(
                self._file_path, self._dataset_name, self._user_id
            )
            self.finished.emit(dataset)
        except Exception as e:
            self.error.emit(str(e))


class UploadWidget(QWidget):
    """Widget for uploading and managing datasets.

    Provides file selection, ETL processing, and dataset listing.
    """

    def __init__(self, user_id: int, role: str, parent=None) -> None:
        """Initialize the upload widget.

        Args:
            user_id: Current user's ID.
            role: Current user's role.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._user_id = user_id
        self._role = role
        self._upload_ctrl = UploadController()
        self._selected_file = ""
        self._worker = None
        self._setup_ui()
        self._load_datasets()

    def _setup_ui(self) -> None:
        """Set up the widget UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Title
        title = QLabel("📁 Importer des données")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # File selection
        file_layout = QHBoxLayout()
        self._file_label = QLabel("Aucun fichier sélectionné")
        self._file_label.setStyleSheet("color: #666;")
        file_layout.addWidget(self._file_label, stretch=1)

        self._browse_btn = QPushButton("Parcourir...")
        self._browse_btn.clicked.connect(self._on_browse)
        file_layout.addWidget(self._browse_btn)
        layout.addLayout(file_layout)

        # Dataset name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Nom du dataset:"))
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Ex: Ventes Q4 2024")
        name_layout.addWidget(self._name_input)
        layout.addLayout(name_layout)

        # Import button
        self._import_btn = QPushButton("📤 Importer et traiter")
        self._import_btn.setStyleSheet(
            "QPushButton { background-color: #1a237e; color: white; "
            "padding: 8px; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background-color: #283593; }"
        )
        self._import_btn.clicked.connect(self._on_import)
        self._import_btn.setEnabled(False)
        layout.addWidget(self._import_btn)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)

        # Status label
        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

        # Datasets table
        layout.addWidget(QLabel("📋 Mes datasets:"))
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["Nom", "Lignes", "Colonnes", "Taille (Mo)", "Statut"]
        )
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        layout.addWidget(self._table)

        # Delete button
        self._delete_btn = QPushButton("🗑️ Supprimer le dataset sélectionné")
        self._delete_btn.clicked.connect(self._on_delete)
        layout.addWidget(self._delete_btn)

    def _on_browse(self) -> None:
        """Handle file browse button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un fichier de données",
            "",
            "Fichiers de données (*.csv *.xlsx *.xls);;Tous les fichiers (*)",
        )
        if file_path:
            self._selected_file = file_path
            self._file_label.setText(os.path.basename(file_path))
            self._import_btn.setEnabled(True)

            if not self._name_input.text():
                name = os.path.splitext(os.path.basename(file_path))[0]
                self._name_input.setText(name)

    def _on_import(self) -> None:
        """Handle import button click — starts ETL in background thread."""
        if not self._selected_file:
            return

        dataset_name = self._name_input.text().strip()
        if not dataset_name:
            dataset_name = os.path.splitext(os.path.basename(self._selected_file))[0]

        self._import_btn.setEnabled(False)
        self._progress_bar.setVisible(True)
        self._status_label.setText("Traitement en cours...")

        self._worker = ETLWorker(self._selected_file, dataset_name, self._user_id)
        self._worker.finished.connect(self._on_import_success)
        self._worker.error.connect(self._on_import_error)
        self._worker.start()

    def _on_import_success(self, dataset) -> None:
        """Handle successful import."""
        self._progress_bar.setVisible(False)
        self._import_btn.setEnabled(True)
        self._status_label.setText(
            f"✅ Dataset '{dataset.nom}' importé ({dataset.nb_lignes} lignes)"
        )
        self._status_label.setStyleSheet("color: green;")
        self._load_datasets()

    def _on_import_error(self, error_msg: str) -> None:
        """Handle import error."""
        self._progress_bar.setVisible(False)
        self._import_btn.setEnabled(True)
        self._status_label.setText(f"❌ Erreur: {error_msg}")
        self._status_label.setStyleSheet("color: red;")

    def _on_delete(self) -> None:
        """Handle delete button click."""
        row = self._table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Attention", "Sélectionnez un dataset à supprimer.")
            return

        dataset_id = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        dataset_name = self._table.item(row, 0).text()

        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            f"Supprimer le dataset '{dataset_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._upload_ctrl.supprimer_dataset(dataset_id, self._user_id, self._role)
                self._load_datasets()
                self._status_label.setText(f"Dataset '{dataset_name}' supprimé.")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def _load_datasets(self) -> None:
        """Reload the datasets table."""
        try:
            datasets = self._upload_ctrl.lister_datasets(self._user_id, self._role)
            self._table.setRowCount(len(datasets))

            for row, ds in enumerate(datasets):
                name_item = QTableWidgetItem(ds.nom)
                name_item.setData(Qt.ItemDataRole.UserRole, ds.id)
                self._table.setItem(row, 0, name_item)
                self._table.setItem(row, 1, QTableWidgetItem(str(ds.nb_lignes)))
                self._table.setItem(row, 2, QTableWidgetItem(str(ds.nb_colonnes)))
                self._table.setItem(row, 3, QTableWidgetItem(f"{ds.taille_mo:.2f}"))
                self._table.setItem(row, 4, QTableWidgetItem(ds.statut))
        except Exception as e:
            self._status_label.setText(f"Erreur chargement: {e}")
