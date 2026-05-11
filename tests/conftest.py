"""Shared pytest fixtures."""
import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Single QApplication for the test session."""
    app = QApplication.instance() or QApplication([])
    yield app
