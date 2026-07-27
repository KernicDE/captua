"""Central palette and stylesheet builders for the modern pill UI."""

# Palette — single accent (the brand red used for annotations).
WINDOW_BG = "#101014"
PILL_BG = "#1A1A1F"
PILL_BORDER = "#2C2C33"
HOVER_BG = "#26262C"
PRESSED_BG = "#30303A"
TEXT = "#E8E8E8"
TEXT_DIM = "#9A9AA2"
ACCENT = "#FF5D62"
ACCENT_TINT = "rgba(255, 93, 98, 0.18)"
ACCENT_HOVER = "#FF7074"
ACCENT_PRESSED = "#E14A4F"

RADIUS_PILL = 14
RADIUS_BUTTON = 8

TOOL_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: transparent;
        color: {TEXT_DIM};
        border: 1px solid transparent;
        border-radius: {RADIUS_BUTTON}px;
    }}
    QPushButton:hover {{
        background-color: {HOVER_BG};
        color: {TEXT};
    }}
    QPushButton:pressed {{
        background-color: {PRESSED_BG};
    }}
    QPushButton:checked {{
        background-color: {ACCENT_TINT};
        border: 1px solid {ACCENT};
        color: {TEXT};
    }}
"""

ACTION_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: transparent;
        color: {TEXT_DIM};
        border: none;
        border-radius: {RADIUS_BUTTON}px;
        font-size: 13px;
        padding: 4px 8px;
    }}
    QPushButton:hover {{
        background-color: {HOVER_BG};
        color: {TEXT};
    }}
    QPushButton:pressed {{
        background-color: {PRESSED_BG};
    }}
    QPushButton:checked {{
        background-color: {ACCENT_TINT};
        color: {TEXT};
        border: 1px solid {ACCENT};
    }}
    QPushButton:disabled {{
        color: #55555C;
    }}
"""

PRIMARY_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {ACCENT};
        color: #FFFFFF;
        border: none;
        border-radius: {RADIUS_BUTTON}px;
        font-size: 13px;
        font-weight: 600;
        padding: 4px 14px;
    }}
    QPushButton:hover {{
        background-color: {ACCENT_HOVER};
    }}
    QPushButton:pressed {{
        background-color: {ACCENT_PRESSED};
    }}
    QPushButton:disabled {{
        background-color: #6E3A3D;
        color: #C8A0A2;
    }}
"""

EDIT_STYLE = f"""
    QLineEdit {{
        background-color: {WINDOW_BG};
        color: {TEXT};
        border: 1px solid {PILL_BORDER};
        border-radius: 6px;
        padding: 2px 4px;
        font-size: 12px;
    }}
    QLineEdit:focus {{
        border: 1px solid {ACCENT};
    }}
"""

SLIDER_STYLE = f"""
    QSlider::groove:horizontal {{
        height: 4px;
        background: {PILL_BORDER};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        width: 12px;
        height: 12px;
        margin: -4px 0;
        border-radius: 6px;
        background: {TEXT_DIM};
    }}
    QSlider::handle:horizontal:hover {{
        background: {ACCENT};
    }}
    QSlider::sub-page:horizontal {{
        background: {ACCENT};
        border-radius: 2px;
    }}
"""

SEPARATOR_STYLE = f"QFrame {{ background-color: {PILL_BORDER}; border: none; }}"

PILL_STYLE = f"""
    QWidget#toolbarPill {{
        background-color: {PILL_BG};
        border: 1px solid {PILL_BORDER};
        border-radius: {RADIUS_PILL}px;
    }}
"""

TOAST_STYLE = (
    f"background-color: rgba(26, 26, 31, 230); color: {TEXT};"
    f" border: 1px solid {PILL_BORDER}; border-radius: 12px;"
    " padding: 8px 16px; font-size: 12px;"
)

MENU_STYLE = f"""
    QMenu {{
        background-color: {PILL_BG};
        color: {TEXT};
        border: 1px solid {PILL_BORDER};
        border-radius: 8px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 20px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {HOVER_BG};
    }}
"""
