"""Frameless overlay window that displays the captured screenshot."""

# Pixels of checkerboard visible around the scene/backdrop when the window opens.
_VIEWPORT_MARGIN = 50

# Pixels of window chrome around the content (screenshot + annotations).
_WINDOW_MARGIN = 50

# Hard lower bound for the window width.
_MIN_WINDOW_WIDTH = 280


def compute_window_size(
    content_w: float,
    content_h: float,
    toolbar_h: int,
    max_w: int,
    max_h: int,
    min_w: int = _MIN_WINDOW_WIDTH,
    toolbar_w: int = 0,
) -> tuple[int, int]:
    """Fixed window size: content plus a 50px margin and the toolbar height.

    Capped at the available screen space (max_w/max_h). The window is at
    least min_w and at least toolbar_w wide so the pill toolbar fits
    without scrolling in the common (select-tool) case.
    """
    w = min(max(int(content_w) + _WINDOW_MARGIN, min_w, toolbar_w), max_w)
    h = min(max(int(content_h) + _WINDOW_MARGIN + toolbar_h, 0), max_h)
    return w, h

import shutil
import sys
import subprocess
import threading
import os
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QBuffer, QIODevice, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from . import __version__
from .backdrop import BackdropPopup
from .canvas import CanvasScene, CanvasView, draw_backdrop
from .uploader import PERMANENT, Uploader
from .settings import apply_to_scene, extract_from_scene, load_settings, save_settings
from .history import capture_state, push_changes
from .imageio import load_image_file
from .theme import DIALOG_STYLE, PROGRESS_STYLE, TOAST_STYLE, WINDOW_BG
from .toolbar import Toolbar
from .tools import (
    ArrowTool,
    BlurTool,
    CounterTool,
    CropTool,
    EllipseTool,
    EmojiTool,
    EyedropperTool,
    LabelTool,
    LineTool,
    MagnifierTool,
    MarkerTool,
    PenTool,
    RectangleTool,
    RulerTool,
    SelectTool,
    ShapeTool,
    SpotlightTool,
    TextTool,
    ToolProperties,
)


