"""Self-update logic: git pull + reinstall, then restart."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, Signal


def _project_root() -> Path | None:
    """Return the project root if it looks like a git clone."""
    root = Path(__file__).resolve().parent.parent
    if (root / ".git").is_dir():
        return root
    return None


def _can_self_update() -> bool:
    """Return True if we are running from a git clone."""
    return _project_root() is not None


class SelfUpdater(QObject):
    """Async self-updater using QProcess (git pull + pip install -e .)."""

    progress = Signal(str)  # human-readable status line
    finished = Signal(bool, str)  # success, message

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._root = _project_root()
        self._proc: QProcess | None = None
        self._success_so_far = True
        self._pending_msg = ""

    def start(self) -> None:
        """Begin the update sequence."""
        if self._root is None:
            self.finished.emit(False, "Cannot self-update: not a git clone.")
            return
        self._run_git_pull()

    def _run_git_pull(self) -> None:
        self.progress.emit("Pulling latest changes…")
        self._proc = QProcess(self)
        self._proc.setWorkingDirectory(str(self._root))
        self._proc.finished.connect(self._on_git_finished)
        self._proc.start("git", ["pull", "origin", "main"])

    def _on_git_finished(self, exit_code: int, _exit_status) -> None:
        if exit_code != 0:
            out = self._proc.readAllStandardError().data().decode("utf-8", "replace").strip()
            self.finished.emit(False, f"git pull failed:\n{out or 'unknown error'}")
            return
        self._run_pip_install()

    def _run_pip_install(self) -> None:
        self.progress.emit("Re-installing…")
        self._proc = QProcess(self)
        self._proc.setWorkingDirectory(str(self._root))
        self._proc.finished.connect(self._on_pip_finished)
        # Use the same Python interpreter that's running Captua
        self._proc.start(sys.executable, ["-m", "pip", "install", "-e", "."])

    def _on_pip_finished(self, exit_code: int, _exit_status) -> None:
        if exit_code != 0:
            out = self._proc.readAllStandardError().data().decode("utf-8", "replace").strip()
            self.finished.emit(False, f"pip install failed:\n{out or 'unknown error'}")
            return
        self.progress.emit("Update complete.")
        self.finished.emit(True, "Captua has been updated and will now restart.")

    @staticmethod
    def restart() -> None:
        """Replace the current process with a fresh instance of Captua."""
        # os.execl replaces the current process — cleanest restart possible.
        os.execl(sys.executable, sys.executable, "-m", "captua", *sys.argv[1:])
