# Captua Agent Guide

## Project Overview

Captua is a fast, lightweight screenshot annotation tool (a Shottr clone) for **Linux / Wayland only**, written in Python with PySide6 (Qt6). It captures a region, screen, or window, opens it in a frameless overlay window with a `QGraphicsScene` canvas, and lets the user annotate, then copy or save the result.

- Current version: **0.4.1** (kept in sync in `captua/__init__.py` and `pyproject.toml`)
- Entry point: console script `captua = captua.main:main`
- CLI modes: `captua` (region, default), `captua --screen|-s`, `captua --window|-w`, `captua --help|-h`
- Repository: https://github.com/KernicDE/captua

## Tech Stack

- Python 3.11+, PySide6 >= 6.5, Pillow >= 10.0
- Build backend: hatchling (`pyproject.toml`)
- System dependencies (Wayland tools, installed via distro package manager):
  - `grim` — screenshot capture
  - `slurp` — region selection
  - `wl-clipboard` (`wl-copy`) — clipboard integration
  - `hyprctl` (Hyprland) or `niri` (Niri) — window capture
- Dev dependencies (extra `dev`): `pytest`, `pytest-qt`

## Project Structure

```
captua/
  __init__.py       # Package meta (__version__)
  main.py           # Entry point: QApplication setup, CLI arg parsing, capture mode dispatch,
                    # screen selection, async update check (3 s delayed)
  capture.py        # Screenshot capture via grim/slurp/hyprctl/niri (subprocess)
  overlay.py        # Frameless OverlayWindow (QMainWindow): toolbar + canvas wiring,
                    # fixed window sizing (compute_window_size), render/export,
                    # clipboard (also shells out to wl-copy), background auto-save on copy
  canvas.py         # CanvasScene (QGraphicsScene) + CanvasView (QGraphicsView): zoom/pan,
                    # resize handles, tool routing, shortcuts, magnetic snap (snap_rect/snap_point),
                    # backdrop draw helper, `?` shortcut overlay
  toolbar.py        # Four floating pill toolbars (corners): close (top-left),
                    # actions Backdrop/Snap/Import/Capture/Save/Copy (top-right),
                    # tool buttons + sticky pin (bottom-left), contextual
                    # stroke/fill properties (bottom-right)
  theme.py          # Central palette + stylesheet builders (single accent, pill styles)
  icons.py          # Programmatically-drawn monochrome 20×20 toolbar icons via QPainter
  tools.py          # Annotation tool classes (SelectTool, CropTool, RectangleTool, EllipseTool,
                    # LineTool, ArrowTool, PenTool, MarkerTool, TextTool, CounterTool, ShapeTool,
                    # EmojiTool, LabelTool, RulerTool, SpotlightTool, BlurTool, MagnifierTool,
                    # EyedropperTool) + ToolProperties
  items.py          # QGraphicsItem subclasses for all annotations, CanvasImageItem,
                    # CropOverlayItem, EyedropperItem
  history.py        # Undo/redo command stack (Command, AddItemCommand, RemoveItemCommand, History)
  settings.py       # JSON persistence to ~/.config/captua/settings.json (atomic write via tmp file)
  backdrop.py       # BackdropPopup (live-preview backdrop settings) + _AngleDial widget
  colorwheel.py     # Color picker dialog (ColorWheelDialog)
  popups.py         # ShapePopup, EmojiPopup, MagnifierPopup selector popups
  shapes.py         # Pre-defined shape paths + ShapePickerDialog
  emojipicker.py    # Emoji data/model + EmojiPickerDialog
  updater.py        # Async GitHub release checker (UpdateChecker, QNetworkAccessManager)
  update_dialog.py  # Non-blocking update-available dialog; triggers SelfUpdater
  self_updater.py   # pip install --upgrade from GitHub release tarball via QProcess, then os.execl restart
tests/              # pytest suite (see Testing)
scripts/
  install.sh        # End-user installer (distro detection, venv at ~/.local/share/captua, .desktop entry)
  debug.sh          # Dev wrapper: runs `python3 -m captua.main` with repo on PYTHONPATH, logs to /tmp/captua.log
docs/GUIDE.md       # User-facing feature documentation
docs/superpowers/   # Plans/notes for AI-assisted development
.github/workflows/release.yml  # Tag-triggered release packaging
pyproject.toml      # Project config, dependencies, pytest config
run.sh              # NOTE: currently a hardcoded launcher for one user's installed venv
                    # (~/.local/share/captua/venv/bin/captua); it does NOT run from the repo.
                    # For development use scripts/debug.sh or `python3 -m captua.main`.
```

## Architecture

