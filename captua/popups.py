"""Popup selectors for shapes, emojis, and magnifier zoom."""

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QListView,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QStandardItem, QStandardItemModel

from .items import _emoji_font_family

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
    " 👍 👎 👌 🤌 🤏 ✌️ 🤞 🫰 🤟 🤘 🤙 👈 👉 👆 👇 ☝️ 👋 🤚 🖐️ ✋ 🖖 👏 🙌 👐 🤲 🙏 ✍️ 💅 🤳 💪 "
    "👂 👃 🧠 👀 👁️ 👅 👄 🫦 👶 🧒 👦 👧 🧑 👱 👨 👩 🧓 👴 👵"
    " 🐶 🐱 🐭 🐹 🐰 🦊 🐻 🐼 🐨 🐯 🦁 🐮 🐷 🐸 🐵 🐔 🐧 🐦 🐤 🦆 🦅 🦉 🦇 🐺 🐗 🐴 🦄 🐝 🐛 🦋 "
    "🐌 🐞 🐜 🦟 🦗 🕷️ 🦂 🐢 🐍 🦎 🦖 🦕 🐙 🦑 🦐 🦞 🦀 🐡 🐠 🐟 🐬 🐳 🐋 🦈 🐊 🐅 🐆 🦓 🦍 🦧 "
    "🐘 🦛 🦏 🐪 🐫 🦒 🦘 🐃 🐂 🐄 🐎 🐖 🐏 🐑 🦙 🐐 🦌 🐕 🐩 🦮 🐕‍🦺 🐈 🐈‍⬛ 🐓 🦃 🦚 🦜 🦢 🦩 🕊️ "
    "🐇 🦝 🦨 🦡 🦦 🦥 🐁 🐀 🐿️ 🦔"
    " 🍏 🍎 🍐 🍊 🍋 🍌 🍉 🍇 🍓 🫐 🍈 🍒 🍑 🥭 🍍 🥥 🥝 🍅 🍆 🥑 🥦 🥬 🥒 🌶️ 🫑 🌽 🥕 🫒 🧄 🧅 "
    "🥔 🍠 🥐 🥯 🍞 🥖 🥨 🧀 🥚 🍳 🧈 🥞 🧇 🥓 🥩 🍗 🍖 🦴 🌭 🍔 🍟 🍕 🫓 🥪 🥙 🧆 🌮 🌯 🫔 🥗 "
    "🥘 🫕 🥫 🍝 🍜 🍲 🍛 🍣 🍱 🥟 🦪 🍤 🍙 🍚 🍘 🍥 🥠 🥮 🍢 🍡 🍧 🍨 🍦 🥧 🧁 🍰 🎂 🍮 🍭 🍬 "
    "🍫 🍿 🍩 🍪 🌰 🥜 🍯 🥛 🍼 🫖 ☕ 🍵 🧃 🥤 🧋 🍶 🍺 🍻 🥂 🍷 🥃 🍸 🍹 🧉 🍾 🧊"
    " ⚽ 🏀 🏈 ⚾ 🥎 🎾 🏐 🏉 🥏 🎱 🏓 🏸 🏒 🏑 🥍 🏏 🥅 ⛳ 🏹 🎣 🤿 🥊 🥋 🎽 🛹 🛼 🛷 ⛸️ 🥌 🎿 "
    "⛷️ 🏂 🪂 🏋️ 🤼 🤸 ⛹️ 🤺 🤾 🏌️ 🏇 🧘 🏄 🏊 🤽 🚣 🧗 🚵 🚴 🏆 🥇 🥈 🥉 🏅 🎖️ 🏵️ 🎗️ 🎫 🎟️ 🎪 "
    "🤹 🎭 🩰 🎨 🎬 🎤 🎧 🎼 🎹 🥁 🪘 🎷 🎺 🪗 🎸 🪕 🎻 🎲 ♟️ 🎯 🎳 🎮 🎰 🧩"
    " 🚗 🚕 🚙 🚌 🚎 🏎️ 🚓 🚑 🚒 🚐 🛻 🚚 🚛 🚜 🦯 🦽 🦼 🛴 🚲 🛵 🏍️ 🛺 🚨 🚔 🚍 🚘 🚖 🚡 🚠 "
    "🚟 🚃 🚋 🚞 🚝 🚄 🚅 🚈 🚂 🚆 🚇 🚊 🚉 ✈️ 🛫 🛬 🛩️ 💺 🛰️ 🚀 🛸 🚁 🛶 ⛵ 🚤 🛥️ 🛳️ ⛴️ 🚢 ⚓ "
    "⛽ 🚧 🚦 🚥 🚏 🗺️ 🗿 🗽 🗼 🏰 🏯 🏟️ 🎡 🎢 🎠 ⛲ ⛱️ 🏖️ 🏝️ 🏜️ 🌋 ⛰️ 🏔️ 🗻 🏕️ ⛺ 🏠 🏡 🏘️ "
    "🏚️ 🏗️ 🏭 🏢 🏬 🏣 🏤 🏥 🏦 🏨 🏪 🏫 🏩 💒 🏛️ ⛪ 🕌 🕍 🛕 🕋 ⛩️ 🛤️ 🛣️ 🗾 🎑 🏞️ 🌅 🌄 🌠 "
    "🎇 🎆 🌇 🌆 🏙️ 🌃 🌌 🌉 🌁"
    " 💻 ⌨️ 🖥️ 🖨️ 🖱️ 🖲️ 🕹️ 💽 💾 💿 📀 📼 📷 📸 📹 🎥 📽️ 🎞️ 📞 ☎️ 📟 📠 📺 📻 🎙️ 🎚️ 🎛️ 🧭 "
    "⏱️ ⏲️ ⏰ 🕰️ ⌛ ⏳ 📡 🔋 🔌 💡 🔦 🕯️ 🪔 🧯 🛢️ 💸 💵 💴 💶 💷 🪙 💰 💳 💎 ⚖️ 🧰 🔧 🛠️ 🔨 "
    "⚒️ 🪓 ⛏️ ⚔️ 🔪 🗡️ ⚙️ 🪚 🔩 ⚗️ 🧪 🧫 🧬 🔬 🔭 📡 💉 🩸 💊 🩹 🩺 🌡️ 🚽 🚰 🚿 🛁 🛀 🪥 🪠 "
    "🪤 🪒 🧴 🧷 🧹 🧺 🧻 🪣 🧼 🫧 🧽 🧯 🛒 🚬 ⚰️ 🪦 ⚱️ 🗿 🪧 🏧 🚮 🚰 ♿ 🚹 🚺 🚻 🚼 🚾 🛂 "
    "🛃 🛄 🛅"
    " ❤️ 🧡 💛 💚 💙 💜 🖤 🤍 🤎 ❣️ 💕 💞 💓 💗 💖 💘 💝 💟 ☮️ ✝️ ☪️ 🕉️ ☸️ ✡️ 🔯 🕎 ☯️ ☦️ 🛐 "
    "⛎ ♈ ♉ ♊ ♋ ♌ ♍ ♎ ♏ ♐ ♑ ♒ ♓ 🆔 ⚛️ 🉑 ☢️ ☣️ 📴 📳 🈶 🈚 🈸 🈺 🈷️ ✴️ 🆚 💮 🉐 ㊙️ ㊗️ 🈴 "
    "🈵 🈹 🈲 🅰️ 🅱️ 🆎 🆑 🅾️ 🆘 ❌ ⭕ 🛑 ⛔ 📛 🚫 💯 💢 ♨️ 🚷 🚯 🚳 🚱 🔞 📵 🚭 ❗ ❕ ❓ ❔ ‼️ ⁉️ "
    "🔅 🔆 〽️ ⚠️ 🚸 🔱 ⚜️ 🔰 ♻️ ✅ 🈯 💹 ❇️ ✳️ ❎ 🌐 💠 ➿ ♾️ Ⓜ️ 🏧 🈂️ 🛂 🛃 🛄 🛅 ♿ 🚹 🚺 🚻 "
    "🚼 🚾 🚰 🚮 🎦 📶 🈁 🔣 ℹ️ 🔤 🔡 🔠 🆖 🆗 🆙 🆒 🆕 🆓 🔟 🔢 #️⃣ *️⃣ ⏏️ ▶️ ⏸️ ⏯️ ⏹️ ⏺️ "
    "⏭️ ⏮️ ⏩ ⏪ ⏫ ⏬ ◀️ 🔼 🔽 ➡️ ⬅️ ⬆️ ⬇️ ↗️ ↘️ ↙️ ↖️ ↕️ ↔️ ↩️ ↪️ ⤴️ ⤵️ 🔃 🔄 🔙 🔚 🔛 🔜 🔝 🛐 "
    "⚛️ 🕉️ ✡️ ☸️ ☯️ ✝️ ☦️ ☪️ ☮️ 🕎 🔯 ♈ ♉ ♊ ♋ ♌ ♍ ♎ ♏ ♐ ♑ ♒ ♓ ⛎ 🔀 🔁 🔂 ▶️ ⏩ ⏭️ ⏯️ ◀️ ⏪ "
    "⏮️ 🔼 ⏫ 🔽 ⏬ ⏸️ ⏹️ ⏺️ ⏏️ 🎦 🔅 🔆 📶 📳 📴 ♀️ ♂️ ⚧️ ✖️ ➕ ➖ ➗ ♾️ ‼️ ⁉️ ❓ ❔ ❕ ❗ 〰️ 💱 💲 "
    "⚕️ ♻️ ❇️ ✳️ ❎ ✅ ☑️ ✔️ ❌ ⭕ 〽️ ✴️ ©️ ®️ ™️"
    " 🏳️ 🏴 🏴‍☠️ 🏁 🚩 🏳️‍🌈 🏳️‍⚧️ 🇺🇳 🇦🇫 🇦🇽 🇦🇱 🇩🇿 🇦🇸 🇦🇩 🇦🇴 🇦🇮 🇦🇶 🇦🇬 🇦🇷 🇦🇲 🇦🇼 🇦🇺 🇦🇹 🇦🇿 🇧🇸 🇧🇭 🇧🇩 "
    "🇧🇧 🇧🇾 🇧🇪 🇧🇿 🇧🇯 🇧🇲 🇧🇹 🇧🇴 🇧🇦 🇧🇼 🇧🇷 🇧🇳 🇧🇬 🇧🇷 🇧🇫 🇧🇮 🇰🇭 🇨🇲 🇨🇦 🇨🇻 🇧🇶 🇰🇾 🇨🇫 🇹🇩 🇨🇱 🇨🇳 🇨🇴 🇰🇲 "
    "🇨🇬 🇨🇩 🇨🇰 🇨🇷 🇨🇮 🇭🇷 🇨🇺 🇨🇼 🇨🇾 🇨🇿 🇩🇰 🇩🇯 🇩🇲 🇩🇴 🇪🇨 🇪🇬 🇸🇻 🇬🇶 🇪🇷 🇪🇪 🇪🇹 🇪🇺 🇫🇰 🇫🇴 🇫🇯 🇫🇮 🇫🇷 "
    "🇬🇦 🇬🇲 🇬🇪 🇩🇪 🇬🇭 🇬🇮 🇬🇷 🇬🇱 🇬🇩 🇬🇵 🇬🇺 🇬🇹 🇬🇬 🇬🇳 🇬🇼 🇬🇾 🇭🇹 🇭🇳 🇭🇰 🇭🇺 🇮🇸 🇮🇳 🇮🇩 🇮🇷 🇮🇶 🇮🇪 🇮🇱 🇮🇲 "
    "🇮🇹 🇯🇲 🇯🇵 🎌 🇯🇪 🇯🇴 🇰🇿 🇰🇪 🇰🇮 🇰🇼 🇰🇬 🇱🇦 🇱🇻 🇱🇧 🇱🇸 🇱🇷 🇱🇾 🇱🇮 🇱🇹 🇱🇺 🇲🇴 🇲🇬 🇲🇼 🇲🇾 🇲🇻 🇲🇱 🇲🇹 🇲🇭 "
    "🇲🇶 🇲🇷 🇲🇺 🇲🇽 🇫🇲 🇲🇩 🇲🇨 🇲🇳 🇲🇪 🇲🇸 🇲🇦 🇲🇿 🇲🇲 🇳🇦 🇳🇷 🇳🇵 🇳🇱 🇳🇨 🇳🇿 🇳🇮 🇳🇪 🇳🇬 🇳🇺 🇳🇫 🇰🇵 🇲🇰 🇲🇵 "
    "🇳🇴 🇴🇲 🇵🇰 🇵🇼 🇵🇸 🇵🇦 🇵🇬 🇵🇾 🇵🇪 🇵🇭 🇵🇳 🇵🇱 🇵🇹 🇵🇷 🇶🇦 🇷🇴 🇷🇺 🇷🇼 🇼🇸 🇸🇲 🇸🇦 🇸🇳 🇷🇸 🇸🇨 🇸🇱 🇸🇬 🇸🇽 🇸🇰 "
    "🇸🇮 🇸🇧 🇸🇴 🇿🇦 🇬🇸 🇰🇷 🇸🇸 🇪🇸 🇱🇰 🇧🇱 🇸🇭 🇰🇳 🇱🇨 🇵🇲 🇻🇨 🇸🇩 🇸🇷 🇸🇿 🇸🇪 🇨🇭 🇸🇾 🇹🇯 🇹🇿 🇹🇭 🇹🇱 🇹🇬 🇹🇰 🇹🇴 "
    "🇹🇹 🇹🇳 🇹🇷 🇹🇲 🇹🇨 🇹🇻 🇻🇮 🇺🇬 🇺🇦 🇦🇪 🇬🇧 🇺🇳 🇺🇸 🇺🇾 🇺🇿 🇻🇺 🇻🇦 🇻🇪 🇻🇳 🇪🇭 🇾🇪 🇿🇲 🇿🇼"
)

