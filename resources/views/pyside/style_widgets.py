"""Reusable styled widgets for PySide6 views matching the Streamlit theme."""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt


class MetricCard(QFrame):
    """A styled metric card that matches the Streamlit render_metric_card component.

    Displays an icon, a large bold value, and a descriptive label inside a
    rounded, shadowed card.
    """

    def __init__(self, label: str, value: str, icon: str = "📊", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("MetricCard")
        self.setStyleSheet("""
            QFrame#MetricCard {
                background-color: #ffffff;
                border: 1px solid #e8e8e8;
                border-radius: 12px;
                padding: 15px;
                min-height: 90px;
            }
            QFrame#MetricCard:hover {
                border: 1px solid #93DC5C;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(12)

        # Icon circle
        icon_label = QLabel(icon)
        icon_label.setFixedSize(45, 45)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("""
            background-color: rgba(147, 220, 92, 0.15);
            border-radius: 22px;
            font-size: 20px;
            color: #93DC5C;
        """)
        layout.addWidget(icon_label)

        # Text area
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #31333f; background: transparent; border: none;")
        text_layout.addWidget(value_label)

        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-size: 12px; color: #888888; background: transparent; border: none;")
        text_layout.addWidget(label_widget)

        layout.addLayout(text_layout)
        layout.addStretch()


class SectionTitle(QLabel):
    """A styled section title matching Streamlit h2/h3 headers."""

    def __init__(self, text: str, icon: str = "", parent=None) -> None:
        display = f"{icon}  {text}" if icon else text
        super().__init__(display, parent)
        self.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #31333f;
            padding: 5px 0;
            background: transparent;
            border: none;
        """)


class SubSectionTitle(QLabel):
    """A styled sub-section title matching Streamlit h3/h4 headers."""

    def __init__(self, text: str, icon: str = "", parent=None) -> None:
        display = f"{icon}  {text}" if icon else text
        super().__init__(display, parent)
        self.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #31333f;
            padding: 3px 0;
            margin-top: 10px;
            background: transparent;
            border: none;
        """)


class Separator(QFrame):
    """A horizontal line separator matching Streamlit's st.markdown('---')."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFixedHeight(1)
        self.setStyleSheet("background-color: #e0e0e0; border: none;")


class GreenButton(QFrame):
    """A green styled QPushButton wrapper matching Streamlit action buttons."""
    pass  # We use QPushButton directly with QSS in each widget for flexibility
