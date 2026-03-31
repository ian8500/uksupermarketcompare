# BasketCompare MVP

BasketCompare is a mobile-first UK grocery basket comparison app with a canonical grocery intelligence layer.

## Architecture

Services:
1. `frontend` (Next.js + TypeScript + Tailwind)
2. `api` (FastAPI + SQLAlchemy + PostgreSQL)
3. `ingestion` (provider interfaces + mock retailer fixtures)
4. `matching` (normalisation + matching rules, async-ready worker)

Core model entities:
- Retailer
- ProductRaw
- ProductCanonical
- ProductPriceSnapshot
- ProductMatch
- Basket
- BasketItem
- User
- SavedList

## Local setup

```bash
cp .env.example .env
docker compose up --build
```

Then run ingestion once container is up:

```bash
docker compose run --rm ingestion
```

App URLs:
- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs


## Xcode (iOS) support

This repo is **not a native Swift app**, but the Next.js frontend can be wrapped and run from Xcode using Capacitor.

1. Install frontend dependencies:

```bash
cd frontend
npm install
```

2. Start the existing app services from the repo root:

```bash
docker compose up --build
```

3. In a second terminal, run the iOS sync/open flow:

```bash
cd frontend
npm run xcode
```

4. Xcode opens `ios/App/App.xcworkspace`. Pick an iOS Simulator and press **Run**.

### Running on a physical iPhone

When using a real device, set `CAP_SERVER_URL` to your computer's LAN IP so the phone can reach your Next.js frontend:

```bash
cd frontend
CAP_SERVER_URL=http://192.168.1.20:3000 npm run xcode
```

Also set `NEXT_PUBLIC_API_URL` to a reachable backend address (not localhost on the phone), for example:

```bash
NEXT_PUBLIC_API_URL=http://192.168.1.20:8000
```

## API Endpoints

- `POST /lists/parse`
- `POST /baskets/compare`
- `GET /baskets/{id}`
- `POST /saved-lists`
- `GET /saved-lists`
- `GET /products/search`
- `GET /admin/matches`

## Matching strategy (MVP)

Canonical matching uses:
- normalized title
- brand signal
- category
- size/unit fields
- latest unit price

Confidence labels:
- `exact`
- `close`
- `substitute`

Substitutions supported:
- branded -> branded across stores
- branded -> own-brand equivalent
- own-brand -> own-brand equivalent

A comparison uncertainty note is added when match quality is weaker.

## Tests

```bash
cd backend
pip install -r requirements.txt
PYTHONPATH=. pytest -q
```

## Fixtures

Mock data includes 54 grocery products (18 each for Tesco, Sainsbury's, Asda) in `ingestion/fixtures/*.json`.

## Extendability notes

- Ingestion providers implement a shared interface (`Provider`), so real APIs can replace mocks.
- Matching uses Postgres-friendly lexical matching first and is designed to swap to Typesense/OpenSearch later.
- Embeddings are disabled by default and gated behind `ENABLE_EMBEDDINGS`.
