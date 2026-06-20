"""PySide6 dataset comparison widget — Streamlit-matching design.

Mirrors ``resources/views/streamlit/comparison_page.py``: lets the user pick
two datasets (ancien / nouveau), runs the comparison in a background thread,
and shows schema changes, statistical drift, and an anomaly comparison.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QProgressBar,
    QScrollArea,
    QTabWidget,
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer

from app.Http.Controllers.comparison_controller import ComparisonController
from app.Http.Controllers.upload_controller import UploadController
from resources.views.pyside.style_widgets import (
    MetricCard,
    SectionTitle,
    SubSectionTitle,
    Separator,
)


class ComparisonWorker(QThread):
    """Background worker thread for dataset comparison."""

    finished = Signal(object)
    error = Signal(str)

    def __init__(
        self, id_ancien: int, id_nouveau: int, user_id: int, role: str
    ) -> None:
        super().__init__()
        self._id_ancien = id_ancien
        self._id_nouveau = id_nouveau
        self._user_id = user_id
        self._role = role
        self._comparison_ctrl = ComparisonController()

    def run(self) -> None:
        """Run the comparison in background."""
        try:
            result = self._comparison_ctrl.comparer(
                self._id_ancien, self._id_nouveau, self._user_id, self._role
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class ComparisonWidget(QWidget):
    """Widget for side-by-side comparison of two datasets."""

    def __init__(self, user_id: int, role: str, parent=None) -> None:
        """Initialize the comparison widget.

        Args:
            user_id: Current user's ID.
            role: Current user's role.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._user_id = user_id
        self._role = role
        self._upload_ctrl = UploadController()
        self._worker = None
        self._setup_ui()
        QTimer.singleShot(0, self._load_data)

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

        layout.addWidget(SectionTitle("Comparaison de datasets", "\u21c4"))
        layout.addWidget(Separator())

        # Dataset selectors
        selectors_layout = QHBoxLayout()
        selectors_layout.setSpacing(20)

        ancien_box = QVBoxLayout()
        ancien_label = QLabel("Dataset de reference (ancien)")
        ancien_label.setStyleSheet("font-weight: bold; background: transparent; border: none;")
        ancien_box.addWidget(ancien_label)
        self._ancien_combo = QComboBox()
        self._ancien_combo.setFixedHeight(40)
        ancien_box.addWidget(self._ancien_combo)
        selectors_layout.addLayout(ancien_box)

        nouveau_box = QVBoxLayout()
        nouveau_label = QLabel("Dataset actuel (nouveau)")
        nouveau_label.setStyleSheet("font-weight: bold; background: transparent; border: none;")
        nouveau_box.addWidget(nouveau_label)
        self._nouveau_combo = QComboBox()
        self._nouveau_combo.setFixedHeight(40)
        nouveau_box.addWidget(self._nouveau_combo)
        selectors_layout.addLayout(nouveau_box)

        layout.addLayout(selectors_layout)

        # Compare button
        self._compare_btn = QPushButton("Comparer les datasets")
        self._compare_btn.setFixedHeight(45)
        self._compare_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._compare_btn.clicked.connect(self._on_compare)
        layout.addWidget(self._compare_btn)

        # Progress
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setVisible(False)
        self._progress.setFixedHeight(8)
        layout.addWidget(self._progress)

        # Status / info label
        self._status_label = QLabel(
            "Selectionnez deux datasets differents puis lancez la comparaison."
        )
        self._status_label.setStyleSheet("color: #555; background: transparent; border: none;")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        layout.addWidget(Separator())

        # Results container (populated after a comparison)
        self._results_container = QWidget()
        self._results_container.setStyleSheet("background: transparent;")
        self._results_layout = QVBoxLayout(self._results_container)
        self._results_layout.setContentsMargins(0, 0, 0, 0)
        self._results_layout.setSpacing(12)
        layout.addWidget(self._results_container)

        layout.addStretch()

        scroll.setWidget(page)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _load_data(self) -> None:
        """Load datasets into the selectors."""
        try:
            datasets = self._upload_ctrl.lister_datasets(self._user_id, self._role)
            self._ancien_combo.clear()
            self._nouveau_combo.clear()
            for ds in datasets:
                label = f"{ds.nom} (ID: {ds.id})"
                self._ancien_combo.addItem(label, ds.id)
                self._nouveau_combo.addItem(label, ds.id)
            # Default the "nouveau" selector to the second dataset if available.
            if self._nouveau_combo.count() > 1:
                self._nouveau_combo.setCurrentIndex(1)

            if len(datasets) < 2:
                self._compare_btn.setEnabled(False)
                self._status_label.setText(
                    "Vous devez avoir au moins 2 datasets importes pour effectuer "
                    "une comparaison. Importez d'abord vos fichiers de donnees."
                )
        except Exception as e:
            self._status_label.setText(f"Erreur chargement datasets: {e}")

    def _on_compare(self) -> None:
        """Handle the compare button click."""
        if self._ancien_combo.currentIndex() < 0 or self._nouveau_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Attention", "Selectionnez deux datasets.")
            return

        id_ancien = self._ancien_combo.currentData()
        id_nouveau = self._nouveau_combo.currentData()

        if id_ancien == id_nouveau:
            QMessageBox.warning(
                self, "Attention", "Veuillez selectionner deux datasets differents."
            )
            return

        self._compare_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._status_label.setText("Comparaison en cours...")
        self._status_label.setStyleSheet("color: #31333f; background: transparent; border: none;")

        self._worker = ComparisonWorker(id_ancien, id_nouveau, self._user_id, self._role)
        self._worker.finished.connect(self._on_compare_success)
        self._worker.error.connect(self._on_compare_error)
        self._worker.start()

    def _on_compare_success(self, result: dict) -> None:
        """Handle successful comparison."""
        self._progress.setVisible(False)
        self._compare_btn.setEnabled(True)
        self._status_label.setText("Comparaison terminee.")
        self._status_label.setStyleSheet("color: #22c55e; font-weight: bold; background: transparent; border: none;")
        self._display_comparison(result)

    def _on_compare_error(self, error_msg: str) -> None:
        """Handle comparison error."""
        self._progress.setVisible(False)
        self._compare_btn.setEnabled(True)
        self._status_label.setText(f"Erreur: {error_msg}")
        self._status_label.setStyleSheet("color: #ef4444; font-weight: bold; background: transparent; border: none;")

    def _clear_results(self) -> None:
        """Remove all widgets from the results container."""
        while self._results_layout.count():
            item = self._results_layout.takeAt(0)
            if item is None:
                break
            widget = item.widget()
            if widget:
                widget.deleteLater()
            else:
                self._clear_sub_layout(item.layout())

    def _clear_sub_layout(self, layout) -> None:
        """Recursively clear a nested layout."""
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            if item is None:
                break
            widget = item.widget()
            if widget:
                widget.deleteLater()
            else:
                self._clear_sub_layout(item.layout())

    def _display_comparison(self, result: dict) -> None:
        """Render comparison results into the results container."""
        self._clear_results()

        schema = result.get("schema_changes", {})
        taille = result.get("taille_changes", {})
        drift = result.get("drift_statistique", [])
        anomalies = result.get("anomalies_comparison", {})

        # Overview cards
        self._results_layout.addWidget(SubSectionTitle("Vue d'ensemble", "\u25a6"))
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        diff_lignes = taille.get("diff_lignes", 0)
        diff_colonnes = taille.get("diff_colonnes", 0)
        cards_layout.addWidget(
            MetricCard("Diff. lignes", f"{'+' if diff_lignes >= 0 else ''}{diff_lignes}", "\u2195")
        )
        cards_layout.addWidget(
            MetricCard("Diff. colonnes", f"{'+' if diff_colonnes >= 0 else ''}{diff_colonnes}", "#")
        )
        cards_layout.addWidget(
            MetricCard("Colonnes ajoutees", str(schema.get("nb_ajoutees", 0)), "+")
        )
        cards_layout.addWidget(
            MetricCard("Colonnes supprimees", str(schema.get("nb_supprimees", 0)), "\u2212")
        )
        self._results_layout.addLayout(cards_layout)

        self._results_layout.addWidget(Separator())

        # Detail tabs
        tabs = QTabWidget()
        tabs.addTab(self._build_schema_tab(schema), "Schema")
        tabs.addTab(self._build_drift_tab(drift), "Drift statistique")
        tabs.addTab(self._build_anomaly_tab(anomalies), "Anomalies")
        self._results_layout.addWidget(tabs)

    def _build_schema_tab(self, schema: dict) -> QWidget:
        """Build the schema-changes tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)

        layout.addWidget(SubSectionTitle("Changements de schema", "\u2692"))

        ajoutees = schema.get("colonnes_ajoutees", [])
        supprimees = schema.get("colonnes_supprimees", [])
        types_modifies = schema.get("types_modifies", [])

        if ajoutees:
            lbl = QLabel("<b>Colonnes ajoutees</b>")
            lbl.setStyleSheet("background: transparent; border: none; color: #31333f;")
            layout.addWidget(lbl)
            for col in ajoutees:
                item = QLabel(f"• {col}")
                item.setStyleSheet("background: transparent; border: none; color: #16a34a;")
                layout.addWidget(item)

        if supprimees:
            lbl = QLabel("<b>Colonnes supprimees</b>")
            lbl.setStyleSheet("background: transparent; border: none; color: #31333f;")
            layout.addWidget(lbl)
            for col in supprimees:
                item = QLabel(f"• {col}")
                item.setStyleSheet("background: transparent; border: none; color: #ef4444;")
                layout.addWidget(item)

        if types_modifies:
            lbl = QLabel("<b>Types modifies</b>")
            lbl.setStyleSheet("background: transparent; border: none; color: #31333f;")
            layout.addWidget(lbl)
            table = QTableWidget()
            keys = list(types_modifies[0].keys())
            table.setColumnCount(len(keys))
            table.setHorizontalHeaderLabels([str(k) for k in keys])
            table.setRowCount(len(types_modifies))
            for r, row in enumerate(types_modifies):
                for c, key in enumerate(keys):
                    table.setItem(r, c, QTableWidgetItem(str(row.get(key, ""))))
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            table.setMinimumHeight(150)
            layout.addWidget(table)

        if not ajoutees and not supprimees and not types_modifies:
            ok = QLabel("Aucun changement de schema detecte.")
            ok.setStyleSheet("color: #16a34a; background: transparent; border: none; font-weight: bold;")
            layout.addWidget(ok)

        layout.addStretch()
        return widget

    def _build_drift_tab(self, drift: list) -> QWidget:
        """Build the statistical-drift tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)

        layout.addWidget(SubSectionTitle("Drift statistique", "\u2197"))

        if not drift:
            info = QLabel("Aucune colonne numerique commune pour analyser le drift.")
            info.setStyleSheet("color: #555; background: transparent; border: none;")
            layout.addWidget(info)
            layout.addStretch()
            return widget

        significant = [d for d in drift if d.get("drift_significatif")]
        if significant:
            warn = QLabel(
                f"\u26a0 {len(significant)} colonne(s) avec drift significatif detecte(s) "
                "(shift de la moyenne > 1 ecart-type)."
            )
            warn.setStyleSheet("color: #f59e0b; background: transparent; border: none; font-weight: bold;")
            warn.setWordWrap(True)
            layout.addWidget(warn)

        headers = ["Colonne", "Moy. ancien", "Moy. nouveau", "Drift (abs)", "% Changement", "Significatif"]
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(drift))
        for r, d in enumerate(drift):
            anc = d.get("ancien", {}).get("mean")
            nouv = d.get("nouveau", {}).get("mean")
            mean_drift = d.get("mean_drift")
            pct = d.get("mean_pct_change")
            values = [
                d.get("colonne", ""),
                round(anc, 2) if anc is not None else "N/A",
                round(nouv, 2) if nouv is not None else "N/A",
                round(mean_drift, 2) if mean_drift is not None else "N/A",
                f"{pct:.1f}%" if pct is not None else "N/A",
                "Oui" if d.get("drift_significatif") else "Non",
            ]
            for c, value in enumerate(values):
                table.setItem(r, c, QTableWidgetItem(str(value)))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setAlternatingRowColors(True)
        table.setMinimumHeight(220)
        layout.addWidget(table)

        # Drift bar chart (matplotlib)
        self._add_drift_chart(layout, drift)

        layout.addStretch()
        return widget

    def _add_drift_chart(self, layout: QVBoxLayout, drift: list) -> None:
        """Add a matplotlib bar chart of the per-column mean variation (%)."""
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

            cols = [d["colonne"] for d in drift if d.get("mean_drift") is not None]
            vals = [d["mean_pct_change"] for d in drift if d.get("mean_drift") is not None]
            if not cols:
                return

            colors = ["#e74c3c" if abs(v) > 10 else "#27ae60" for v in vals]
            fig, ax = plt.subplots(figsize=(7, 3.2))
            fig.patch.set_facecolor("#f8f9fc")
            ax.bar(cols, vals, color=colors, edgecolor="white")
            ax.set_title("Variation de la moyenne par colonne (%)", fontsize=11)
            ax.set_ylabel("% Changement")
            ax.tick_params(axis="x", labelrotation=45)
            ax.axhline(0, color="#888", linewidth=0.8)
            fig.tight_layout()

            canvas = FigureCanvas(fig)
            canvas.setFixedHeight(240)
            canvas.setStyleSheet("background-color: #f8f9fc; border: none;")
            layout.addWidget(canvas)
            plt.close(fig)
        except Exception:
            pass

    def _build_anomaly_tab(self, anomalies: dict) -> QWidget:
        """Build the anomaly-comparison tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)

        layout.addWidget(SubSectionTitle("Comparaison des anomalies", "\u26a0"))

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        ancien_total = anomalies.get("ancien_total", 0)
        nouveau_total = anomalies.get("nouveau_total", 0)
        diff = anomalies.get("diff", 0)
        cards_layout.addWidget(MetricCard("Anomalies (ancien)", str(ancien_total), "!"))
        cards_layout.addWidget(MetricCard("Anomalies (nouveau)", str(nouveau_total), "!"))
        if anomalies.get("amelioration"):
            cards_layout.addWidget(MetricCard("Evolution", f"-{abs(diff)}", "\u2198"))
        else:
            cards_layout.addWidget(
                MetricCard("Evolution", f"{'+' if diff > 0 else ''}{diff}", "\u2197")
            )
        layout.addLayout(cards_layout)

        if anomalies.get("amelioration"):
            msg = QLabel(
                f"\u2713 Amelioration: {abs(diff)} anomalies en moins dans le nouveau dataset."
            )
            msg.setStyleSheet("color: #16a34a; background: transparent; border: none; font-weight: bold;")
        elif diff > 0:
            msg = QLabel(
                f"\u26a0 Attention: {diff} anomalies supplementaires detectees dans le nouveau dataset."
            )
            msg.setStyleSheet("color: #f59e0b; background: transparent; border: none; font-weight: bold;")
        else:
            msg = QLabel("Nombre d'anomalies stable entre les deux versions.")
            msg.setStyleSheet("color: #555; background: transparent; border: none;")
        msg.setWordWrap(True)
        layout.addWidget(msg)

        layout.addStretch()
        return widget
