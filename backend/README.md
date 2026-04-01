# UKSupermarketCompare FastAPI Backend

This backend provides the first live API for the iOS app.

## Endpoints

- `GET /health`
- `POST /compare`

`/compare` returns realistic mock comparison data using the same JSON field names used by the Swift Codable models.

## Run locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r ../requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API base URL while running locally:

- `http://localhost:8000`

Swagger docs:

- `http://localhost:8000/docs`

## iOS wiring

Set your app's live API endpoint to:

- `http://<your-machine-ip>:8000/compare`

If testing directly from Simulator on the same Mac, `localhost` also works.
