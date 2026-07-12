# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Captua is a Shottr-style screenshot annotation tool for Linux/Wayland, built with Python 3.11+ and PySide6 (Qt6). Wayland-only — relies on `grim`, `slurp`, and `wl-clipboard`.

**System dependencies:** `grim`, `slurp`, `wl-clipboard`

## Commands

```bash
# Install in editable mode (recommended for development)
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# Run without installing
./run.sh [--screen | -s | --window | -w]

# Run directly
python3 -m captua.main [--screen | -s | --window | -w]
```

No linter config. Type-check with `mypy captua/`. Run tests:

```bash
# Install with dev deps
pip install -e ".[dev]"

# Run all tests
pytest

# Run a single test file
pytest tests/test_history.py -v
```

## Architecture

```
main.py           → QApplication setup, CLI arg parsing, capture dispatch, screen selection
capture.py        → ALL subprocess calls (grim, slurp, hyprctl, wl-copy); only file that shells out
overlay.py        → OverlayWindow (QMainWindow): owns toolbar + canvas, wires all signals,
                    handles export (render_to_pixmap), clipboard, save, import, backdrop dialog,
                    auto-save-on-copy
canvas.py         → CanvasScene (QGraphicsScene) + CanvasView (QGraphicsView):
                    scene holds image layers (z=0) + annotations (z>0);
                    view handles zoom/pan, resize handles, tool routing, key shortcuts,
                    magnetic snap (snap_rect/snap_point), keyboard-shortcut overlay (`?`)
toolbar.py        → Top bar: action buttons, tool buttons with icons, contextual property
                    controls (colour/width/fill alpha), emits signals for tool/property changes
icons.py          → Programmatically-drawn monochrome 20×20 toolbar icons via QPainter
tools.py          → All annotation tool classes (SelectTool, PenTool, ArrowTool, etc.)
                    each tool gets (scene, props, history) and implements mouse_press/move/release
items.py          → QGraphicsItem subclasses for all annotations and CanvasImageItem
history.py        → Undo/redo command stack (push/undo/redo)
settings.py       → JSON persistence to ~/.config/captua/settings.json (backdrop prefs,
                    default tool properties, auto-save, update-check settings)
backdrop.py       → BackdropPopup: live-preview dialog for backdrop settings
colorwheel.py     → Color picker dialog
popups.py         → EmojiPicker and shape selector popups
shapes.py         → Pre-defined QPainterPath shapes (heart, star, etc.)
emojipicker.py    → Emoji data model
updater.py        → Async GitHub release checker (QNetworkAccessManager), runs 3s after startup
update_dialog.py  → Non-modal, stay-on-top dialog: changelog + Update Now / Ask Again / Skip
self_updater.py   → git pull origin main + pip install -e . + os.execl restart (git-clone installs only)
```

### Key design points

- **draw_backdrop()** in `canvas.py` is shared: called in `CanvasView.drawBackground()` (editor view, not exported) and in `OverlayWindow.render_to_pixmap()` (export). The checkerboard in `drawBackground()` is intentionally skipped during export.
- **scene_rect_fitted** signal: `CanvasScene` emits this (not `sceneRectChanged`) when items expand the scene; `OverlayWindow._on_scene_rect_fitted()` resizes the window (grow only, capped at 90% screen, never below toolbar minimum width).
- **Auto-switch to select**: `CanvasView` emits `tool_finished` after any non-select, non-crop, non-counter tool completes a draw; `OverlayWindow` connects this to switch back to SelectTool.
- **Tool routing**: `CanvasView` checks `_tool_handles_mouse` first; falls through to resize-handle detection, then magnifier-glass drag, then Qt default (item drag/select).
- **Wayland constraint**: `resize()` is used instead of `setGeometry()` — Wayland ignores window position requests.
- **Blur/Magnifier pipeline**: Both tools use `QBuffer`/`BytesIO` for in-memory PNG encode/decode — no disk I/O.
- **Auto-save on copy**: When `auto_save_on_copy` is true (default), `Ctrl+C`/Copy copies to clipboard, saves to `~/Pictures/Screenshots/captua-<timestamp>.png`, shows a brief toast, then closes the app.
- **Magnetic snap**: Toggled via toolbar. `snap_rect()` aligns edges/centerlines of a moving item against all other items (including the base image) within 15px; drawing tools call `snap_point()` for corner/edge alignment unless Shift is held.
- **Shift constraints while drawing**: Rectangle→square, Ellipse→circle, Line/Arrow→45° snap, Pen→Bezier smoothing, Marker→straight line, Spotlight/Blur→square.
- **Eyedropper** (`D`): viewport QLabel overlay (not a scene item) shows live HEX+RGB under the cursor; click copies HEX to clipboard; stays active until another tool is chosen.
- **Spotlight resize**: `SpotlightItem` exposes `rect()`/`setRect()` so `CanvasView` resize handles work on its inner transparent rectangle; `mousePressEvent` selects on any click, drag inside moves the inner rect.
- **Auto-updater**: 3s after startup, checks GitHub releases; if newer and not skipped, shows the non-modal `update_dialog`. "Update Now" runs `self_updater.py` (git pull + reinstall + restart) if running from a git clone, otherwise opens the release page in the browser. "Skip This Version" persists to settings.

## Coding Style

- Type hints throughout; use them on all new functions/methods.
- Qt enums fully qualified: `Qt.AspectRatioMode.KeepAspectRatio`, not `Qt.KeepAspectRatio`.
- Explicit imports, no wildcard imports.
- `ToolProperties` (in `tools.py`) is the shared state bag passed to all tools; add new tool properties there.