_ALL_EMOJIS = [e for e in _EMOJIS.replace("\n", " ").split(" ") if e]


class ShapePopup(QWidget):
    """Popup shape selector that appears below a toolbar button."""

    shape_selected = Signal(str)

    def __init__(self, current_shape: str = "heart", parent=None) -> None:
        super().__init__(parent, Qt.WindowType.Popup)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("""
            QWidget {
                background-color: #1A1A1A;
                border: 1px solid #2A2A2A;
                border-radius: 10px;
            }
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
                border: 1px solid #A07050;
            }
        """)
        self.setFixedSize(200, 200)

        layout = QGridLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)

        for i, (key, icon) in enumerate(_SHAPE_ICONS):
            btn = QPushButton(icon)
            btn.setFixedSize(52, 44)
            btn.setCheckable(True)
            btn.setChecked(key == current_shape)
            btn.clicked.connect(lambda _checked, k=key: self._select(k))
            layout.addWidget(btn, i // 3, i % 3)

    def _select(self, key: str) -> None:
        self.shape_selected.emit(key)
        self.close()

    def show_below(self, widget: QWidget) -> None:
        pos = widget.mapToGlobal(QPoint(0, widget.height() + 4))
        self.move(pos)
        self.show()


class EmojiPopup(QWidget):
    """Popup emoji selector that appears below a toolbar button."""

    emoji_selected = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent, Qt.WindowType.Popup)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 360)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        container = QFrame(self)
        container.setStyleSheet("""
            QFrame {
                background-color: #1A1A1A;
                border: 1px solid #2A2A2A;
                border-radius: 10px;
            }
        """)
        inner = QVBoxLayout(container)
        inner.setContentsMargins(10, 10, 10, 10)
        inner.setSpacing(6)

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

        font = QFont(_emoji_font_family(), 20)
        self._view.setFont(font)

        self._view.setStyleSheet("""
            QListView {
                background-color: transparent;
                border: none;
            }
            QListView::item {
                background-color: transparent;
                color: #E8E8E8;
            }
            QListView::item:hover {
                background-color: #303030;
                border-radius: 4px;
            }
            QListView::item:selected {
                background-color: #5C3A2E;
                border: 1px solid #A07050;
                border-radius: 4px;
            }
        """)

        model = QStandardItemModel(self)
        for emoji in _ALL_EMOJIS:
            item = QStandardItem(emoji)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setEditable(False)
            model.appendRow(item)

        self._view.setModel(model)
        self._view.clicked.connect(self._on_clicked)

        inner.addWidget(self._view)
        outer.addWidget(container)

    def _on_clicked(self, index) -> None:
        emoji = index.data(Qt.ItemDataRole.DisplayRole)
        self.emoji_selected.emit(emoji)
        self.close()

    def show_below(self, widget: QWidget) -> None:
        pos = widget.mapToGlobal(QPoint(0, widget.height() + 4))
        screen = widget.screen()
        if screen is not None:
            geo = screen.availableGeometry()
            if pos.x() + self.width() > geo.right():
                pos.setX(geo.right() - self.width() - 4)
        self.move(pos)
        self.show()