- `main.py` boots the `QApplication` (app name/desktop file: `captua-overlay`), picks the capture mode from CLI args, captures via `capture.py`, creates the `OverlayWindow`, and starts a delayed (3 s) non-blocking update check.
- `OverlayWindow` (overlay.py) owns a `CanvasView` (canvas.py), which owns a `CanvasScene`.
- `CanvasScene` holds layers: base image (z=0), additional images (z=0), annotations (z>0).
- `CanvasView.drawBackground()` paints the checkerboard + backdrop (not scene items); `drawForeground()` paints resize handles for selected rect items.
- Subprocess usage: `capture.py` shells out to grim/slurp/hyprctl/niri; `overlay.py` shells out to `wl-copy` for clipboard; `self_updater.py` runs `pip` via `QProcess`.
- `settings.py` persists backdrop preferences, default tool properties, snap toggle, sticky-tools toggle, auto-save, screenshots folder/filename template, and update-check settings to `~/.config/captua/settings.json` (defaults merged on load, atomic save). `OverlayWindow.closeEvent()` merges current values over the loaded settings so unrelated keys survive.
- Tools in `tools.py` each receive `(scene, props, history)` and implement mouse press/move/release; completed edits are pushed onto the `History` command stack for undo/redo.

## Key Behaviours

- **Backdrop in exports**: `OverlayWindow.render_to_pixmap()` computes `itemsBoundingRect()`, draws the backdrop, then renders scene items on top. The checkerboard is drawn in `drawBackground()` but intentionally skipped in exports.
- **Window sizing**: `compute_window_size()` (overlay.py) sizes the window to content + 50px margin + pill zones (top and bottom), capped at the available screen space (`availableGeometry()` minus 40px). Minimum width = `Toolbar.full_width()` — enough for both pill rows (close+actions, tools+props) side by side, refreshed in `showEvent` via `refresh_full_width()` because pre-show size hints are unreliable. `_on_scene_rect_fitted()` grows the window (never shrinks) when content extends past the image edge. After `showEvent`, the size is re-asserted twice via `QTimer` (`_reassert_size`) because compositors may impose a default height on new floating windows (e.g. a global niri `default-window-height` rule).
- **Floating pills**: the four toolbar pills are direct children of `OverlayWindow` (not in the layout), positioned to the corners by `_place_pills()` (window `resizeEvent` + `pills_changed` signal). The canvas fills the whole window; `_fit_image()` centers content between the equal top/bottom pill zones. Plain QWidgets need `WA_StyledBackground` for the pill stylesheet background to paint.
- **Single instance**: `ensure_single_instance()` (main.py) runs at startup (after `--help` handling). It reads `$XDG_RUNTIME_DIR/captua-overlay-<uid>.pid`, verifies the recorded PID is a live captua process (`/proc/<pid>/cmdline` guard against PID recycling), sends SIGTERM with a 2s grace period, then writes its own PID (removed via `atexit`).
- **Auto-switch to select**: `CanvasView` emits `tool_finished` after non-select tools complete; `OverlayWindow` switches back to select mode unless **sticky tools** are enabled (pin toggle in the toolbar, persisted as `sticky_tools`).
- **Auto-save on copy**: when `auto_save_on_copy` is true (default), `Ctrl+C` / Copy renders once, sets the `QClipboard` image synchronously, then encodes PNG once in a background thread that also writes `<screenshots_folder>/<template>.png` (default `~/Pictures/Screenshots/captua-{timestamp}.png`) and feeds `wl-copy`. The thread reports back via the `copy_finished` signal; the window closes immediately on success (no artificial delay) or stays open with an error dialog on save failure.
- **Esc hierarchy**: `Esc` clears text focus → closes the shortcut overlay → clears the selection → and only then closes the window.
- **Contextual properties**: the toolbar properties panel (colour, width, fill alpha) is only visible when a drawing tool is active or a single item is selected.
- **Keyboard shortcut overlay**: `?` toggles a help overlay listing all shortcuts; `Esc` or `?` dismisses it.
- **Auto-updater**: 3 s after startup the app queries the GitHub releases API. If a newer, non-skipped version exists, a non-modal dialog offers **Update Now** (self-update, see below), **Ask Again Later**, or **Skip This Version** (persisted as `skipped_version`).
- **Self-update**: `SelfUpdater` runs `pip install --upgrade <github release tarball URL>` via `QProcess` (with a `--user` fallback on permission errors), then restarts with `os.execl` after chdir-ing to a temp dir so a git clone's source folder cannot shadow the installed package. (It no longer uses `git pull`.)
- **Magnetic snap**: toolbar toggle (`snap_enabled` setting). `snap_rect()` aligns edges/centerlines of a moving item to all other items (15 px tolerance); drawing tools call `snap_point()` unless Shift is held.
- **Shift constraints while drawing**: Rectangle→square, Ellipse→circle, Line/Arrow→45° snap, Pen→Bezier smoothing, Marker→straight line, Spotlight/Blur→square.
- **Eyedropper**: `D` shortcut. A viewport QLabel overlay (not a scene item) shows live HEX+RGB under the cursor; click copies HEX to the clipboard. Stays active until another tool is chosen.
- **Spotlight resize**: `SpotlightItem` exposes `rect()`/`setRect()` so the `CanvasView` resize handles work on the inner transparent rectangle.
- **Window capture**: works on Hyprland (`hyprctl activewindow -j` + `grim -g`) and Niri (`niri msg action screenshot-window`, then loads the newest file from `~/Pictures/Screenshots`); Niri is detected via `XDG_CURRENT_DESKTOP=niri`.

