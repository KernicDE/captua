"""Upload a screenshot to Litterbox (temporary) or Catbox (permanent), both free and anonymous."""

from urllib.parse import urlparse

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtNetwork import QHttpMultiPart, QHttpPart, QNetworkAccessManager, QNetworkReply, QNetworkRequest

LITTERBOX_URL = "https://litterbox.catbox.moe/resources/internals/api.php"
EXPIRIES = ("1h", "12h", "24h", "72h")
CATBOX_URL = "https://catbox.moe/user/api.php"
PERMANENT = "permanent"
_HOSTS = ("litter.catbox.moe", "litterbox.catbox.moe", "files.catbox.moe")
_TIMEOUT_MS = 60_000


def parse_link(text: str) -> str | None:
    """The response body is the file URL as plain text; accept only an https link on the service's hosts."""
    url = urlparse(text.strip())
    return text.strip() if url.scheme == "https" and url.hostname in _HOSTS else None


class Uploader(QObject):
    """Asynchronous Litterbox upload; one request at a time is the caller's job."""

    finished = Signal(str)  # link
    failed = Signal(str)
    progress = Signal(int, int)  # bytes sent, total

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._nam = QNetworkAccessManager(self)

    def upload(self, png: bytes, expiry: str = "24h") -> None:
        multi = QHttpMultiPart(QHttpMultiPart.ContentType.FormDataType)
        fields = [("reqtype", b"fileupload")]
        if expiry != PERMANENT:
            fields.append(("time", expiry.encode()))
        for name, value in fields:
            part = QHttpPart()
            part.setHeader(QNetworkRequest.KnownHeaders.ContentDispositionHeader, f'form-data; name="{name}"')
            part.setBody(value)
            multi.append(part)
        file_part = QHttpPart()
        file_part.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "image/png")
        file_part.setHeader(
            QNetworkRequest.KnownHeaders.ContentDispositionHeader,
            'form-data; name="fileToUpload"; filename="captua.png"',
        )
        file_part.setBody(png)
        multi.append(file_part)

        req = QNetworkRequest(QUrl(CATBOX_URL if expiry == PERMANENT else LITTERBOX_URL))
        req.setRawHeader(b"User-Agent", b"captua")
        req.setTransferTimeout(_TIMEOUT_MS)
        reply = self._nam.post(req, multi)
        multi.setParent(reply)  # keep the parts alive until the reply is gone
        reply.uploadProgress.connect(self.progress.emit)
        reply.finished.connect(lambda: self._on_reply(reply))

    def _on_reply(self, reply: QNetworkReply) -> None:
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                self.failed.emit(reply.errorString())
                return
            link = parse_link(bytes(reply.readAll().data()).decode("utf-8", "replace"))
            if link is None:
                self.failed.emit("Unexpected response from the upload service.")
            else:
                self.finished.emit(link)
        finally:
            reply.deleteLater()
