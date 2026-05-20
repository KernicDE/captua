# Captua User Guide

Captua is a fast, lightweight screenshot annotation tool for Linux / Wayland built with Qt6.

## Installation

Requires **Python 3.11+**, **PySide6**, **grim**, **slurp**, and **wl-clipboard**.

```bash
# Dependencies (Arch example)
pacman -S python python-pyside6 grim slurp wl-clipboard

# Run
./run.sh
```

## Capture Modes

| Mode | Command | Description |
|---|---|---|
| Region | `captua` (default) | Select a rectangle with slurp |
| Screen | `captua --screen` / `-s` | Capture the full active screen |
| Window | `captua --window` / `-w` | Capture the active Hyprland window |

## Toolbar

The top bar contains (left to right):

- **✕** — Close the overlay (`Esc`)
- **💾** — Save to file (`Ctrl+S`)
- **📋** — Copy to clipboard (`Ctrl+C`)
- **➕** — Import an image from disk
- **📷** — Capture a new region and add it to the canvas
- **⚙** — Backdrop settings (padding, color, corner radius)
- **Line color / width** — Stroke appearance for shapes, lines, arrows, etc.
- **Fill color / opacity** — Fill appearance for closed shapes
- **Tool buttons** — See table below

## Tools

| Tool | Shortcut | Description |
|---|---|---|
| 🖱 Mouse | `V` | Select, move, and resize items |
| ▭ Square | `R` | Rectangle with optional fill |
| ○ Circle | `O` | Ellipse with optional fill |
| ╱ Line | `L` | Straight line |
| ➜ Arrow | `A` | Arrow with adjustable stroke |
| ✎ Pen | `P` | Freehand drawing |
| 🖍 Marker | `M` | Thick highlighter stroke |
| ⬟ Forms | `S` | Shapes (heart, star, etc.) |
| 😀 Emojis | `E` | Emoji picker |
| T Text | `T` | Click to place editable text |
| 🏷 Label | `K` | Callout label with a leader line |
| ① Numbering | `N` | Auto-incrementing counter badges |
| 📏 Ruler | `U` | Measurement line with distance label |
| 🔦 Highlight | `I` | Spotlight / dim overlay |
| 🌫 Blur | `B` | Blur region (privacy) |
| 🔍 Magnifier | `G` | Loupe that zooms part of the image |
| 🧪 Picker | `D` | Eyedropper — live colour read-out, click to copy HEX |

### Selection Editing

When a single item is selected, the toolbar shows that item's properties. Changing a property updates the selected item in real time.

- **Line color** — Stroke / border color
- **Line width** — Stroke thickness (1–20 px)
- **Fill color** — Interior color
- **Fill opacity** — 0% (transparent) to 100% (solid)

### Resize Handles

In Mouse mode, blue corner handles appear on rectangle-based items. Drag a handle to resize.

Spotlight / Highlight can also be resized — drag the inner transparent rectangle to move it, or drag the corner handles to resize it.

### Magnetic Snap

When **Snap** is enabled in the toolbar, edges and centerlines of items automatically align to each other while drawing and moving. The snapping distance is ~15 px.

### Shift Constraints

Hold **Shift** while drawing to constrain the shape:

| Tool | Constraint |
|---|---|
| Rectangle | Square |
| Ellipse | Circle |
| Line / Arrow | 45° angles |
| Pen | Smooth Bezier curves |
| Marker | Straight line |
| Spotlight / Blur | Square |

## Layer Ordering

Select an item and press:

- **PgUp** — Bring forward
- **PgDn** — Send backward

## Importing Images

Three ways to add images to the canvas:

1. **Toolbar ➕** — Open a file dialog
2. **Drag & drop** — Drop an image file onto the canvas
3. **Ctrl+V** — Paste from clipboard

Images are selectable and movable once placed.

## Backdrop Settings

Click **⚙** to configure the background behind your screenshots:

- **Backdrop padding** — Space between images and backdrop edge
- **Backdrop color** — Solid fill color
- **Use gradient** — Diagonal gradient between two colors
- **Canvas rounding** — Corner radius for screenshot images
- **Backdrop rounding** — Corner radius for the backdrop rectangle

Changes are previewed live. Settings persist between sessions.

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Esc` | Close overlay (or clear text focus) |
| `Ctrl+S` | Save to file |
| `Ctrl+C` | Copy to clipboard |
| `Ctrl+V` | Paste image from clipboard |
| `Ctrl+Z` | Undo |
| `Ctrl+Shift+Z` | Redo |
| `Ctrl+Y` | Redo |
| `Delete` / `Backspace` | Remove selected items |
| `PgUp` / `PgDn` | Change layer order |
| `?` | Toggle keyboard-shortcut overlay |
| `Middle-drag` | Pan the canvas |
| `Ctrl+Scroll` | Zoom in / out |

## Tips

- After drawing most annotations, the tool automatically switches back to **Mouse** mode so you can reposition it immediately.
- The **Picker** (`D`) stays active after a click so you can sample multiple colours; switch to another tool when done.
- The canvas auto-expands when you drag items beyond the current boundary; the window grows to match.
- Use **Undo** liberally — the full history is kept in memory for the session.
- The checkerboard pattern behind the canvas is only visible in the editor; it is **not** included in saved or copied images.
- Captua checks for updates on startup. If a newer version is available you can update with one click (when running from a git clone) or open the release page in your browser.