## Build and Run

```bash
# Development install
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run from the repo (no install needed)
python3 -m captua.main [--screen | -s | --window | -w]

# Debug run with logging to /tmp/captua.log (sets QT_QPA_PLATFORM=wayland)
./scripts/debug.sh [--screen | --window]
```

The repo contains two venv directories: `.venv/` was created on macOS (Homebrew Python 3.12, broken on this machine) and `venv/` targets `/usr/bin/python3.14`. Prefer creating your own `.venv` per the README. `run.sh` is a user-specific launcher, not a dev entry point (see Project Structure note).

## Testing

- Framework: pytest + pytest-qt (`pyproject.toml`: `testpaths = ["tests"]`, `qt_api = "pyside6"`).
- `tests/conftest.py` provides a session-scoped `QApplication` fixture (`qapp`); widget-related tests should use it (pytest-qt's `qapp`/`qtbot` also work).
- Capture tests mock `subprocess.run`; settings tests monkeypatch `captua.settings.CONFIG_DIR`/`CONFIG_FILE` to a `tmp_path` — never touch the real `~/.config/captua` in tests.

```bash
# Headless environments need the offscreen platform
QT_QPA_PLATFORM=offscreen pytest            # all tests
QT_QPA_PLATFORM=offscreen pytest tests/test_history.py -v
```

Known caveat: the two `TestCaptureWindow` tests in `tests/test_capture.py` assume the Hyprland code path and fail on a Niri session (`XDG_CURRENT_DESKTOP=niri` routes `capture_window()` to the Niri path). This is a pre-existing, environment-dependent failure — as of writing, the suite is 25 passed / 2 failed on a Niri desktop, 27 passed elsewhere.

No linter config. Type-check with `mypy captua/`.

## Coding Style

- Type hints throughout.
- Explicit imports, no wildcard imports.
- Qt enums referenced fully (e.g., `Qt.AspectRatioMode.KeepAspectRatio`).
- Comments and documentation are in English.
- Make minimal, scoped changes; match the surrounding file's naming and structure.

## Release / Deployment

- Releases are cut by pushing a `v*` tag. `.github/workflows/release.yml` packages a source tarball (`git archive`) plus `scripts/install.sh` and uploads them to a GitHub release with auto-generated notes.
- End users install via `scripts/install.sh` (detects distro, installs grim/slurp/wl-clipboard, creates a venv at `~/.local/share/captua`, drops a launcher in `~/.local/bin` and a `.desktop` entry).
- The in-app self-updater downloads the release source tarball, so every release must remain pip-installable from the tag tarball (`pip install https://github.com/KernicDE/captua/archive/refs/tags/v<X>.tar.gz`).
- When bumping the version, update both `pyproject.toml` (`project.version`) and `captua/__init__.py` (`__version__`); the updater compares against `__version__`.

## Security Considerations

- The app executes external binaries (`grim`, `slurp`, `hyprctl`, `niri`, `wl-copy`, `pip`). Commands are built as argument lists (no shell string interpolation); keep it that way — never pass user input through a shell.
- Subprocess calls use timeouts; raise `RuntimeError` (not raw `CalledProcessError`/`JSONDecodeError`) on failure so `main.py` can report cleanly.
- Window capture on Hyprland uses a temporary PNG file that is deleted in a `finally` block; blur/magnifier pipelines process images in memory (`QBuffer`/`BytesIO`) rather than via temp files.
- `settings.py` writes atomically (tmp file + `replace`) and merges loaded data over defaults so corrupt JSON falls back to defaults instead of crashing.
- The self-updater pipes `pip` output to the dialog and restarts via `os.execl`; it only installs from the project's own GitHub release tarballs.
- Screenshots may contain sensitive content; auto-save writes to the user's configured screenshots folder, and nothing is sent over the network except the GitHub release check (opt-out via `update_check_enabled`).
