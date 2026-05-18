"""Persistent JSON settings for Captua."""

import json
from pathlib import Path

from PySide6.QtGui import QColor

CONFIG_DIR = Path.home() / ".config" / "captua"
CONFIG_FILE = CONFIG_DIR / "settings.json"


def _default_settings() -> dict:
    return {
        "backdrop_padding": 25,
        "backdrop_color": "#2A2A37",
        "backdrop_use_gradient": False,
        "backdrop_gradient_start": "#2A2A37",
        "backdrop_gradient_end": "#1F1F28",
        "backdrop_corner_radius": 0,
        "canvas_corner_radius": 0,
        "line_color": "#FF5D62",
        "line_width": 3,
        "fill_color": "#FF5D62",
        "fill_alpha": 128,
        "auto_save_on_copy": True,
        "update_check_enabled": True,
        "skipped_version": "",
        "screenshots_folder": "~/Pictures/Screenshots",
        "screenshot_filename_template": "captua-{timestamp}.png",
    }


def load_settings() -> dict:
    """Load settings from disk, returning defaults for missing keys."""
    defaults = _default_settings()
    if not CONFIG_FILE.exists():
        return defaults
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return defaults

    # Merge with defaults so new keys are always present
    merged = {**defaults, **data}
    return merged


def save_settings(data: dict) -> None:
    """Write settings to disk atomically, creating directories if necessary."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp_file = CONFIG_DIR / ".settings.tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    tmp_file.replace(CONFIG_FILE)


def apply_to_scene(scene, settings: dict) -> None:
    """Apply loaded settings to a CanvasScene."""
    scene.backdrop_padding = settings.get("backdrop_padding", 20)
    scene.backdrop_color = QColor(settings.get("backdrop_color", "#2A2A37"))
    scene.backdrop_use_gradient = settings.get("backdrop_use_gradient", False)
    scene.backdrop_gradient_start = QColor(settings.get("backdrop_gradient_start", "#2A2A37"))
    scene.backdrop_gradient_end = QColor(settings.get("backdrop_gradient_end", "#1F1F28"))
    scene.backdrop_corner_radius = settings.get("backdrop_corner_radius", 0)
    scene.canvas_corner_radius = settings.get("canvas_corner_radius", 0)


def extract_from_scene(scene) -> dict:
    """Extract current backdrop settings from a CanvasScene."""
    return {
        "backdrop_padding": scene.backdrop_padding,
        "backdrop_color": scene.backdrop_color.name(),
        "backdrop_use_gradient": scene.backdrop_use_gradient,
        "backdrop_gradient_start": scene.backdrop_gradient_start.name(),
        "backdrop_gradient_end": scene.backdrop_gradient_end.name(),
        "backdrop_corner_radius": scene.backdrop_corner_radius,
        "canvas_corner_radius": scene.canvas_corner_radius,
    }
