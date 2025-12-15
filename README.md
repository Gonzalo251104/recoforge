# RecoForge

Recommendation API (FastAPI) implementing content-based, user-based and hybrid strategies (WIP).

## Run (Poetry)

```bash
poetry install
poetry run uvicorn app.main:app --reload
```

Open: http://127.0.0.1:8000/docs

## Health check

curl http://127.0.0.1:8000/health
