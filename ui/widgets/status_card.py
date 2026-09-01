from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtCore import Qt

class StatusCardWidget(QFrame):
    def __init__(self, title: str, value: str = "0", subtext: str = "", accent_color: str = "#3B82F6", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #1E293B;
                border-radius: 12px;
                border-left: 4px solid {accent_color};
                padding: 12px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: bold; letter-spacing: 1px;")

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("color: #F8FAFC; font-size: 28px; font-weight: bold;")

        self.subtext_label = QLabel(subtext)
        self.subtext_label.setStyleSheet("color: #64748B; font-size: 12px;")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.subtext_label)

    def set_value(self, value: str, subtext: str = ""):
        self.value_label.setText(str(value))
        if subtext:
            self.subtext_label.setText(subtext)
