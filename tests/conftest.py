import sys
import os
import pytest

# Ensure project root directory is in sys.path for pytest module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set offscreen QPA for headless test execution
os.environ["QT_QPA_PLATFORM"] = "offscreen"

@pytest.fixture(scope="session", autouse=True)
def qapp():
    from PySide6.QtGui import QGuiApplication
    app = QGuiApplication.instance()
    if app is None:
        app = QGuiApplication(sys.argv[:1])
    return app

