"""Popup selectors for shapes, emojis, and magnifier zoom."""

import unicodedata

from PySide6.QtCore import QPoint, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QListView,
    QPushButton,
    QTabBar,
    QVBoxLayout,
    QWidget,
)

from .items import _emoji_font_family
from .theme import EDIT_STYLE, PILL_BG, PILL_BORDER, TEXT, accent_css

# Fixed annotation colours offered by the hover palette.
PRESET_COLORS = [
    ("Red", "#F23C3C"),
    ("Orange", "#FF9F0A"),
    ("Yellow", "#FFD60A"),
    ("Green", "#2FBF5B"),
    ("Blue", "#2F7BFF"),
    ("Pink / Purple", "#C86BFA"),
    ("White", "#FFFFFF"),
    ("Black", "#111111"),
]
BACKDROP_COLORS = PRESET_COLORS + [("Dark", "#1A1A1A")]

_SHAPE_ICONS = [
    ("heart", "♥"),
    ("star5", "★"),
    ("star4", "✦"),
    ("triangle", "▲"),
    ("diamond", "◆"),
    ("hexagon", "⬡"),
    ("arrow_shape", "➤"),
    ("cross", "✚"),
    ("moon", "☾"),
]

_EMOJIS = (
    "😀 😃 😄 😁 😆 😅 🤣 😂 🙂 🙃 😉 😊 😇 🥰 😍 🤩 😘 😗 😚 😙 😋 😛 😜 🤪 😝 🤑 🤗 🤭 🤫 🤔 "
    "🤐 🤨 😐 😑 😶 😏 😒 🙄 😬 🤥 😌 😔 😪 🤤 😴 😷 🤒 🤕 🤢 🤮 🤧 🥵 🥶 🥴 😵 🤯 🤠 🥳 😎 🤓 🧐 "
    "😕 😟 🙁 ☹️ 😮 😯 😲 😳 🥺 😦 😧 😨 😰 😥 😢 😭 😱 😖 😣 😞 😓 😩 😫 🥱 😤 😡 😠 🤬 😈 👿 💀 "
    "☠️ 💩 🤡 👹 👺 👻 👽 👾 🤖 😺 😸 😹 😻 😼 😽 🙀 😿 😾"
    "|👍 👎 👌 🤌 🤏 ✌️ 🤞 🫰 🤟 🤘 🤙 👈 👉 👆 👇 ☝️ 👋 🤚 🖐️ ✋ 🖖 👏 🙌 👐 🤲 🙏 ✍️ 💅 🤳 💪 "
    "👂 👃 🧠 👀 👁️ 👅 👄 🫦 👶 🧒 👦 👧 🧑 👱 👨 👩 🧓 👴 👵"
    "|🐶 🐱 🐭 🐹 🐰 🦊 🐻 🐼 🐨 🐯 🦁 🐮 🐷 🐸 🐵 🐔 🐧 🐦 🐤 🦆 🦅 🦉 🦇 🐺 🐗 🐴 🦄 🐝 🐛 🦋 "
    "🐌 🐞 🐜 🦟 🦗 🕷️ 🦂 🐢 🐍 🦎 🦖 🦕 🐙 🦑 🦐 🦞 🦀 🐡 🐠 🐟 🐬 🐳 🐋 🦈 🐊 🐅 🐆 🦓 🦍 🦧 "
    "🐘 🦛 🦏 🐪 🐫 🦒 🦘 🐃 🐂 🐄 🐎 🐖 🐏 🐑 🦙 🐐 🦌 🐕 🐩 🦮 🐕‍🦺 🐈 🐈‍⬛ 🐓 🦃 🦚 🦜 🦢 🦩 🕊️ "
    "🐇 🦝 🦨 🦡 🦦 🦥 🐁 🐀 🐿️ 🦔"
    "|🍏 🍎 🍐 🍊 🍋 🍌 🍉 🍇 🍓 🫐 🍈 🍒 🍑 🥭 🍍 🥥 🥝 🍅 🍆 🥑 🥦 🥬 🥒 🌶️ 🫑 🌽 🥕 🫒 🧄 🧅 "
    "🥔 🍠 🥐 🥯 🍞 🥖 🥨 🧀 🥚 🍳 🧈 🥞 🧇 🥓 🥩 🍗 🍖 🦴 🌭 🍔 🍟 🍕 🫓 🥪 🥙 🧆 🌮 🌯 🫔 🥗 "
    "🥘 🫕 🥫 🍝 🍜 🍲 🍛 🍣 🍱 🥟 🦪 🍤 🍙 🍚 🍘 🍥 🥠 🥮 🍢 🍡 🍧 🍨 🍦 🥧 🧁 🍰 🎂 🍮 🍭 🍬 "
    "🍫 🍿 🍩 🍪 🌰 🥜 🍯 🥛 🍼 🫖 ☕ 🍵 🧃 🥤 🧋 🍶 🍺 🍻 🥂 🍷 🥃 🍸 🍹 🧉 🍾 🧊"
    "|⚽ 🏀 🏈 ⚾ 🥎 🎾 🏐 🏉 🥏 🎱 🏓 🏸 🏒 🏑 🥍 🏏 🥅 ⛳ 🏹 🎣 🤿 🥊 🥋 🎽 🛹 🛼 🛷 ⛸️ 🥌 🎿 "
    "⛷️ 🏂 🪂 🏋️ 🤼 🤸 ⛹️ 🤺 🤾 🏌️ 🏇 🧘 🏄 🏊 🤽 🚣 🧗 🚵 🚴 🏆 🥇 🥈 🥉 🏅 🎖️ 🏵️ 🎗️ 🎫 🎟️ 🎪 "
    "🤹 🎭 🩰 🎨 🎬 🎤 🎧 🎼 🎹 🥁 🪘 🎷 🎺 🪗 🎸 🪕 🎻 🎲 ♟️ 🎯 🎳 🎮 🎰 🧩"
    "|🚗 🚕 🚙 🚌 🚎 🏎️ 🚓 🚑 🚒 🚐 🛻 🚚 🚛 🚜 🦯 🦽 🦼 🛴 🚲 🛵 🏍️ 🛺 🚨 🚔 🚍 🚘 🚖 🚡 🚠 "
    "🚟 🚃 🚋 🚞 🚝 🚄 🚅 🚈 🚂 🚆 🚇 🚊 🚉 ✈️ 🛫 🛬 🛩️ 💺 🛰️ 🚀 🛸 🚁 🛶 ⛵ 🚤 🛥️ 🛳️ ⛴️ 🚢 ⚓ "
    "⛽ 🚧 🚦 🚥 🚏 🗺️ 🗿 🗽 🗼 🏰 🏯 🏟️ 🎡 🎢 🎠 ⛲ ⛱️ 🏖️ 🏝️ 🏜️ 🌋 ⛰️ 🏔️ 🗻 🏕️ ⛺ 🏠 🏡 🏘️ "
    "🏚️ 🏗️ 🏭 🏢 🏬 🏣 🏤 🏥 🏦 🏨 🏪 🏫 🏩 💒 🏛️ ⛪ 🕌 🕍 🛕 🕋 ⛩️ 🛤️ 🛣️ 🗾 🎑 🏞️ 🌅 🌄 🌠 "
    "🎇 🎆 🌇 🌆 🏙️ 🌃 🌌 🌉 🌁"
    "|💻 ⌨️ 🖥️ 🖨️ 🖱️ 🖲️ 🕹️ 💽 💾 💿 📀 📼 📷 📸 📹 🎥 📽️ 🎞️ 📞 ☎️ 📟 📠 📺 📻 🎙️ 🎚️ 🎛️ 🧭 "
    "⏱️ ⏲️ ⏰ 🕰️ ⌛ ⏳ 📡 🔋 🔌 💡 🔦 🕯️ 🪔 🧯 🛢️ 💸 💵 💴 💶 💷 🪙 💰 💳 💎 ⚖️ 🧰 🔧 🛠️ 🔨 "
    "⚒️ 🪓 ⛏️ ⚔️ 🔪 🗡️ ⚙️ 🪚 🔩 ⚗️ 🧪 🧫 🧬 🔬 🔭 📡 💉 🩸 💊 🩹 🩺 🌡️ 🚽 🚰 🚿 🛁 🛀 🪥 🪠 "
    "🪤 🪒 🧴 🧷 🧹 🧺 🧻 🪣 🧼 🫧 🧽 🧯 🛒 🚬 ⚰️ 🪦 ⚱️ 🗿 🪧 🏧 🚮 🚰 ♿ 🚹 🚺 🚻 🚼 🚾 🛂 "
    "🛃 🛄 🛅"
    "|❤️ 🧡 💛 💚 💙 💜 🖤 🤍 🤎 ❣️ 💕 💞 💓 💗 💖 💘 💝 💟 ☮️ ✝️ ☪️ 🕉️ ☸️ ✡️ 🔯 🕎 ☯️ ☦️ 🛐 "
    "⛎ ♈ ♉ ♊ ♋ ♌ ♍ ♎ ♏ ♐ ♑ ♒ ♓ 🆔 ⚛️ 🉑 ☢️ ☣️ 📴 📳 🈶 🈚 🈸 🈺 🈷️ ✴️ 🆚 💮 🉐 ㊙️ ㊗️ 🈴 "
    "🈵 🈹 🈲 🅰️ 🅱️ 🆎 🆑 🅾️ 🆘 ❌ ⭕ 🛑 ⛔ 📛 🚫 💯 💢 ♨️ 🚷 🚯 🚳 🚱 🔞 📵 🚭 ❗ ❕ ❓ ❔ ‼️ ⁉️ "
    "🔅 🔆 〽️ ⚠️ 🚸 🔱 ⚜️ 🔰 ♻️ ✅ 🈯 💹 ❇️ ✳️ ❎ 🌐 💠 ➿ ♾️ Ⓜ️ 🏧 🈂️ 🛂 🛃 🛄 🛅 ♿ 🚹 🚺 🚻 "
    "🚼 🚾 🚰 🚮 🎦 📶 🈁 🔣 ℹ️ 🔤 🔡 🔠 🆖 🆗 🆙 🆒 🆕 🆓 🔟 🔢 #️⃣ *️⃣ ⏏️ ▶️ ⏸️ ⏯️ ⏹️ ⏺️ "
    "⏭️ ⏮️ ⏩ ⏪ ⏫ ⏬ ◀️ 🔼 🔽 ➡️ ⬅️ ⬆️ ⬇️ ↗️ ↘️ ↙️ ↖️ ↕️ ↔️ ↩️ ↪️ ⤴️ ⤵️ 🔃 🔄 🔙 🔚 🔛 🔜 🔝 🛐 "
    "⚛️ 🕉️ ✡️ ☸️ ☯️ ✝️ ☦️ ☪️ ☮️ 🕎 🔯 ♈ ♉ ♊ ♋ ♌ ♍ ♎ ♏ ♐ ♑ ♒ ♓ ⛎ 🔀 🔁 🔂 ▶️ ⏩ ⏭️ ⏯️ ◀️ ⏪ "
    "⏮️ 🔼 ⏫ 🔽 ⏬ ⏸️ ⏹️ ⏺️ ⏏️ 🎦 🔅 🔆 📶 📳 📴 ♀️ ♂️ ⚧️ ✖️ ➕ ➖ ➗ ♾️ ‼️ ⁉️ ❓ ❔ ❕ ❗ 〰️ 💱 💲 "
    "⚕️ ♻️ ❇️ ✳️ ❎ ✅ ☑️ ✔️ ❌ ⭕ 〽️ ✴️ ©️ ®️ ™️"
    "|🏳️ 🏴 🏴‍☠️ 🏁 🚩 🏳️‍🌈 🏳️‍⚧️ 🇺🇳 🇦🇫 🇦🇽 🇦🇱 🇩🇿 🇦🇸 🇦🇩 🇦🇴 🇦🇮 🇦🇶 🇦🇬 🇦🇷 🇦🇲 🇦🇼 🇦🇺 🇦🇹 🇦🇿 🇧🇸 🇧🇭 🇧🇩 "
    "🇧🇧 🇧🇾 🇧🇪 🇧🇿 🇧🇯 🇧🇲 🇧🇹 🇧🇴 🇧🇦 🇧🇼 🇧🇷 🇧🇳 🇧🇬 🇧🇷 🇧🇫 🇧🇮 🇰🇭 🇨🇲 🇨🇦 🇨🇻 🇧🇶 🇰🇾 🇨🇫 🇹🇩 🇨🇱 🇨🇳 🇨🇴 🇰🇲 "
    "🇨🇬 🇨🇩 🇨🇰 🇨🇷 🇨🇮 🇭🇷 🇨🇺 🇨🇼 🇨🇾 🇨🇿 🇩🇰 🇩🇯 🇩🇲 🇩🇴 🇪🇨 🇪🇬 🇸🇻 🇬🇶 🇪🇷 🇪🇪 🇪🇹 🇪🇺 🇫🇰 🇫🇴 🇫🇯 🇫🇮 🇫🇷 "
    "🇬🇦 🇬🇲 🇬🇪 🇩🇪 🇬🇭 🇬🇮 🇬🇷 🇬🇱 🇬🇩 🇬🇵 🇬🇺 🇬🇹 🇬🇬 🇬🇳 🇬🇼 🇬🇾 🇭🇹 🇭🇳 🇭🇰 🇭🇺 🇮🇸 🇮🇳 🇮🇩 🇮🇷 🇮🇶 🇮🇪 🇮🇱 🇮🇲 "
    "🇮🇹 🇯🇲 🇯🇵 🎌 🇯🇪 🇯🇴 🇰🇿 🇰🇪 🇰🇮 🇰🇼 🇰🇬 🇱🇦 🇱🇻 🇱🇧 🇱🇸 🇱🇷 🇱🇾 🇱🇮 🇱🇹 🇱🇺 🇲🇴 🇲🇬 🇲🇼 🇲🇾 🇲🇻 🇲🇱 🇲🇹 🇲🇭 "
    "🇲🇶 🇲🇷 🇲🇺 🇲🇽 🇫🇲 🇲🇩 🇲🇨 🇲🇳 🇲🇪 🇲🇸 🇲🇦 🇲🇿 🇲🇲 🇳🇦 🇳🇷 🇳🇵 🇳🇱 🇳🇨 🇳🇿 🇳🇮 🇳🇪 🇳🇬 🇳🇺 🇳🇫 🇰🇵 🇲🇰 🇲🇵 "
    "🇳🇴 🇴🇲 🇵🇰 🇵🇼 🇵🇸 🇵🇦 🇵🇬 🇵🇾 🇵🇪 🇵🇭 🇵🇳 🇵🇱 🇵🇹 🇵🇷 🇶🇦 🇷🇴 🇷🇺 🇷🇼 🇼🇸 🇸🇲 🇸🇦 🇸🇳 🇷🇸 🇸🇨 🇸🇱 🇸🇬 🇸🇽 🇸🇰 "
    "🇸🇮 🇸🇧 🇸🇴 🇿🇦 🇬🇸 🇰🇷 🇸🇸 🇪🇸 🇱🇰 🇧🇱 🇸🇭 🇰🇳 🇱🇨 🇵🇲 🇻🇨 🇸🇩 🇸🇷 🇸🇿 🇸🇪 🇨🇭 🇸🇾 🇹🇯 🇹🇿 🇹🇭 🇹🇱 🇹🇬 🇹🇰 🇹🇴 "
    "🇹🇹 🇹🇳 🇹🇷 🇹🇲 🇹🇨 🇹🇻 🇻🇮 🇺🇬 🇺🇦 🇦🇪 🇬🇧 🇺🇳 🇺🇸 🇺🇾 🇺🇿 🇻🇺 🇻🇦 🇻🇪 🇻🇳 🇪🇭 🇾🇪 🇿🇲 🇿🇼"
)


