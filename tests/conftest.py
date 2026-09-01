import sys
import os

# Ensure project root directory is in sys.path for pytest module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
