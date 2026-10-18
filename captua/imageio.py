"""Safe loading of image files that come from outside (drop, paste, import)."""

import os
import stat

from PySide6.QtGui import QImageReader, QPixmap

_MAX_PIXELS = 100_000_000
_MAX_BYTES = 200 * 1024 * 1024
_FORMATS = {b"png", b"jpg", b"jpeg", b"bmp", b"webp", b"gif", b"tiff", b"tif"}


def load_image_file(path: str) -> QPixmap | None:
    """Load a regular image file; None if it is not one, too big, or unreadable.

    The check keeps FIFOs/devices from blocking the UI and image bombs from
    exhausting memory before a decoder runs."""
    try:
        st = os.stat(path)
    except OSError:
        return None
    if not stat.S_ISREG(st.st_mode) or st.st_size > _MAX_BYTES:
        return None
    reader = QImageReader(path)
    reader.setAutoTransform(True)
    size = reader.size()
    if bytes(reader.format().data()).lower() not in _FORMATS:
        return None
    if size.isValid() and size.width() * size.height() > _MAX_PIXELS:
        return None
    image = reader.read()
    if image.isNull():
        return None
    return QPixmap.fromImage(image)
