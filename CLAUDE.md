# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Captua is a Shottr-style screenshot annotation tool for Linux/Wayland (Arch + Hyprland), built with Python 3.12+ and PySide6 (Qt6).

**System dependencies:** `grim`, `slurp`, `wl-clipboard` (Arch: `pacman -S grim slurp wl-clipboard`)

## Commands

```bash
# Install in editable mode
pip install -e .

# Run without installing (also works via symlink from ~/.local/bin/)
./run.sh [--screen | -s | --window | -w]

# Run directly
python3 -m captua.main [--screen | -s | --window | -w]
```

No test suite, no linter config. Type-check manually with `mypy captua/` if needed.

## Architecture

```
main.py        → QApplication setup, CLI arg parsing, capture dispatch, screen selection
capture.py     → all subprocess calls (grim, slurp, wl-copy); only file that shells out
overlay.py     → OverlayWindow (QMainWindow): owns toolbar + canvas, wires all signals,
                 handles export (render_to_pixmap), clipboard, save, import, backdrop dialog
canvas.py      → CanvasScene (QGraphicsScene) + CanvasView (QGraphicsView):
                 scene holds image layers (z=0) + annotations (z>0);
                 view handles zoom/pan, resize handles, tool routing, key shortcuts
toolbar.py     → Top bar: emits signals for tool changes and property changes
tools.py       → All annotation tool classes (SelectTool, PenTool, ArrowTool, etc.)
                 each tool gets (scene, props, history) and implements mouse_press/move/release
items.py       → QGraphicsItem subclasses for annotations and CanvasImageItem
history.py     → Undo/redo command stack (push/undo/redo)
settings.py    → JSON persistence to ~/.config/captua/settings.json
backdrop.py    → BackdropDialog: live-preview dialog for backdrop settings
colorwheel.py  → Color picker dialog
popups.py      → EmojiPicker and shape selector popups
shapes.py      → Pre-defined QPainterPath shapes (heart, star, etc.)
emojipicker.py → Emoji data model
```

### Key design points

- **draw_backdrop()** in `canvas.py` is shared: called in `CanvasView.drawBackground()` (editor view, not exported) and in `OverlayWindow.render_to_pixmap()` (export only). The checkerboard in `drawBackground()` is intentionally skipped during export.
- **scene_rect_fitted** signal: `CanvasScene` emits this (not `sceneRectChanged`) when items expand the scene; `OverlayWindow._on_scene_rect_fitted()` resizes the window accordingly (grow only, capped at 90% screen, never below toolbar minimum width).
- **Auto-switch to select**: `CanvasView` emits `tool_finished` after any non-select, non-crop, non-counter tool completes a draw; `OverlayWindow` connects this to switch back to SelectTool.
- **Tool routing**: `CanvasView` checks `_tool_handles_mouse` first; falls through to resize-handle detection, then magnifier-glass drag, then Qt default (item drag/select).
- **Wayland constraint**: `resize()` is used instead of `setGeometry()` — Wayland ignores window position requests.

## Coding Style

- Type hints throughout; use them on all new functions/methods.
- Qt enums fully qualified: `Qt.AspectRatioMode.KeepAspectRatio`, not `Qt.KeepAspectRatio`.
- Explicit imports, no wildcard imports.
- `ToolProperties` (in `tools.py`) is the shared state bag passed to all tools; add new tool properties there.
