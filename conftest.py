"""Root conftest.py — adds src/ to sys.path so that internal app imports work.

The application code uses bare `app.*` imports (e.g. `from app.api.v1.routes import ...`)
which is designed for running with `--app-dir src`. This conftest ensures the same
resolution works during pytest by prepending the `src` directory to sys.path.
"""
import sys
import os

# Add src/ to the front of sys.path so `import app.*` resolves correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
