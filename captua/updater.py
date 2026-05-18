"""Check for updates from GitHub releases."""

import json

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest


class UpdateChecker(QObject):
    """Asynchronous GitHub release checker."""

    update_available = Signal(str, str, str)  # version, changelog, url
    no_update = Signal()
    error = Signal(str)

    def __init__(self, current_version: str, parent=None) -> None:
        super().__init__(parent)
        self._current = current_version
        self._nam = QNetworkAccessManager(self)
        self._nam.finished.connect(self._on_reply)

    def check(self) -> None:
        """Start an async check against the GitHub releases API."""
        req = QNetworkRequest(
            QUrl("https://api.github.com/repos/KernicDE/captua/releases/latest")
        )
        # GitHub requires a User-Agent header
        req.setRawHeader(b"User-Agent", b"captua-updater")
        self._nam.get(req)

    def _on_reply(self, reply: QNetworkReply) -> None:
        if reply.error() != QNetworkReply.NetworkError.NoError:
            self.error.emit(reply.errorString())
            return

        try:
            data = json.loads(reply.readAll().data())
        except json.JSONDecodeError as exc:
            self.error.emit(f"Invalid JSON: {exc}")
            return

        tag = data.get("tag_name", "").lstrip("v")
        body = data.get("body", "")
        url = data.get("html_url", "")

        if not tag:
            self.error.emit("No version found in release data.")
            return

        if self._is_newer(tag, self._current):
            self.update_available.emit(tag, body, url)
        else:
            self.no_update.emit()

    @staticmethod
    def _is_newer(latest: str, current: str) -> bool:
        """Return True if *latest* is a higher version than *current*."""
        try:
            latest_t = tuple(int(x) for x in latest.split(".") if x.isdigit())
            current_t = tuple(int(x) for x in current.split(".") if x.isdigit())
        except ValueError:
            return latest != current
        return latest_t > current_t