# Emoji categories, in the order of the groups in _EMOJIS ("|" separates them).
_CATEGORIES = [
    ("😀", "Smileys"), ("👍", "People"), ("🐶", "Animals"), ("🍎", "Food"),
    ("⚽", "Activities"), ("🚗", "Travel"), ("💡", "Objects"), ("❤️", "Symbols"), ("🏳️", "Flags"),
]
_EMOJI_GROUPS = [list(dict.fromkeys(g.split())) for g in _EMOJIS.split("|")]


def _emoji_name(emoji: str) -> str:
    """Searchable text: Unicode names, flags as their two-letter code."""
    words = []
    for c in emoji:
        if 0x1F1E6 <= ord(c) <= 0x1F1FF:  # regional indicator -> letter
            words.append(chr(ord(c) - 0x1F1E6 + ord("a")))
        elif c not in "\ufe0f\u200d":
            words.append(unicodedata.name(c, "").lower())
    return "".join(words) if all(len(w) == 1 for w in words) else " ".join(words)


def _show_above(popup: QWidget, widget: QWidget) -> None:
    """Place a popup directly above `widget` (below it if there is no room)."""
    pos = widget.mapToGlobal(QPoint(0, -popup.height() - 4))
    screen = widget.screen()
    if screen is not None:
        geo = screen.availableGeometry()
        pos.setX(max(geo.left(), min(pos.x(), geo.right() - popup.width())))
        if pos.y() < geo.top():
            pos.setY(widget.mapToGlobal(QPoint(0, widget.height() + 4)).y())
    popup.move(pos)
    popup.show()


