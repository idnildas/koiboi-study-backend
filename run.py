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

args = [uvicorn_path, "app.main:app", "--reload", "--app-dir", "src"]

# Replace current process with uvicorn so signals (Ctrl+C) are handled by uvicorn.
os.execv(uvicorn_path, args)
