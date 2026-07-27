"""Unit tests for the fixed window sizing logic."""

from captua.overlay import compute_window_size


class TestComputeWindowSize:
    def test_content_plus_margin(self) -> None:
        w, h = compute_window_size(800, 600, toolbar_h=80, max_w=1920, max_h=1080)
        assert w == 850  # content width + 50
        assert h == 730  # content height + 50 + toolbar

    def test_capped_at_available_width(self) -> None:
        w, _ = compute_window_size(5000, 600, toolbar_h=80, max_w=1840, max_h=1040)
        assert w == 1840

    def test_capped_at_available_height(self) -> None:
        _, h = compute_window_size(800, 5000, toolbar_h=80, max_w=1840, max_h=1040)
        assert h == 1040

    def test_minimum_width(self) -> None:
        w, _ = compute_window_size(100, 100, toolbar_h=80, max_w=1920, max_h=1080)
        assert w == 280

    def test_toolbar_width_does_not_inflate_window(self) -> None:
        # A narrow screenshot must not get a wide window just because the
        # toolbar prefers more space — the toolbar scrolls instead.
        w, _ = compute_window_size(300, 200, toolbar_h=80, max_w=1920, max_h=1080)
        assert w == 350