_POPUP_SURFACE = """
    QWidget { background-color: #1A1A1A; border: 1px solid #2A2A2A; border-radius: 10px; }
"""


class ColorPalettePopup(QFrame):
    """Row of fixed colours shown above a swatch while the mouse is over it.

    A plain child of the overlay (not a Qt.Popup) so hovering keeps working."""

    color_picked = Signal(QColor)
    hover_changed = Signal(bool)

    def __init__(self, parent: QWidget, colors: list[tuple[str, str]]) -> None:
        super().__init__(parent)
        self.setObjectName("colorPalette")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            f"#colorPalette {{ background-color: {PILL_BG}; border: 1px solid {PILL_BORDER}; border-radius: 14px; }}"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)
        self._buttons: list[QPushButton] = []
        for name, hex_ in colors:
            btn = QPushButton()
            btn.setFixedSize(24, 24)
            btn.setToolTip(name)
            btn.setAccessibleName(name)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {hex_}; border: 2px solid transparent; border-radius: 12px; }}"
                f"QPushButton:hover, QPushButton:focus {{ border: 2px solid {TEXT}; }}"
            )
            btn.clicked.connect(lambda _c=False, h=hex_: self.color_picked.emit(QColor(h)))
            layout.addWidget(btn)
            self._buttons.append(btn)
        self.adjustSize()
        self.hide()

    def enterEvent(self, event) -> None:
        self.hover_changed.emit(True)

    def leaveEvent(self, event) -> None:
        self.hover_changed.emit(False)