class MagnifierPopup(QWidget):
    """Popup zoom slider that appears below the magnifier toolbar button."""

    zoom_changed = Signal(float)

    def __init__(self, current_zoom: float = 2.0, parent=None) -> None:
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(180, 80)
        self.setStyleSheet("""
            QWidget {
                background-color: #1A1A1A;
                border: 1px solid #2A2A2A;
                border-radius: 10px;
            }
            QLabel {
                color: #E8E8E8;
                font-size: 12px;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #2A2A2A;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #A07050;
                width: 14px;
                height: 14px;
                border-radius: 7px;
                margin: -5px 0;
            }
            QSlider::sub-page:horizontal {
                background: #A07050;
                border-radius: 2px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        self._label = QLabel(f"Zoom: {current_zoom:.1f}x")
        layout.addWidget(self._label)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(15, 50)  # 1.5x to 5.0x
        self._slider.setValue(int(current_zoom * 10))
        self._slider.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self._slider)

    def _on_value_changed(self, value: int) -> None:
        zoom = value / 10.0
        self._label.setText(f"Zoom: {zoom:.1f}x")
        self.zoom_changed.emit(zoom)

    def set_zoom(self, zoom: float) -> None:
        self._slider.blockSignals(True)
        self._slider.setValue(int(round(zoom * 10)))
        self._slider.blockSignals(False)
        self._label.setText(f"Zoom: {zoom:.1f}x")

    def show_below(self, widget: QWidget) -> None:
        pos = widget.mapToGlobal(QPoint(0, widget.height() + 4))
        screen = widget.screen()
        if screen is not None:
            geo = screen.availableGeometry()
            if pos.x() + self.width() > geo.right():
                pos.setX(geo.right() - self.width() - 4)
        self.move(pos)
        self.show()
