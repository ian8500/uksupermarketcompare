from celery import Celery

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.matching import match_products

celery_app = Celery("basketcompare", broker=settings.redis_url, backend=settings.redis_url)


@celery_app.task
def match_item(query: str, retailers: list[str]) -> list[dict]:
    db = SessionLocal()
    try:
        matches = match_products(db, query, retailers)
        return [
            {
                "product": m.raw.title,
                "retailer": m.raw.retailer.slug,
                "price": m.price,
                "confidence": m.confidence_label,
            }
            for m in matches
        ]
    finally:
        db.close()
