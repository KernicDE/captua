# Captua Agent Guide

## Project Structure

```
captua/
  __init__.py       # Package meta
  main.py           # Entry point: QApplication setup, capture mode dispatch
  capture.py        # grim/slurp/hyprctl integration (screenshot capture)
  overlay.py        # Frameless QMainWindow overlay; render/export; settings wiring; auto-save on copy
  canvas.py         # QGraphicsScene + QGraphicsView with zoom/pan, backdrop draw helper, shortcut overlay
  toolbar.py        # Top toolbar: action buttons, tool buttons with icons, contextual property controls
  icons.py          # Programmatically-drawn monochrome toolbar icons
  tools.py          # Annotation tool implementations (pen, arrow, text, etc.)
  items.py          # QGraphicsItem subclasses for annotations and images
  backdrop.py       # Backdrop settings dialog with live preview
  settings.py       # JSON-based persistent settings (~/.config/captua/settings.json)
  history.py        # Undo/redo command stack
  colorwheel.py     # Color picker dialog
  popups.py         # Emoji and shape selector popups
  shapes.py         # Pre-defined shape paths
  emojipicker.py    # Emoji data/model for popup
docs/
  GUIDE.md          # User-facing feature documentation
pyproject.toml      # Project config
```

## Tech Stack
- Python 3.11+
- PySide6 (Qt6)
- grim, slurp (system deps for screenshot capture on Wayland)

## Architecture
- `main.py` boots the app, decides capture mode, creates `OverlayWindow`
- `OverlayWindow` owns a `CanvasView` which owns a `CanvasScene`
- `CanvasScene` holds layers: base image (z=0), additional images (z=0), annotations (z>0)
- `CanvasView.drawBackground()` paints checkerboard + backdrop (not scene items)
- `CanvasView.drawForeground()` paints resize handles for selected rect items
- `capture.py` is the only module that shells out to system commands
- `settings.py` persists backdrop preferences, default tool properties, and auto-save settings to `~/.config/captua/settings.json`
- `icons.py` renders all toolbar icons as crisp 20×20 QPixmaps using QPainter

## Key Behaviours
- **Backdrop in exports**: `OverlayWindow.render_to_pixmap()` computes `itemsBoundingRect()`, draws the backdrop via `draw_backdrop()`, then renders scene items on top.
- **Window auto-resize**: `CanvasScene` emits `scene_rect_fitted` when items expand the scene; `OverlayWindow._on_scene_rect_fitted()` grows (never shrinks) the window to fit content, capped at 90% of screen. (`sceneRectChanged` is connected but its handler is a no-op.)
- **Auto-switch to select**: `CanvasView` emits `tool_finished` after non-select tools complete; `OverlayWindow` switches back to select mode.
- **Checkerboard not exported**: The checkerboard is drawn in `drawBackground()` but is intentionally skipped in `render_to_pixmap()`.
- **Auto-save on copy**: When `auto_save_on_copy` is true (default), pressing `Ctrl+C` or clicking Copy copies to clipboard via `QClipboard`, saves to `~/Pictures/Screenshots/captua-<timestamp>.png`, shows a brief toast, and closes the app.
- **Contextual properties**: The toolbar properties panel (colour, width, fill alpha) is only visible when a drawing tool is active or a single item is selected.
- **Keyboard shortcut overlay**: Press `?` to show a help overlay listing all shortcuts. Press `Esc` or `?` again to dismiss.

## Coding Style
- Type hints throughout
- Explicit imports, no wildcard imports
- Qt enums referenced fully (e.g., `Qt.AspectRatioMode.KeepAspectRatio`)