def _write_new_file(path: Path, data: bytes) -> Path:
    """Create `path` (owner-only) without ever overwriting or following a link;
    on a name clash use -2, -3, … instead. Returns the path actually written."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    n = 1
    while True:
        target = path if n == 1 else path.with_name(f"{path.stem}-{n}{path.suffix}")
        try:
            fd = os.open(target, flags, 0o600)
        except FileExistsError:
            n += 1
            continue
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        return target


def _deliver_png(
    image: "QImage",
    save_path: Path | None,
    use_wl_copy: bool,
) -> tuple[bool, str]:
    """Background worker: encode PNG once, auto-save it, hand it to wl-copy.

    Runs off the UI thread. Encoding a QImage (not QPixmap) and writing the
    file here keeps the UI responsive. Returns (success, saved_filename);
    success is False only when the auto-save write failed — wl-copy delivery
    is best-effort.
    """
    try:
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, "PNG")
        png_data = bytes(buffer.data())
        buffer.close()
    except Exception:
        return False, ""

    saved_name = ""
    if save_path is not None:
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            saved_name = _write_new_file(save_path, png_data).name
        except OSError:
            return False, ""

    if use_wl_copy:
        try:
            proc = subprocess.Popen(
                ["wl-copy", "--type", "image/png"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            proc.stdin.write(png_data)
            proc.stdin.close()
            # Wait until wl-copy has taken over the data so the clipboard
            # survives the app exiting right after.
            proc.wait(timeout=5)
        except Exception:
            pass

    return True, saved_name


class OverlayWindow(QMainWindow):
    """
    A frameless, floating window for Hyprland/Wayland.

    Designed to work with these Hyprland windowrules:
        windowrule = float on, match:class ^(captua-overlay)$
        windowrule = center on, match:class ^(captua-overlay)$
        windowrule = pin on, match:class ^(captua-overlay)$
    """

    copy_finished = Signal(bool, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # Window flags for a clean overlay look.
        # WindowStaysOnTopHint is omitted under Wayland — Hyprland handles
        # pinning via windowrule instead, and the flag can prevent the
        # window from showing at all on some compositors.
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
        )

        # Background colour (dark, modern)
        self.setStyleSheet(f"background-color: {WINDOW_BG};")
        self.setAcceptDrops(True)

        # Central widget: the canvas fills the whole window; the toolbar
        # pills float on top of it (not part of the layout).
        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)

        # Four floating pill toolbars (corners) — created as children of
        # this window by Toolbar, positioned in _place_pills().
        self._toolbar = Toolbar(self)
        self._toolbar.pills_changed.connect(self._place_pills)
        self._pills_hidden = False
        self.setMinimumWidth(280)
        self._backdrop_popup: BackdropPopup | None = None

        # Toast label for ephemeral status messages
        self._toast = QLabel(self)
        self._toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._toast.setStyleSheet(TOAST_STYLE)
        self._toast.hide()

        # Faint version tag in the bottom-right corner, below the pills
        self._version_label = QLabel(f"v{__version__}", self)
        self._version_label.setStyleSheet(
            "color: rgba(154, 154, 162, 0.45); font-size: 8px; background: transparent;"
        )
        self._version_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._version_label.adjustSize()

        # Canvas fills the whole window below the floating toolbar
        self._scene = CanvasScene(self)
        self._view = CanvasView(self._scene, self)
        layout.addWidget(self._view)

        # Tools
        self._props = ToolProperties()
        history = self._scene.history()
        self._tools = {
            "select": SelectTool(self._scene, self._props, history),
            "crop": CropTool(self._scene, self._props, history),
            "rectangle": RectangleTool(self._scene, self._props, history),
            "ellipse": EllipseTool(self._scene, self._props, history),
            "line": LineTool(self._scene, self._props, history),
            "arrow": ArrowTool(self._scene, self._props, history),
            "pen": PenTool(self._scene, self._props, history),
            "marker": MarkerTool(self._scene, self._props, history),
            "text": TextTool(self._scene, self._props, history),
            "label": LabelTool(self._scene, self._props, history),
            "counter": CounterTool(self._scene, self._props, history),
            "ruler": RulerTool(self._scene, self._props, history),
            "spotlight": SpotlightTool(self._scene, self._props, history),
            "blur": BlurTool(self._scene, self._props, history),
            "magnifier": MagnifierTool(self._scene, self._props, history),
            "eyedropper": EyedropperTool(self._scene, self._props, history),
            "shape": ShapeTool(self._scene, self._props, history),
            "emoji": EmojiTool(self._scene, self._props, history),
        }
        self._set_tool("select")

        # Load persisted settings
        self._settings = load_settings()
        apply_to_scene(self._scene, self._settings)

        # Sticky tools: keep the active tool after drawing instead of
        # auto-switching back to select
        self._sticky_tools = bool(self._settings.get("sticky_tools", False))
        self._toolbar.set_sticky(self._sticky_tools)

        # Apply default tool properties from settings
        self._props.color = QColor(self._settings.get("line_color", "#F23C3C"))
        self._props.stroke_width = self._settings.get("line_width", 3)
        self._props.fill_color = QColor(self._settings.get("fill_color", "#F23C3C"))
        self._props.fill_alpha = self._settings.get("fill_alpha", 128)
        self._toolbar.set_line_color(self._props.color)
        self._toolbar.set_line_width(self._props.stroke_width)
        self._toolbar.set_fill_color(self._props.fill_color)
        self._toolbar.set_fill_alpha(self._props.fill_alpha)


        # Toolbar signals
        self._toolbar.tool_changed.connect(self._set_tool)
        self._toolbar.line_color_changed.connect(self._update_line_color)
        self._toolbar.line_width_changed.connect(self._update_line_width)
        self._toolbar.fill_color_changed.connect(self._update_fill_color)
        self._toolbar.fill_alpha_changed.connect(self._update_fill_alpha)
        self._toolbar.shape_selected.connect(self._update_shape)
        self._toolbar.emoji_selected.connect(self._update_emoji)
        self._toolbar.close_triggered.connect(self.close)
        self._toolbar.save_triggered.connect(self.save_to_disk)
        self._toolbar.copy_triggered.connect(self.copy_to_clipboard)
        self._toolbar.upload_triggered.connect(self.upload_image)
        self._toolbar.import_image_triggered.connect(self._import_image)
        self._toolbar.capture_triggered.connect(self._capture_region)
        self._toolbar.backdrop_settings_triggered.connect(self._show_backdrop_dialog)
        self._toolbar.magnifier_zoom_changed.connect(self._update_magnifier_zoom)
        self._toolbar.snap_toggled.connect(self._update_snap)
        self._toolbar.sticky_toggled.connect(self._update_sticky)

        self._view.tool_finished.connect(self._on_tool_finished)
        self._view.tool_selected.connect(self._set_tool)
        self._scene.selectionChanged.connect(self._on_selection_changed)
        self._scene.scene_rect_fitted.connect(self._on_scene_rect_fitted)
        self._copy_in_progress = False
        self.copy_finished.connect(self._on_copy_finished)
        self._uploading = False
        self._upload_bar = None
        self._upload_png = b""
        self._upload_expiry = ""
        self._uploader = Uploader(self)
        self._uploader.finished.connect(self._on_upload_finished)
        self._uploader.failed.connect(self._on_upload_failed)

    def _set_tool(self, name: str) -> None:
        tool = self._tools.get(name)
        self._view.set_active_tool(tool)
        self._toolbar.update_active_tool_button(name)
        self._toolbar.set_zoom_visible(name == "magnifier" or self._selected_has_zoom())

    def _selected_has_zoom(self) -> bool:
        items = [i for i in self._scene.selectedItems() if i is not self._scene.base_image()]
        return len(items) == 1 and hasattr(items[0], "zoom_level")

    def _edit_selected(self, setter: str, value) -> None:
        """Apply a style change to the selection as one undoable step."""
        base = self._scene.base_image()
        items = [i for i in self._scene.selectedItems() if i is not base and hasattr(i, setter)]
        before = {i: capture_state(i) for i in items}
        for item in items:
            getattr(item, setter)(value)
        push_changes(self._scene, before)

    def _update_line_color(self, color) -> None:
        self._props.color = color
        self._edit_selected("set_line_color", color)

    def _update_line_width(self, width: float) -> None:
        self._props.stroke_width = width
        self._edit_selected("set_line_width", width)

    def _update_fill_color(self, color) -> None:
        self._props.fill_color = color
        self._edit_selected("set_fill_color", color)

    def _update_fill_alpha(self, alpha: int) -> None:
        self._props.fill_alpha = alpha
        self._edit_selected("set_fill_alpha", alpha)

    def _on_selection_changed(self) -> None:
        items = [i for i in self._scene.selectedItems() if i is not self._scene.base_image()]
        self._toolbar.set_zoom_visible(self._toolbar.active_tool() == "magnifier" or self._selected_has_zoom())
        if len(items) != 1:
            return
        item = items[0]
        if hasattr(item, "line_color"):
            self._toolbar.set_line_color(item.line_color())
            self._props.color = item.line_color()
        if hasattr(item, "line_width"):
            self._toolbar.set_line_width(item.line_width())
            self._props.stroke_width = item.line_width()
        if hasattr(item, "fill_color"):
            self._toolbar.set_fill_color(item.fill_color())
            self._props.fill_color = item.fill_color()
        if hasattr(item, "fill_alpha"):
            self._toolbar.set_fill_alpha(item.fill_alpha())
            self._props.fill_alpha = item.fill_alpha()
        if hasattr(item, "zoom_level"):
            self._toolbar.set_magnifier_zoom(item.zoom_level())
            self._props.zoom_level = item.zoom_level()

    def _update_shape(self, shape_type: str) -> None:
        self._props.shape_type = shape_type

    def _update_emoji(self, emoji: str) -> None:
        self._props.emoji = emoji

    def _update_magnifier_zoom(self, zoom: float) -> None:
        self._props.zoom_level = zoom
        self._edit_selected("set_zoom_level", zoom)

    def _update_snap(self, enabled: bool) -> None:
        self._scene.snap_enabled = enabled

    def _update_sticky(self, enabled: bool) -> None:
        self._sticky_tools = enabled

    def _on_tool_finished(self) -> None:
        """Auto-switch back to select after a draw — unless sticky tools are on."""
        if not self._sticky_tools:
            self._set_tool("select")

    def _capture_region(self) -> None:
        """Capture a new region and add it to the canvas."""
        try:
            from .capture import CaptureCancelled, capture_region
            pixmap = capture_region()
            if pixmap is not None and not pixmap.isNull():
                try:
                    dpr = self.screen().devicePixelRatio()
                except Exception:
                    dpr = 1.0
                pixmap.setDevicePixelRatio(dpr)
                center = self._view.mapToScene(self._view.viewport().rect().center())
                pos = center - QPointF(pixmap.width() / 2, pixmap.height() / 2)
                self._scene.add_image(pixmap, pos)
        except CaptureCancelled:
            return
        except RuntimeError as exc:
            # slurp/Spectacle report a cancelled selection as a failed command
            self._show_toast("Capture cancelled or failed", 2500)
            print(f"Capture failed: {exc}", file=sys.stderr)

    def _import_image(self) -> None:
        """Open a file dialog to import an image onto the canvas."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Image",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif)",
        )
        if file_path:
            pixmap = load_image_file(file_path)
            if pixmap is not None:
                # Place at center of current view
                center = self._view.mapToScene(self._view.viewport().rect().center())
                pos = center - QPointF(pixmap.width() / 2, pixmap.height() / 2)
                self._scene.add_image(pixmap, pos)

    def paste_from_clipboard(self) -> None:
        """Paste image from clipboard onto the canvas."""
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()
        if mime is None:
            return

        # Try image data first
        if mime.hasImage():
            from PySide6.QtGui import QImage
            img = mime.imageData()
            if isinstance(img, QImage):
                pixmap = QPixmap.fromImage(img)
                if not pixmap.isNull():
                    center = self._view.mapToScene(self._view.viewport().rect().center())
                    pos = center - QPointF(pixmap.width() / 2, pixmap.height() / 2)
                    self._scene.add_image(pixmap, pos)
                    return

        # Try URLs
        if mime.hasUrls():
            for url in mime.urls():
                if url.isLocalFile():
                    pixmap = load_image_file(url.toLocalFile())
                    if pixmap is not None:
                        center = self._view.mapToScene(self._view.viewport().rect().center())
                        pos = center - QPointF(pixmap.width() / 2, pixmap.height() / 2)
                        self._scene.add_image(pixmap, pos)
                        return

    def _show_backdrop_dialog(self) -> None:
        """Show backdrop settings popup below toolbar button."""
        self._backdrop_popup = BackdropPopup(self._scene, self._view)
        self._backdrop_popup.show_below(self._toolbar.backdrop_button())

    def set_crop_mode(self, enabled: bool) -> None:
        """Hide toolbar pills and activate crop tool; called for region/window modes."""
        self._pills_hidden = enabled
        if enabled:
            self._toolbar.set_pills_visible(False)
            self._set_tool("crop")
            self._toolbar.set_tool("crop")
        else:
            self._toolbar.set_pills_visible(True)
            self._set_tool("select")
            self._toolbar.set_tool("select")

    def _screen_constraints(self) -> tuple[int, int, int, int]:
        """Return (margin, max_w, max_h) for window sizing.

        Uses availableGeometry() rather than geometry() so bars/panels
        (waybar, DankMaterialShell top bar, etc.) are excluded — the window
        must never exceed the actually usable screen space. A fixed pixel
        margin is also reserved on top of that so the window keeps a
        visible floating gap instead of touching the available area's edges.
        """
        try:
            available = self.screen().availableGeometry()
        except Exception:
            available = None
        margin = 40
        if available is not None:
            max_w = available.width() - margin * 2
            max_h = available.height() - margin * 2
        else:
            max_w = 1920
            max_h = 1080
        return margin, max_w, max_h

    def _toolbar_zone(self) -> int:
        """Vertical space reserved for the floating pills (top and bottom)."""
        return 2 * (self._toolbar.pill_close.height() + 16)

    def _place_pills(self) -> None:
        """Put the floating pills into the four window corners."""
        tb = self._toolbar
        m = 10
        gap = 8
        # top-left: close — top-right: actions
        tb.pill_close.move(m, m)
        ax = max(m + tb.pill_close.width() + gap, self.width() - m - tb.pill_actions.width())
        tb.pill_actions.move(ax, m)
        # bottom-left: tools — bottom-right: contextual properties
        yb = self.height() - m - tb.pill_tools.height()
        tb.pill_tools.move(m, yb)
        px = max(m + tb.pill_tools.width() + gap, self.width() - m - tb.pill_props.width())
        tb.pill_props.move(px, yb)
        # Properties stay visible whenever they fit beside the tools
        fits = px + tb.pill_props.width() + m <= self.width()
        tb.pill_props.setVisible(fits and tb.pill_tools.isVisible())
        vl = self._version_label
        vl.move(self.width() - vl.width() - 8, self.height() - vl.height())
        vl.raise_()
        for pill in (tb.pill_close, tb.pill_actions, tb.pill_tools, tb.pill_props):
            pill.raise_()

    def _resize_for_scene(self) -> None:
        """Resize window to the actual content (screenshot + annotations)
        plus a fixed 50px margin and the toolbar height. Deliberately ignores
        the scene's decorative backdrop padding (user-configurable, up to
        120px). The window is at least as wide as the pill toolbar (plus the
        central layout margins) so it fits without scrolling."""
        _, max_w, max_h = self._screen_constraints()
        content_rect = self._scene.content_rect()
        toolbar_w = self._toolbar.full_width()  # all four pills + margins
        new_w, new_h = compute_window_size(
            content_rect.width(),
            content_rect.height(),
            self._toolbar_zone(),
            max_w,
            max_h,
            toolbar_w=toolbar_w,
        )
        self.resize(new_w, new_h)

    def _on_scene_rect_fitted(self, old_rect: QRectF, new_rect: QRectF) -> None:
        """Scene grew past the image edge (annotation drawn outside, image
        added, ...): grow the window to keep the content visible.

        Grow-only — the window never shrinks below its initial fit. The
        decorative backdrop padding is ignored (content_rect excludes it).
        Content beyond the available screen space stays reachable via
        pan/zoom."""
        _, max_w, max_h = self._screen_constraints()
        content_rect = self._scene.content_rect()
        toolbar_w = self._toolbar.full_width()
        need_w, need_h = compute_window_size(
            content_rect.width(),
            content_rect.height(),
            self._toolbar_zone(),
            max_w,
            max_h,
            toolbar_w=toolbar_w,
        )
        new_w = min(max(self.width(), need_w), max_w)
        new_h = min(max(self.height(), need_h), max_h)
        if new_w != self.width() or new_h != self.height():
            self.resize(new_w, new_h)
        self._view.viewport().update()

    def set_image(self, pixmap: QPixmap) -> None:
        """Load a new screenshot into the canvas."""
        # Apply screen DPR so the pixmap renders 1:1 with physical pixels
        try:
            dpr = self.screen().devicePixelRatio()
        except Exception:
            dpr = 1.0
        pixmap.setDevicePixelRatio(dpr)

        self._scene.set_base_image(pixmap)
        self._resize_for_scene()
        if self.isVisible():
            self._fit_image()

    def _fit_image(self) -> None:
        """Show content at 1:1 centered (margin visible) or scaled if screen-capped.

        Fits against the actual content (screenshot + annotations), not the
        full sceneRect — the sceneRect also carries the decorative, user-
        configurable backdrop padding (up to 120px), which must never force
        the real screenshot to shrink just because the window (correctly
        sized to content + 50px) is smaller than that padded sceneRect.

        The content is centered in the viewport — the floating pills reserve
        equal zones at the top and bottom, so a plain center keeps the
        screenshot clear of them."""
        content_rect = self._scene.content_rect()
        view_rect = self._view.viewport().rect()
        if content_rect.width() <= view_rect.width() and content_rect.height() <= view_rect.height():
            # Fits at 1:1 — window was sized with margin, so checkerboard shows around it
            self._view.resetTransform()
            self._view.centerOn(content_rect.center())
        else:
            # Screen-capped window: scale to fit, keep margin where possible
            scale = min(
                max((view_rect.width() - _VIEWPORT_MARGIN * 2), 1) / content_rect.width(),
                max((view_rect.height() - self._toolbar_zone() - _VIEWPORT_MARGIN), 1) / content_rect.height(),
            )
            self._view.resetTransform()
            self._view.scale(scale, scale)
            self._view.centerOn(content_rect.center())

    def showEvent(self, event) -> None:
        """Recompute sizing once the window actually has a platform window.

        Before the first show(), self.screen() can report the screen under
        the OS cursor instead of the one set via setScreen() (no platform
        window exists yet for Qt to bind to), which corrupts the available-
        space calculation in _resize_for_scene(). Recomputing here, after
        super().showEvent() has created the real platform window, uses the
        correct screen.
        """
        super().showEvent(event)
        if self._scene.base_image() is not None:
            self._toolbar.refresh_full_width()
            self._resize_for_scene()
            self._fit_image()
            # Some compositors impose a default height on freshly opened
            # floating windows (e.g. a niri window-rule with
            # `default-window-height { proportion 1.0 }`). Re-assert our
            # computed size once the compositor has had its say.
            QTimer.singleShot(120, self._reassert_size)
            QTimer.singleShot(500, self._reassert_size)
        self._toolbar.set_pills_visible(not self._pills_hidden)
        self._place_pills()
        # Grab keyboard focus immediately so modifier keys (e.g. Ctrl for
        # zoom) are recognised without requiring a click into the canvas first.
        self.activateWindow()
        self._view.setFocus(Qt.FocusReason.ActiveWindowFocusReason)

    def _reassert_size(self) -> None:
        """Re-apply the computed window size (see showEvent note)."""
        if self._scene.base_image() is not None:
            self._resize_for_scene()
            self._fit_image()

    def closeEvent(self, event) -> None:
        """Persist all current settings on window close.

        Merges over the loaded settings so keys managed elsewhere
        (screenshots folder/template, update check, skipped version,
        auto-save toggle) are not wiped on every close."""
        if self._copy_in_progress:
            # Closing now would kill the delivery thread before wl-copy has the data
            event.ignore()
            return
        # "Skip version" is saved by the update dialog while the window is open
        stored = {**self._settings, **extract_from_scene(self._scene)}
        stored["skipped_version"] = load_settings().get("skipped_version", "")
        stored["line_color"] = self._props.color.name()
        stored["line_width"] = self._props.stroke_width
        stored["fill_color"] = self._props.fill_color.name()
        stored["fill_alpha"] = self._props.fill_alpha
        stored["sticky_tools"] = self._sticky_tools
        try:
            save_settings(stored)
        except OSError as exc:
            print(f"Could not save settings: {exc}", file=sys.stderr)
        super().closeEvent(event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._place_pills()

    def render_to_pixmap(self) -> QPixmap:
        """Render the entire scene (with backdrop) to a pixmap at physical resolution."""
        base = self._scene.base_image()
        dpr = base.pixmap().devicePixelRatio() if base else 1.0

        # Full bounds of all items, plus backdrop padding
        items_rect = self._scene.itemsBoundingRect()
        pad = self._scene.backdrop_padding if self._scene.backdrop_enabled else 0
        render_rect = items_rect.adjusted(-pad, -pad, pad, pad)

        physical_w = max(1, int(render_rect.width() * dpr))
        physical_h = max(1, int(render_rect.height() * dpr))
        pixmap = QPixmap(physical_w, physical_h)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = None
        try:
            from PySide6.QtGui import QPainter
            painter = QPainter(pixmap)
            painter.scale(dpr, dpr)
            painter.save()
            painter.translate(-render_rect.x(), -render_rect.y())
            draw_backdrop(painter, self._scene, self._scene._content_rect)
            painter.restore()
            # Hide selection decorations during export
            selected = list(self._scene.selectedItems())
            for item in selected:
                item.setSelected(False)
            # Render scene items on top
            self._scene.render(painter, QRectF(0, 0, render_rect.width(), render_rect.height()), render_rect)
            # Restore selection
            for item in selected:
                item.setSelected(True)
        finally:
            if painter is not None:
                painter.end()
        return pixmap

    def _auto_save_path(self) -> Path:
        """Compute the auto-save target path from the configured folder/template."""
        folder = Path(self._settings.get("screenshots_folder", "~/Pictures/Screenshots")).expanduser()
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        template = self._settings.get("screenshot_filename_template", "captua-{timestamp}.png")
        filename = template.replace("{timestamp}", ts).replace("{date}", datetime.now().strftime("%Y-%m-%d"))
        filename = Path(filename).name or f"captua-{ts}.png"  # no ../ or absolute paths
        path = folder / filename
        n = 2
        while path.exists():
            path = folder / f"{Path(filename).stem}-{n}{Path(filename).suffix}"
            n += 1
        return path

    def _show_toast(self, message: str, duration_ms: int = 1500) -> None:
        """Show a transient status label centered in the window."""
        from PySide6.QtWidgets import QLabel
        if self._toast is None:
            self._toast = QLabel(self)
            self._toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._toast.setStyleSheet(TOAST_STYLE)
        self._toast.setText(message)
        self._toast.adjustSize()
        x = (self.width() - self._toast.width()) // 2
        y = self.height() - self._toast.height() - 20
        self._toast.move(x, y)
        self._toast.raise_()
        self._toast.show()
        QTimer.singleShot(duration_ms, self._toast.hide)

    def copy_to_clipboard(self) -> None:
        """Render scene, copy to clipboard, auto-save in the background, close.

        Only the render and the QClipboard handoff run on the UI thread;
        PNG encoding, disk write and wl-copy delivery happen in a background
        thread that reports back via copy_finished. The window closes as soon
        as the delivery is done — no artificial delay."""
        if self._copy_in_progress:
            return
        self._copy_in_progress = True
        self._toolbar.set_copy_enabled(False)

        pixmap = self.render_to_pixmap()
        image = pixmap.toImage()
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            # Use setImage instead of setPixmap — it is more reliable on Wayland
            clipboard.setImage(image)

        auto_save = self._settings.get("auto_save_on_copy", True)
        save_path = self._auto_save_path() if auto_save else None
        use_wl_copy = shutil.which("wl-copy") is not None
        threading.Thread(
            target=self._deliver_copy,
            args=(image, save_path, use_wl_copy),
            daemon=True,
        ).start()

    def _dialog(self, icon, title: str, text: str, ask: bool = False) -> bool:
        """Themed message box; returns True when the user confirmed (ask=True)."""
        box = QMessageBox(icon, title, text, parent=self)
        box.setStyleSheet(DIALOG_STYLE)
        if ask:
            box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        return box.exec() == QMessageBox.StandardButton.Yes

    def upload_image(self, permanent: bool = False) -> None:
        """Upload the rendered scene (Litterbox, or Catbox if permanent) and copy the link.

        Asks for consent each time for permanent uploads (they cannot be deleted
        anonymously), once for temporary ones."""
        if self._uploading:
            return
        if permanent:
            question = (
                "The image is sent to catbox.moe, a third-party host, and stays online "
                "permanently. Anonymous uploads cannot be deleted. Anyone with the link can view it."
            )
        elif not self._settings.get("upload_consent"):
            question = (
                "The image is sent to litterbox.catbox.moe, a third-party host. Anyone with "
                f"the link can view it until it expires ({self._settings.get('upload_expiry', '24h')})."
            )
        else:
            question = ""
        if question:
            if not self._dialog(QMessageBox.Icon.Question, "Upload screenshot", f"{question}\n\nUpload now?", ask=True):
                return
            if not permanent:
                self._settings["upload_consent"] = True
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        self.render_to_pixmap().toImage().save(buffer, "PNG")
        self._upload_png = bytes(buffer.data())
        self._send_upload(PERMANENT if permanent else self._settings.get("upload_expiry", "24h"))

    def _send_upload(self, expiry: str) -> None:
        self._upload_expiry = expiry
        self._uploading = True
        self._toolbar.set_upload_enabled(False)
        self._show_upload_progress()
        self._uploader.upload(self._upload_png, expiry)

    def _show_upload_progress(self) -> None:
        """Centered progress bar; busy (range 0..0) until the first progress report."""
        if self._upload_bar is None:
            self._upload_bar = QProgressBar(self)
            self._upload_bar.setStyleSheet(PROGRESS_STYLE)
            self._upload_bar.setFixedWidth(280)
            self._uploader.progress.connect(self._on_upload_progress)
        self._upload_bar.setRange(0, 0)
        self._upload_bar.setFormat("Uploading…")
        self._upload_bar.move((self.width() - 280) // 2, self.height() - 105)  # above the bottom pills
        self._upload_bar.raise_()
        self._upload_bar.show()

    def _on_upload_progress(self, sent: int, total: int) -> None:
        if self._upload_bar is None or total <= 0:
            return
        self._upload_bar.setRange(0, total)
        self._upload_bar.setValue(sent)
        self._upload_bar.setFormat("Uploading… %p%" if sent < total else "Waiting for server…")

    def _hide_upload_progress(self) -> None:
        if self._upload_bar is not None:
            self._upload_bar.hide()

    def _on_upload_finished(self, link: str) -> None:
        self._hide_upload_progress()
        self._uploading = False
        self._toolbar.set_upload_enabled(True)
        QApplication.clipboard().setText(link)
        self._show_toast("Link copied")

    def _on_upload_failed(self, message: str, server_error: bool = False) -> None:
        self._hide_upload_progress()
        self._uploading = False
        self._toolbar.set_upload_enabled(True)
        self._show_toast("Upload failed")
        if server_error and self._upload_expiry != PERMANENT:
            if self._dialog(
                QMessageBox.Icon.Question,
                "Upload failed",
                f"{message}\n\nUpload permanently via catbox.moe instead? Anonymous uploads "
                "cannot be deleted, and anyone with the link can view the image.",
                ask=True,
            ):
                self._send_upload(PERMANENT)
        else:
            self._dialog(QMessageBox.Icon.Warning, "Upload failed", message)

    def _deliver_copy(self, image: QImage, save_path: Path | None, use_wl_copy: bool) -> None:
        ok, saved_name = _deliver_png(image, save_path, use_wl_copy)
        self.copy_finished.emit(ok, saved_name)

    def _on_copy_finished(self, ok: bool, saved_name: str) -> None:
        self._copy_in_progress = False
        self._toolbar.set_copy_enabled(True)
        if not ok:
            self._dialog(
                QMessageBox.Icon.Critical,
                "Save Failed",
                "Could not auto-save the screenshot to "
                f"{self._settings.get('screenshots_folder', '~/Pictures/Screenshots')}.\n"
                "Check the folder permissions or use Save As (Ctrl+S) instead.",
            )
            return
        # Closing right away is the feedback that the copy succeeded; wl-copy
        # has already taken over the clipboard data at this point.
        self.close()

    def save_to_disk(self) -> None:
        """Render scene and save to a user-selected file."""
        from PySide6.QtWidgets import QFileDialog
        pixmap = self.render_to_pixmap()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Screenshot",
            self._auto_save_path().name,
            "Images (*.png *.jpg *.webp)",
        )
        if file_path:
            pixmap.save(file_path)

