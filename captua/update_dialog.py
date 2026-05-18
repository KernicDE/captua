"""Non-blocking update-available dialog."""

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .self_updater import SelfUpdater, _can_self_update


class UpdateDialog(QWidget):
    """Independent, non-modal update dialog that stays on top."""

    skipped = Signal(str)  # version string
    dismissed = Signal()

    def __init__(self, version: str, changelog: str, url: str, parent=None) -> None:
        super().__init__(parent, Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self._version = version
        self._url = url
        self.setWindowTitle("Update Available")
        self.setFixedSize(520, 560)
        self.setStyleSheet(
            "background-color: #18181B; color: #F4F4F5; font-family: Inter, sans-serif; font-size: 13px;"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header
        header = QLabel(f"<b>Captua v{version}</b> is available")
        header.setStyleSheet("font-size: 18px; color: #F4F4F5;")
        header.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(header)

        sub = QLabel("A new version has been released. Would you like to update?")
        sub.setStyleSheet("color: #A1A1AA; font-size: 13px;")
        sub.setWordWrap(True)
        layout.addWidget(sub)

        # Changelog scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        changelog_widget = QTextEdit()
        changelog_widget.setReadOnly(True)
        changelog_widget.setPlainText(changelog)
        changelog_widget.setStyleSheet(
            "QTextEdit { background-color: #27272A; color: #F4F4F5; "
            "border: 1px solid #3F3F46; border-radius: 8px; padding: 10px; "
            "font-family: 'SF Mono', 'Fira Code', monospace; font-size: 12px; }"
        )
        changelog_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        changelog_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        changelog_widget.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)

        scroll.setWidget(changelog_widget)
        layout.addWidget(scroll, stretch=1)

        # Progress bar (hidden until update starts)
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # indeterminate
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet(
            "QProgressBar { background-color: #27272A; border: 1px solid #3F3F46; "
            "border-radius: 4px; height: 6px; }"
            "QProgressBar::chunk { background-color: #7E9CD8; border-radius: 4px; }"
        )
        self._progress.hide()
        layout.addWidget(self._progress)

        self._status = QLabel("")
        self._status.setStyleSheet("color: #A1A1AA; font-size: 12px;")
        self._status.hide()
        layout.addWidget(self._status)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        can_self = _can_self_update()

        self._update_btn = QPushButton("Update Now" if can_self else "Open Release Page")
        self._update_btn.setFixedHeight(36)
        self._update_btn.setStyleSheet(
            "QPushButton { background-color: #7E9CD8; color: #18181B; "
            "border: none; border-radius: 8px; font-weight: bold; font-size: 13px; padding: 0 16px; }"
            "QPushButton:hover { background-color: #9ABAE8; }"
            "QPushButton:pressed { background-color: #5A7FB8; }"
        )
        self._update_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if can_self:
            self._update_btn.clicked.connect(self._on_self_update)
        else:
            self._update_btn.clicked.connect(self._on_open_page)
        btn_row.addWidget(self._update_btn)

        self._later_btn = QPushButton("Ask Again Later")
        self._later_btn.setFixedHeight(36)
        self._later_btn.setStyleSheet(
            "QPushButton { background-color: #27272A; color: #F4F4F5; "
            "border: 1px solid #3F3F46; border-radius: 8px; font-size: 13px; padding: 0 16px; }"
            "QPushButton:hover { background-color: #3F3F46; border-color: #52525B; }"
            "QPushButton:pressed { background-color: #52525B; }"
        )
        self._later_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._later_btn.clicked.connect(self._on_later)
        btn_row.addWidget(self._later_btn)

        self._skip_btn = QPushButton("Skip This Version")
        self._skip_btn.setFixedHeight(36)
        self._skip_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #A1A1AA; "
            "border: 1px solid #3F3F46; border-radius: 8px; font-size: 13px; padding: 0 16px; }"
            "QPushButton:hover { background-color: #27272A; color: #F4F4F5; border-color: #52525B; }"
            "QPushButton:pressed { background-color: #3F3F46; }"
        )
        self._skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._skip_btn.clicked.connect(self._on_skip)
        btn_row.addWidget(self._skip_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _on_self_update(self) -> None:
        self._update_btn.setEnabled(False)
        self._later_btn.setEnabled(False)
        self._skip_btn.setEnabled(False)
        self._progress.show()
        self._status.show()
        self._status.setText("Checking for updates…")

        self._updater = SelfUpdater(self)
        self._updater.progress.connect(self._status.setText)
        self._updater.finished.connect(self._on_updater_finished)
        self._updater.start()

    def _on_updater_finished(self, success: bool, message: str) -> None:
        self._progress.hide()
        self._status.setText(message)
        if success:
            self._update_btn.setText("Restarting…")
            self._update_btn.setEnabled(False)
            QTimer.singleShot(1500, self._do_restart)
        else:
            self._update_btn.setText("Open Release Page")
            self._update_btn.setEnabled(True)
            self._update_btn.clicked.disconnect()
            self._update_btn.clicked.connect(self._on_open_page)
            self._later_btn.setEnabled(True)
            self._skip_btn.setEnabled(True)

    def _do_restart(self) -> None:
        SelfUpdater.restart()

    def _on_open_page(self) -> None:
        QDesktopServices.openUrl(QUrl(self._url))
        self.close()
        self.dismissed.emit()

    def _on_later(self) -> None:
        self.close()
        self.dismissed.emit()

    def _on_skip(self) -> None:
        self.close()
        self.skipped.emit(self._version)

    def closeEvent(self, event) -> None:
        self.dismissed.emit()
        super().closeEvent(event)
