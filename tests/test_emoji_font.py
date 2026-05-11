"""Tests for emoji font fallback in popups."""
from unittest.mock import patch

import pytest
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def test_emoji_popup_does_not_hardcode_noto(qapp):
    """EmojiPopup font must go through _emoji_font_family(), not hardcode Noto."""
    import captua.items as items_mod
    import captua.popups as popups_mod
    from captua.popups import EmojiPopup

    calls = []
    original = items_mod._emoji_font_family

    def _spy():
        calls.append(True)
        return original()

    # Patch in the popups module's namespace (where the from-import lands)
    with patch.object(popups_mod, "_emoji_font_family", side_effect=_spy):
        popup = EmojiPopup()

    assert calls, "_emoji_font_family() was never called by EmojiPopup"


def test_emoji_font_family_falls_back_when_noto_missing(qapp):
    """_emoji_font_family should return empty string if no known emoji font is installed."""
    from captua import items as items_mod

    # Reset cached value
    items_mod._EMOJI_FONT_FAMILY = None

    with patch.object(QFontDatabase, "families", return_value=[]):
        result = items_mod._emoji_font_family()

    assert result == ""  # graceful fallback
    items_mod._EMOJI_FONT_FAMILY = None  # reset after test
