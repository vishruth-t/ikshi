from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtCore import Qt

class StatusCardWidget(QFrame):
    def __init__(self, title: str, value: str = "0", subtext: str = "", accent_color: str = "#cba6f7", icon: str = "", parent=None):
        super().__init__(parent)
        self.title_text = title
        self.accent_color = accent_color
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(4)

        # Header row: Title
        self.title_label = QLabel(title.upper())
        main_layout.addWidget(self.title_label)

        # Main Value Metric
        self.value_label = QLabel(str(value))
        main_layout.addWidget(self.value_label)

        # Subtitle / Indicator
        self.subtext_label = QLabel(subtext)
        main_layout.addWidget(self.subtext_label)
        
        self.apply_theme()

    def apply_theme(self, theme_name: str = None):
        from config.settings import settings
        from ui.utils.theme import get_palette
        theme = theme_name or getattr(settings, "theme", "dark")
        p = get_palette(theme)
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {p["bg_card"]};
                border: 1px solid {p["border"]};
                border-radius: 8px;
            }}
        """)
        self.title_label.setStyleSheet(f"color: {p['text_secondary']}; font-size: 11px; font-weight: 600; letter-spacing: 0.5px; background: transparent; border: none;")
        self.value_label.setStyleSheet(f"color: {p['text_primary']}; font-size: 22px; font-weight: 700; background: transparent; border: none;")
        self.subtext_label.setStyleSheet(f"color: {p['text_secondary']}; font-size: 12px; background: transparent; border: none;")

    def set_value(self, value: str, subtext: str = ""):
        self.value_label.setText(str(value))
        if subtext:
            self.subtext_label.setText(subtext)


