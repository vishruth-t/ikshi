from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QWidget
from PySide6.QtCore import Qt

class StatusCardWidget(QFrame):
    def __init__(self, title: str, value: str = "0", subtext: str = "", accent_color: str = "#3B82F6", icon: str = "📊", parent=None):
        super().__init__(parent)
        self.accent_color = accent_color
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1E293B, stop:1 #131D2E);
                border: 1px solid #334155;
                border-top: 2px solid {accent_color};
                border-radius: 14px;
            }}
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(6)

        # Header row: Title + Icon Badge
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 700; letter-spacing: 1.2px; background: transparent; border: none;")

        self.icon_label = QLabel(icon)
        self.icon_label.setStyleSheet(f"""
            font-size: 14px;
            background-color: {accent_color}22;
            color: {accent_color};
            border-radius: 8px;
            padding: 4px 8px;
            border: 1px solid {accent_color}44;
        """)

        header_row.addWidget(self.title_label)
        header_row.addStretch()
        header_row.addWidget(self.icon_label)
        main_layout.addLayout(header_row)

        # Main Value Metric
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("color: #FFFFFF; font-size: 26px; font-weight: 800; background: transparent; border: none; padding-top: 2px;")
        main_layout.addWidget(self.value_label)

        # Subtitle / Indicator
        self.subtext_label = QLabel(subtext)
        self.subtext_label.setStyleSheet("color: #94A3B8; font-size: 12px; background: transparent; border: none;")
        main_layout.addWidget(self.subtext_label)

    def set_value(self, value: str, subtext: str = ""):
        self.value_label.setText(str(value))
        if subtext:
            self.subtext_label.setText(subtext)

