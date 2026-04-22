# Koiboi Study Backend

Minimal FastAPI backend scaffold (src layout).

Quick start:

1. Create a virtualenv and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run development server:

```bash
uvicorn app.main:app --reload --app-dir src
```

3. Open http://127.0.0.1:8080/docs for the OpenAPI UI.
