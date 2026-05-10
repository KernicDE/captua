# Captua

> **Vibe-coded with AI.** This project was built almost entirely through conversations with LLMs — it is experimental, opinionated, and may contain rough edges. Contributions and bug reports are welcome!

A fast, lightweight screenshot annotation tool for **Linux / Wayland**.

> ⚠️ **Wayland only** — Captua relies on `grim`, `slurp`, and `wl-clipboard`, which are Wayland-native tools. It will **not** work on X11.

## Features

- **Region capture** via `grim` + `slurp`
- **Full-screen capture** via `grim`
- **Window capture** via `grim` + `hyprctl` (Hyprland)
- **Frameless overlay** with `QGraphicsScene` canvas
- **Zoom** (`Ctrl` + scroll) and **pan** (middle-click drag)
- **Annotations** — rectangles, circles, arrows, pen, marker, text, labels, emojis, shapes, blur, magnifier, ruler, spotlight, numbering
- **Clipboard** (`Ctrl+C`) and **save** (`Ctrl+S`) support
- **Undo / redo**, layer ordering, drag & drop, paste from clipboard
- **Backdrop settings** — padding, colors, gradients, corner radius

## Install

### AppImage (recommended)

Download the latest `Captua-x86_64.AppImage` from the [Releases](https://github.com/KernicDE/captua/releases) page, make it executable, and run:

```bash
chmod +x Captua-x86_64.AppImage
./Captua-x86_64.AppImage
```

> System dependencies `grim`, `slurp`, and `wl-clipboard` must still be installed on your system (see below).

### From source

```bash
pip install -e .
```

### System dependencies

| Distro | Command |
|--------|---------|
| Arch | `pacman -S grim slurp wl-clipboard` |
| Fedora | `dnf install grim slurp wl-clipboard` |
| openSUSE | `zypper install grim slurp wl-clipboard` |

## Hyprland Setup

Add these window rules to `~/.config/hypr/hyprland.conf`:

```ini
windowrulev2 = float, class:(captua-overlay)
windowrulev2 = center, class:(captua-overlay)
windowrulev2 = size 80%, class:(captua-overlay)
windowrulev2 = noanim, class:(captua-overlay)
```

## Usage

```bash
# Capture a region (default)
captua

# Capture full screen
captua --screen

# Capture active window (Hyprland)
captua --window
```

## Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl + C` | Copy image to clipboard |
| `Ctrl + S` | Save image to disk |
| `Ctrl + V` | Paste image from clipboard |
| `Ctrl + Z` | Undo |
| `Ctrl + Shift + Z` / `Ctrl + Y` | Redo |
| `Ctrl + Wheel` | Zoom |
| `Middle-click drag` | Pan |
| `Delete` / `Backspace` | Remove selected items |
| `PgUp` / `PgDn` | Change layer order |
| `Escape` | Close |

See [`docs/GUIDE.md`](docs/GUIDE.md) for the full user guide.

## Tech Stack

- Python 3.12+
- PySide6 (Qt6)
- grim, slurp, wl-clipboard (system deps)

## License

MIT
