"""Tests for capture.py subprocess wrappers."""
import json
import subprocess
from unittest.mock import patch

import pytest


def _make_completed(stdout: str, returncode: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr="")


class TestCaptureWindow:
    def test_invalid_json_raises_runtime_error(self):
        """hyprctl returning invalid JSON must raise RuntimeError, not JSONDecodeError."""
        bad_output = _make_completed("not valid json")

        with patch("subprocess.run", return_value=bad_output):
            from captua.capture import capture_window

            with pytest.raises(RuntimeError, match="invalid JSON"):
                capture_window()

    def test_empty_window_raises_runtime_error(self):
        """hyprctl returning a window with size [0,0] must raise RuntimeError."""
        data = {"at": [0, 0], "size": [0, 0], "scale": 1.0}
        good_output = _make_completed(json.dumps(data))

        with patch("subprocess.run", return_value=good_output):
            from captua.capture import capture_window

            with pytest.raises(RuntimeError, match="No active window"):
                capture_window()

    def test_timeout_raises_runtime_error(self):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="hyprctl", timeout=15)):
            from captua.capture import capture_window

            with pytest.raises(RuntimeError, match="timed out"):
                capture_window()


class TestRun:
    def test_nonzero_returncode_raises(self):
        failed = _make_completed("", returncode=1)
        failed.stderr = "something went wrong"

        with patch("subprocess.run", return_value=failed):
            from captua.capture import _run

            with pytest.raises(RuntimeError, match="Command failed"):
                _run(["fake-cmd"])

    def test_timeout_raises(self):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="fake", timeout=15)):
            from captua.capture import _run

            with pytest.raises(RuntimeError, match="timed out"):
                _run(["fake-cmd"])