class ShapePopup(QWidget):
    """Horizontal shape bar that appears above the shape button."""

    shape_selected = Signal(str)

    def __init__(self, current_shape: str = "heart", parent=None) -> None:
        super().__init__(parent, Qt.WindowType.Popup)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(accent_css(_POPUP_SURFACE + """
            QPushButton {
                background-color: #2A2A2A;
                color: #E8E8E8;
                border: 1px solid #303030;
                border-radius: 6px;
                padding: 4px;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #303030;
                border: 1px solid #E8E8E8;
            }
            QPushButton:checked {
                background-color: #5C3A2E;
                border: 1px solid #FF5D62;
            }
        """))
        layout = QHBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 8, 10, 8)

        self._buttons: dict[str, QPushButton] = {}
        for key, icon in _SHAPE_ICONS:
            btn = QPushButton(icon)
            btn.setFixedSize(44, 40)
            btn.setCheckable(True)
            btn.setChecked(key == current_shape)
            btn.clicked.connect(lambda _checked, k=key: self._select(k))
            layout.addWidget(btn)
            self._buttons[key] = btn
        self.setFixedSize(self.sizeHint())

    def _select(self, key: str) -> None:
        for k, btn in self._buttons.items():
            btn.setChecked(k == key)
        self.shape_selected.emit(key)
        self.close()

    def show_above(self, widget: QWidget) -> None:
        _show_above(self, widget)


