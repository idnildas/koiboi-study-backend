#!/usr/bin/env python3
"""
Wrapper to start the FastAPI dev server using the project's .venv uvicorn.

Run with:
    python3 run.py

This will exec `.venv/bin/uvicorn app.main:app --reload --app-dir src`.
"""
import os
import sys


HERE = os.path.dirname(__file__)
uvicorn_path = os.path.join(HERE, ".venv", "bin", "uvicorn")

if not os.path.exists(uvicorn_path):
    sys.stderr.write(
        f"uvicorn not found at {uvicorn_path}.\nPlease create/activate the virtualenv or run .venv/bin/uvicorn directly.\n"
    )
    sys.exit(1)

port = os.environ.get("PORT", "8080")
args = [uvicorn_path, "app.main:app", "--reload", "--app-dir", "src", "--port", port]

# Ensure the venv site-packages are on PYTHONPATH for reload subprocesses
venv_site_packages = os.path.join(HERE, ".venv", "lib", "python3.12", "site-packages")
existing = os.environ.get("PYTHONPATH", "")
os.environ["PYTHONPATH"] = f"{venv_site_packages}:{existing}" if existing else venv_site_packages

# Replace current process with uvicorn so signals (Ctrl+C) are handled by uvicorn.
os.execv(uvicorn_path, args)
