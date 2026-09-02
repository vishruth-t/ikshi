"""Theme engine for IKSHI - Supports seamlessly dynamic Dark Mode and Light Mode."""

THEME_PALETTES = {
    "dark": {
        "bg_app": "#0D1117",
        "bg_sidebar": "#010409",
        "bg_card": "#161B22",
        "bg_card_inner": "#0D1117",
        "bg_input": "#0D1117",
        "border": "#30363D",
        "border_subtle": "#21262D",
        "text_primary": "#F0F6FC",
        "text_secondary": "#8B949E",
        "text_muted": "#6E7681",
        "accent": "#cba6f7",
        "accent_hover": "#b4befe",
        "accent_bg": "#1E1A2E",
        "accent_dark": "#11111B",
        "btn_primary_bg": "#238636",
        "btn_primary_hover": "#2EA043",
        "btn_primary_border": "#2EA043",
        "btn_secondary_bg": "#21262D",
        "btn_secondary_hover": "#30363D",
        "btn_secondary_text": "#F0F6FC",
        "btn_danger_bg": "#DA3633",
        "btn_danger_hover": "#E5534B",
        "status_bar_bg": "#010409",
        "status_bar_text": "#8B949E",
        "table_bg": "#0D1117",
        "table_alt_bg": "#161B22",
        "table_header_bg": "#161B22",
        "table_select_bg": "#21262D",
        "card_header_color": "#F0F6FC"
    },
    "light": {
        "bg_app": "#F6F8FA",
        "bg_sidebar": "#FFFFFF",
        "bg_card": "#FFFFFF",
        "bg_card_inner": "#F6F8FA",
        "bg_input": "#FFFFFF",
        "border": "#D0D7DE",
        "border_subtle": "#E1E4E8",
        "text_primary": "#1F2328",
        "text_secondary": "#656D76",
        "text_muted": "#8C959F",
        "accent": "#8250DF",
        "accent_hover": "#6F42C1",
        "accent_bg": "#F3EEFA",
        "accent_dark": "#FFFFFF",
        "btn_primary_bg": "#1F883D",
        "btn_primary_hover": "#1A7F37",
        "btn_primary_border": "#1A7F37",
        "btn_secondary_bg": "#F6F8FA",
        "btn_secondary_hover": "#EAEEF2",
        "btn_secondary_text": "#1F2328",
        "btn_danger_bg": "#CF222E",
        "btn_danger_hover": "#A40E26",
        "status_bar_bg": "#FFFFFF",
        "status_bar_text": "#656D76",
        "table_bg": "#FFFFFF",
        "table_alt_bg": "#F6F8FA",
        "table_header_bg": "#F6F8FA",
        "table_select_bg": "#EAEFF7",
        "card_header_color": "#1F2328"
    }
}

def get_palette(theme_name: str = "dark") -> dict:
    return THEME_PALETTES.get(theme_name.lower(), THEME_PALETTES["dark"])

