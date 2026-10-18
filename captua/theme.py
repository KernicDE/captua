"""Central palette and stylesheet builders for the modern pill UI."""

from PySide6.QtGui import QColor, QGuiApplication, QPalette

BRAND_RED = "#FF5D62"  # default annotation colour and fallback accent


def _mix(a: QColor, b: QColor, t: float) -> QColor:
    return QColor.fromRgbF(*(a.getRgbF()[i] * t + b.getRgbF()[i] * (1 - t) for i in range(3)))


def _system_accent() -> QColor:
    """System accent from the Qt palette; needs a QApplication, else brand red."""
    app = QGuiApplication.instance()
    c = app.palette().color(QPalette.ColorRole.Accent) if app else QColor()
    if not c.isValid():
        return QColor(BRAND_RED)
    h, s, l, _ = c.getHsl()
    return QColor.fromHsl(h, s, max(l, 130))  # keep contrast on the dark UI


# Palette — UI accent follows the system; import theme only after QApplication exists.
WINDOW_BG = "#101014"
PILL_BG = "#1A1A1F"
PILL_BORDER = "#3A3A44"  # >= 1.6:1 against PILL_BG so pills stay visible on bright screenshots
HOVER_BG = "#26262C"
PRESSED_BG = "#30303A"
TEXT = "#E8E8E8"
TEXT_DIM = "#9A9AA2"
_ACC = _system_accent()
ACCENT = _ACC.name().upper()
ACCENT_TINT = f"rgba({_ACC.red()}, {_ACC.green()}, {_ACC.blue()}, 0.18)"
ACCENT_HOVER = _ACC.lighter(115).name().upper()
ACCENT_PRESSED = _ACC.darker(115).name().upper()
ACCENT_DEEP = _mix(_ACC, QColor("#1A1A1A"), 0.25).name().upper()  # selected-item background
ACCENT_DISABLED_BG = _mix(_ACC, QColor(PILL_BG), 0.25).name().upper()
ACCENT_DISABLED_FG = _mix(_ACC, QColor(PILL_BG), 0.6).name().upper()


def accent_css(css: str) -> str:
    """Swap the brand-red literals of a plain stylesheet for the system accent."""
    return css.replace(BRAND_RED, ACCENT).replace("#5C3A2E", ACCENT_DEEP)

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
    QPushButton:focus {{
        border: 1px solid {TEXT};
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
    QPushButton:focus {{
        border: 1px solid {TEXT};
    }}
    QPushButton:disabled {{
        color: #75757D;
    }}
    QPushButton::menu-indicator {{
        image: none;
        width: 0;
    }}
"""

PRIMARY_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {ACCENT};
        color: #101014;
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
    QPushButton:focus {{
        border: 2px solid {TEXT};
    }}
    QPushButton:disabled {{
        background-color: {ACCENT_DISABLED_BG};
        color: {ACCENT_DISABLED_FG};
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

SEPARATOR_STYLE = f"QFrame {{ background-color: {PILL_BORDER}; border: none; }}"

PILL_STYLE = f"""
    QWidget#toolbarPill {{
        background-color: {PILL_BG};
        border: 1px solid {PILL_BORDER};
        border-radius: {RADIUS_PILL}px;
    }}
    QWidget#toolbarPill QLabel {{
        background: transparent;
        border: none;
    }}
    QWidget#toolbarPill QSlider {{
        background: transparent;
        border: none;
    }}
"""

TOAST_STYLE = (
    f"background-color: rgba(26, 26, 31, 230); color: {TEXT};"
    f" border: 1px solid {PILL_BORDER}; border-radius: 12px;"
    " padding: 8px 16px; font-size: 12px;"
)

MENU_STYLE = f"""
QMenu {{ background-color: {PILL_BG}; color: {TEXT}; border: 1px solid {PILL_BORDER};
         border-radius: {RADIUS_BUTTON}px; padding: 4px; }}
QMenu::item {{ padding: 6px 16px; border-radius: 6px; }}
QMenu::item:selected {{ background-color: {HOVER_BG}; }}
"""

# Dialogs inherit the overlay's dark background but not its text colour, so the
# platform theme can leave them dark-on-dark.
DIALOG_STYLE = f"""
QMessageBox {{ background-color: {PILL_BG}; }}
QMessageBox QLabel {{ color: {TEXT}; background: transparent; }}
QMessageBox QPushButton {{ background-color: {HOVER_BG}; color: {TEXT}; border: 1px solid {PILL_BORDER};
                           border-radius: {RADIUS_BUTTON}px; padding: 5px 16px; min-width: 60px; }}
QMessageBox QPushButton:hover {{ background-color: {PRESSED_BG}; }}
"""
