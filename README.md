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
- **Annotations** — rectangles, circles, arrows, pen, marker, text, labels, emojis, shapes, blur, magnifier, ruler, spotlight, numbering, eyedropper
- **Clipboard** (`Ctrl+C`) and **save** (`Ctrl+S`) support
- **Undo / redo**, layer ordering, drag & drop, paste from clipboard
- **Magnetic snap** — edges and centerlines align automatically while drawing and moving
- **Shift constraints** — hold Shift to force squares, circles, 45° lines, straight strokes
- **Backdrop settings** — padding, colors, gradients, corner radius, angle dial
- **Auto-updater** — checks for new releases on startup and self-updates from git

## Install

### Quick install (recommended)

Download and run the installer from the latest release:

```bash
curl -fsSL https://github.com/KernicDE/captua/releases/latest/download/install.sh -o install-captua.sh
chmod +x install-captua.sh
./install-captua.sh
```

The installer will:
1. Detect your distro and install `grim`, `slurp`, and `wl-clipboard`
2. Create a Python virtual environment at `~/.local/share/captua/venv`
3. Install Captua and its Python dependencies
4. Place a `captua` launcher in `~/.local/bin/`
5. Install a `.desktop` entry

> Make sure `~/.local/bin` is in your `PATH`.

### From source (for development)

```bash
# Clone
git clone https://github.com/KernicDE/captua.git
cd captua

# Create a venv and install
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Or run directly without installing
./run.sh
```

### System dependencies

If you prefer to install manually, you need:

| Package | Purpose |
|---------|---------|
| `grim` | Screenshot capture |
| `slurp` | Region selection |
| `wl-clipboard` | Clipboard integration |

| Distro | Command |
|--------|---------|
| Arch | `pacman -S grim slurp wl-clipboard` |
| Fedora | `dnf install grim slurp wl-clipboard` |
| openSUSE | `zypper install grim slurp wl-clipboard` |
| Debian / Ubuntu | `apt-get install grim slurp wl-clipboard` |

## Window Manager / Desktop Environment Setup

Captua requests a frameless, always-on-top window. Depending on your compositor you may want to add rules so the overlay floats and is centered.

### Hyprland

Add these window rules to `~/.config/hypr/hyprland.conf`:

```ini
windowrulev2 = float, class:(captua-overlay)
windowrulev2 = center, class:(captua-overlay)
windowrulev2 = size 80%, class:(captua-overlay)
windowrulev2 = noanim, class:(captua-overlay)
```

### KDE Plasma (KWin)

Create a window rule in *System Settings → Window Management → Window Rules → New*:

| Property | Value |
|---|---|
| Window class | `captua-overlay` |
| Window types | Normal window |
| **Position** | Centered |
| **Size** | 80% of screen |
| **Window matching** | Exact match |
| **Keep above** | Force → Yes |
| **No border** | Force → Yes |
| **Fullscreen** | Force → No |

Or add the rule directly to `~/.config/kwinrulesrc`:

```ini
[captua-overlay]
description=Captua Overlay
clientmachine=localhost
wmclass=captua-overlay
wmclassmatch=1
position=3
size=80
above=true
aboverule=3
noborder=true
noborderrule=3
fullscreenrule=2
```

### GNOME (Mutter)

GNOME does not have built-in per-window rules. Captua already requests a frameless, always-on-top window, so it should work out of the box as a regular window.

If you use a tiling extension (e.g. **Pop Shell**, **Forge**, or **Tiling Assistant**), add `captua-overlay` to the floating-windows exception list so it is not tiled.

### Sway

Add to `~/.config/sway/config`:

```
for_window [app_id="captua-overlay"] floating enable, move position center, resize set 80 ppt 80 ppt, border none
```

## Set Captua as your default screenshot tool

### Hyprland

Add key bindings to `~/.config/hypr/hyprland.conf`:

```ini
# Region capture
bind = , Print, exec, captua
# Full screen
bind = SHIFT, Print, exec, captua --screen
# Active window
bind = ALT, Print, exec, captua --window
```

### KDE Plasma

1. Open *System Settings → Shortcuts → Custom Shortcuts*
2. Create three new **Global Shortcuts → Command/URL** items:

| Trigger | Command | Shortcut |
|---|---|---|
| Captua Region | `captua` | `Print` |
| Captua Screen | `captua --screen` | `Shift+Print` |
| Captua Window | `captua --window` | `Meta+Print` |

3. Disable or rebind Spectacle's shortcuts so they don't conflict.

### GNOME

1. Open *Settings → Keyboard → Keyboard Shortcuts → Custom Shortcuts*
2. Add three shortcuts:

| Name | Command | Shortcut |
|---|---|---|
| Captua Region | `captua` | `Print` |
| Captua Screen | `captua --screen` | `Shift+Print` |
| Captua Window | `captua --window` | `Alt+Print` |

GNOME's default screenshot shortcuts will conflict — remove or rebind them in the same settings panel.

### Sway

Add to `~/.config/sway/config`:

```
# Region capture
bindsym Print exec captua
# Full screen
bindsym Shift+Print exec captua --screen
# Active window
bindsym $mod+Print exec captua --window
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
| `?` | Toggle keyboard-shortcut overlay |
| `Ctrl + Wheel` | Zoom |
| `Middle-click drag` | Pan |
| `Delete` / `Backspace` | Remove selected items |
| `PgUp` / `PgDn` | Change layer order |
| `Escape` | Close |

See [`docs/GUIDE.md`](docs/GUIDE.md) for the full user guide.

## Tech Stack

- Python 3.11+
- PySide6 (Qt6)
- grim, slurp, wl-clipboard (system deps)

## License

MIT
