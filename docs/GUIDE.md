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

The floating pill bar at the top contains:

- **Top row:** Close (`Esc`) on the left; Backdrop settings, Snap toggle, an overflow menu (⋯: Import image, Capture region), **Save** (`Ctrl+S`) and the primary **Copy** button (`Ctrl+C`) on the right
- **Bottom row:** the tool buttons (see table below), a **pin toggle** to keep the active tool after drawing, and the contextual property controls
- **Line color / width** — Stroke appearance for shapes, lines, arrows, etc.
- **Fill color / opacity** — Fill appearance for closed shapes

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
| `Esc` | Clear text focus → clear selection → close overlay |
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

- After drawing most annotations, the tool automatically switches back to **Mouse** mode so you can reposition it immediately. Toggle the **pin** button next to the tools to keep the active tool instead (persists between sessions).
- The **Picker** (`D`) stays active after a click so you can sample multiple colours; switch to another tool when done.
- The window has a fixed size — the captured content plus a 50 px margin, capped at the available screen space. Content drawn beyond the image edge stays reachable via pan and zoom.
- Copying is instant: the window closes right away while the image is encoded, saved and handed to the clipboard in the background.
- Use **Undo** liberally — the full history is kept in memory for the session.
- The checkerboard pattern behind the canvas is only visible in the editor; it is **not** included in saved or copied images.
- Captua checks for updates on startup. If a newer version is available you can update with one click (when running from a git clone) or open the release page in your browser.
