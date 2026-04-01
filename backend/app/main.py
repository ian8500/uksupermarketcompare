from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.catalog import router as catalog_router
from app.routes.compare import router as compare_router
from app.routes.health import router as health_router
from app.routes.saved_baskets import router as saved_baskets_router

app = FastAPI(title='UKSupermarketCompare API', version='0.1.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(health_router)
app.include_router(catalog_router)
app.include_router(compare_router)

app.include_router(saved_baskets_router)