class EmojiPopup(QWidget):
    """Emoji picker above its toolbar button: category tabs plus search."""

    emoji_selected = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent, Qt.WindowType.Popup)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 380)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        container = QFrame(self)
        container.setStyleSheet(accent_css("""
            QFrame {
                background-color: #1A1A1A;
                border: 1px solid #2A2A2A;
                border-radius: 10px;
            }
        """))
        inner = QVBoxLayout(container)
        inner.setContentsMargins(10, 10, 10, 10)
        inner.setSpacing(6)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search…")
        self._search.setStyleSheet(EDIT_STYLE)
        self._search.textChanged.connect(self._refresh)
        inner.addWidget(self._search)

        self._tabs = QTabBar()
        self._tabs.setDrawBase(False)
        self._tabs.setExpanding(True)
        self._tabs.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._tabs.setFont(QFont(_emoji_font_family(), 13))
        self._tabs.setStyleSheet(accent_css("""
            QTabBar::tab { background: transparent; border: none; border-bottom: 2px solid transparent; padding: 3px 4px; }
            QTabBar::tab:hover { background: #303030; border-radius: 4px; }
            QTabBar::tab:selected { border-bottom: 2px solid #FF5D62; }
        """))
        for icon, name in _CATEGORIES:
            self._tabs.setTabText(self._tabs.addTab(icon), icon)
            self._tabs.setTabToolTip(self._tabs.count() - 1, name)
        self._tabs.currentChanged.connect(self._refresh)
        inner.addWidget(self._tabs)

        self._view = QListView()
        self._view.setViewMode(QListView.ViewMode.IconMode)
        self._view.setFlow(QListView.Flow.LeftToRight)
        self._view.setWrapping(True)
        self._view.setResizeMode(QListView.ResizeMode.Adjust)
        self._view.setGridSize(QSize(44, 44))
        self._view.setUniformItemSizes(True)
        self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self._view.setSelectionMode(QListView.SelectionMode.SingleSelection)
        self._view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._view.setFont(QFont(_emoji_font_family(), 20))
        self._view.setStyleSheet(accent_css("""
            QListView { background-color: transparent; border: none; }
            QListView::item { background-color: transparent; color: #E8E8E8; }
            QListView::item:hover { background-color: #303030; border-radius: 4px; }
            QListView::item:selected { background-color: #5C3A2E; border: 1px solid #FF5D62; border-radius: 4px; }
        """))
        self._model = QStandardItemModel(self)
        self._view.setModel(self._model)
        self._view.clicked.connect(self._on_clicked)
        inner.addWidget(self._view)
        outer.addWidget(container)
        self._refresh()

    def _refresh(self, *_) -> None:
        query = self._search.text().lower().split()
        if query:  # search spans all categories and hides the tab selection
            pool = dict.fromkeys(e for g in _EMOJI_GROUPS for e in g)
            names = {e: _emoji_name(e).split() for e in pool}
            emojis = [e for e in pool if all(any(w.startswith(q) for w in names[e]) for q in query)]
        else:
            emojis = _EMOJI_GROUPS[max(0, self._tabs.currentIndex())]
        self._model.clear()
        for emoji in emojis:
            item = QStandardItem(emoji)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setEditable(False)
            self._model.appendRow(item)

    def _on_clicked(self, index) -> None:
        self.emoji_selected.emit(index.data(Qt.ItemDataRole.DisplayRole))
        self.close()

    def show_above(self, widget: QWidget) -> None:
        self._search.clear()
        _show_above(self, widget)
        self._search.setFocus()
