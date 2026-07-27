"""Tests for the single-instance enforcement in main.py."""

import os
import subprocess
import time

import pytest

import captua.main as main_module


@pytest.fixture()
def pid_file(tmp_path, monkeypatch):
    path = tmp_path / "captua.pid"
    monkeypatch.setattr(main_module, "_pid_file", lambda: path)
    return path


class TestEnsureSingleInstance:
    def test_writes_own_pid(self, pid_file) -> None:
        main_module.ensure_single_instance()
        assert int(pid_file.read_text().strip()) == os.getpid()

    def test_terminates_previous_instance(self, pid_file, monkeypatch) -> None:
        proc = subprocess.Popen(["sleep", "30"])
        pid_file.write_text(str(proc.pid))
        monkeypatch.setattr(main_module, "_is_captua_process", lambda pid: True)

        main_module.ensure_single_instance()

        proc.wait(timeout=5)
        assert proc.poll() is not None  # terminated
        assert int(pid_file.read_text().strip()) == os.getpid()

    def test_stale_pid_file_is_ignored(self, pid_file, monkeypatch) -> None:
        # PID that (almost certainly) does not exist
        pid_file.write_text("4194303")
        monkeypatch.setattr(main_module, "_is_captua_process", lambda pid: False)
        main_module.ensure_single_instance()  # must not raise
        assert int(pid_file.read_text().strip()) == os.getpid()

    def test_unrelated_process_is_not_killed(self, pid_file, monkeypatch) -> None:
        proc = subprocess.Popen(["sleep", "30"])
        try:
            pid_file.write_text(str(proc.pid))
            # cmdline guard says: not a captua process
            monkeypatch.setattr(main_module, "_is_captua_process", lambda pid: False)
            main_module.ensure_single_instance()
            assert proc.poll() is None  # still running
        finally:
            proc.terminate()
            proc.wait(timeout=5)
