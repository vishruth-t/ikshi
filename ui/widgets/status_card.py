from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtCore import Qt

class StatusCardWidget(QFrame):
    def __init__(self, title: str, value: str = "0", subtext: str = "", accent_color: str = "#cba6f7", icon: str = "", parent=None):
        super().__init__(parent)

        self.accent_color = accent_color
        self.setStyleSheet("""
            QFrame {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 8px;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(4)

        # Header row: Title
        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet("color: #8B949E; font-size: 11px; font-weight: 600; letter-spacing: 0.5px; background: transparent; border: none;")
        main_layout.addWidget(self.title_label)

        # Main Value Metric
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet("color: #F0F6FC; font-size: 22px; font-weight: 700; background: transparent; border: none;")
        main_layout.addWidget(self.value_label)

        # Subtitle / Indicator
        self.subtext_label = QLabel(subtext)
        self.subtext_label.setStyleSheet("color: #8B949E; font-size: 12px; background: transparent; border: none;")
        main_layout.addWidget(self.subtext_label)

    def set_value(self, value: str, subtext: str = ""):
        self.value_label.setText(str(value))
        if subtext:
            self.subtext_label.setText(subtext)


