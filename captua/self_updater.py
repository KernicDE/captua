"""Self-update logic: pip install from GitHub release tarball, then restart."""

from __future__ import annotations

import os
import sys
import tempfile

from PySide6.QtCore import QObject, QProcess, Signal


class SelfUpdater(QObject):
    """Async self-updater using pip + GitHub release tarball."""

    progress = Signal(str)  # human-readable status line
    finished = Signal(bool, str)  # success, message

    def __init__(self, target_version: str, parent=None) -> None:
        super().__init__(parent)
        self._version = target_version
        self._proc: QProcess | None = None

    def start(self) -> None:
        """Begin the update sequence."""
        url = f"https://github.com/KernicDE/captua/archive/refs/tags/v{self._version}.tar.gz"
        self._run_pip(["install", "--upgrade", url])

    def _run_pip(self, args: list[str]) -> None:
        self.progress.emit("Downloading and installing update…")
        self._proc = QProcess(self)
        self._proc.finished.connect(self._on_pip_finished)
        self._proc.start(sys.executable, ["-m", "pip", *args])

    def _on_pip_finished(self, exit_code: int, _exit_status) -> None:
        if exit_code != 0:
            out = self._proc.readAllStandardError().data().decode("utf-8", "replace").strip()
            # If the error looks like a permission issue, try --user as a fallback
            if "Permission denied" in out or "permission denied" in out.lower():
                self._try_user_install()
                return
            self.finished.emit(
                False,
                f"Update failed.\n{out or 'pip exited with an error.'}",
            )
            return
        self.progress.emit("Update complete.")
        self.finished.emit(True, "Captua has been updated and will now restart.")

    def _try_user_install(self) -> None:
        """Retry with --user when a system-wide install lacks permissions."""
        self.progress.emit("Retrying with user install…")
        url = f"https://github.com/KernicDE/captua/archive/refs/tags/v{self._version}.tar.gz"
        self._proc = QProcess(self)
        self._proc.finished.connect(self._on_user_pip_finished)
        self._proc.start(sys.executable, ["-m", "pip", "install", "--upgrade", "--user", url])

    def _on_user_pip_finished(self, exit_code: int, _exit_status) -> None:
        if exit_code != 0:
            out = self._proc.readAllStandardError().data().decode("utf-8", "replace").strip()
            self.finished.emit(
                False,
                f"Update failed (even with --user).\n{out or 'pip exited with an error.'}",
            )
            return
        self.progress.emit("Update complete.")
        self.finished.emit(True, "Captua has been updated and will now restart.")

    @staticmethod
    def restart() -> None:
        """Replace the current process with a fresh instance of Captua.

        We chdir to a temp directory first so that the old source folder
        (if the user is running from a git clone) does not shadow the
        newly installed package on PYTHONPATH.
        """
        os.chdir(tempfile.gettempdir())
        os.execl(sys.executable, sys.executable, "-m", "captua", *sys.argv[1:])