def get_app_stylesheet(theme_name: str = "dark") -> str:
    p = get_palette(theme_name)
    return f"""
        QMainWindow, QWidget {{
            background-color: {p["bg_app"]};
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            color: {p["text_primary"]};
            font-size: 13px;
        }}
        QDialog, QMessageBox {{
            background-color: {p["bg_card"]};
            color: {p["text_primary"]};
        }}
        QMessageBox {{
            background-color: {p["bg_card"]};
            border: 1px solid {p["border"]};
            border-radius: 8px;
        }}
        QMessageBox QLabel {{
            color: {p["text_primary"]};
            font-size: 13px;
            font-weight: 500;
            background-color: transparent;
            min-height: 36px;
        }}
        QMessageBox QPushButton {{
            background-color: {p["accent"]};
            color: {p["accent_dark"]};
            font-weight: 700;
            font-size: 12px;
            padding: 6px 18px;
            border-radius: 6px;
            border: 1px solid {p["accent"]};
            min-width: 65px;
            min-height: 22px;
        }}
        QMessageBox QPushButton:hover {{
            background-color: {p["accent_hover"]};
            border: 1px solid {p["accent_hover"]};
        }}
        QDialog QPushButton {{
            background-color: {p["btn_secondary_bg"]};
            color: {p["btn_secondary_text"]};
            border: 1px solid {p["border"]};
            padding: 6px 14px;
            border-radius: 6px;
            font-weight: 500;
            font-size: 12px;
            min-width: 65px;
        }}
        QDialog QPushButton:hover {{
            background-color: {p["btn_secondary_hover"]};
        }}
        QToolTip {{
            background-color: {p["bg_card"]};
            color: {p["text_primary"]};
            border: 1px solid {p["border"]};
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 12px;
        }}
        QStatusBar {{
            background-color: {p["status_bar_bg"]};
            color: {p["status_bar_text"]};
            border-top: 1px solid {p["border_subtle"]};
            padding: 4px 12px;
            font-size: 12px;
        }}
        QScrollBar:vertical {{
            background: {p["bg_app"]};
            width: 8px;
            border-radius: 4px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical {{
            background: {p["border"]};
            min-height: 24px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {p["text_muted"]};
        }}
        QScrollBar:horizontal {{
            background: {p["bg_app"]};
            height: 8px;
            border-radius: 4px;
            margin: 2px;
        }}
        QScrollBar::handle:horizontal {{
            background: {p["border"]};
            min-width: 24px;
            border-radius: 4px;
        }}
        QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox {{
            background-color: {p["bg_input"]};
            color: {p["text_primary"]};
            border: 1px solid {p["border"]};
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 12px;
        }}
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QComboBox:focus, QComboBox:on {{
            border: 1.5px solid {p["accent"]};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {p["bg_card"]};
            color: {p["text_primary"]};
            selection-background-color: {p["accent"]};
            selection-color: {p["accent_dark"]};
            border: 1px solid {p["border"]};
            border-radius: 6px;
            padding: 4px;
            outline: 0;
        }}
        QComboBox QAbstractItemView::item {{
            min-height: 26px;
            padding: 4px 8px;
            color: {p["text_primary"]};
            background-color: transparent;
            border-radius: 4px;
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: {p["btn_secondary_hover"]};
            color: {p["text_primary"]};
        }}
        QComboBox QAbstractItemView::item:selected {{
            background-color: {p["accent"]};
            color: {p["accent_dark"]};
            font-weight: 600;
        }}
    """

def get_sidebar_styles(theme_name: str = "dark") -> tuple[str, str, str]:
    p = get_palette(theme_name)
    sidebar_qss = f"""
        QWidget#sidebar {{
            background-color: {p["bg_sidebar"]};
            border-right: 1px solid {p["border_subtle"]};
        }}
        QLabel {{
            border: none;
            background: transparent;
        }}
    """
    expanded_btn = f"""
        QPushButton {{
            background-color: transparent;
            color: {p["text_secondary"]};
            font-weight: 600;
            font-size: 13px;
            text-align: left;
            padding: 10px 14px;
            border: 1px solid transparent;
            border-radius: 8px;
            margin: 2px 10px;
            min-height: 20px;
        }}
        QPushButton:hover {{
            background-color: {p["bg_card"]};
            color: {p["text_primary"]};
            border: 1px solid {p["border"]};
        }}
        QPushButton:checked {{
            background-color: {p["accent_bg"]};
            color: {p["accent"]};
            font-weight: 700;
            border: 1px solid {p["accent"]};
        }}
    """
    collapsed_btn = f"""
        QPushButton {{
            background-color: transparent;
            color: {p["text_secondary"]};
            border: 1px solid transparent;
            border-radius: 8px;
            margin: 3px 8px;
            min-height: 40px;
            max-height: 40px;
        }}
        QPushButton:hover {{
            background-color: {p["bg_card"]};
            border: 1px solid {p["border"]};
        }}
        QPushButton:checked {{
            background-color: {p["accent_bg"]};
            border: 1px solid {p["accent"]};
        }}
    """
    return sidebar_qss, expanded_btn, collapsed_btn

def get_table_qss(theme_name: str = "dark") -> str:
    p = get_palette(theme_name)
    return f"""
        QTableWidget {{
            background-color: {p["table_bg"]};
            alternate-background-color: {p["table_alt_bg"]};
            color: {p["text_primary"]};
            gridline-color: transparent;
            border: 1px solid {p["border"]};
            border-radius: 6px;
            selection-background-color: {p["table_select_bg"]};
            selection-color: {p["text_primary"]};
            outline: none;
        }}
        QHeaderView::section {{
            background-color: {p["table_header_bg"]};
            color: {p["text_secondary"]};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
            padding: 10px 8px;
            border: none;
            border-bottom: 1px solid {p["border"]};
        }}
        QTableWidget::item {{
            padding: 6px 10px;
            border-bottom: 1px solid {p["border_subtle"]};
            color: {p["text_primary"]};
            font-size: 13px;
        }}
        QScrollBar:vertical {{
            background: {p["table_bg"]};
            width: 8px;
            border-radius: 4px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical {{
            background: {p["border"]};
            min-height: 24px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {p["text_muted"]};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
    """
