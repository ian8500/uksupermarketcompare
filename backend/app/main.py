from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.routes.catalog import router as catalog_router
from app.routes.compare import router as compare_router
from app.routes.diagnostics import router as diagnostics_router
from app.routes.health import router as health_router
from app.routes.product import router as product_router
from app.routes.saved_baskets import router as saved_baskets_router
from app.routes.search import router as search_router
from app.services.catalog_store import ensure_seed_data

app = FastAPI(title='UKSupermarketCompare API', version='0.1.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    ensure_seed_data()


app.include_router(health_router)
app.include_router(catalog_router)
app.include_router(compare_router)
app.include_router(search_router)
app.include_router(product_router)
app.include_router(diagnostics_router)

app.include_router(saved_baskets_router)
