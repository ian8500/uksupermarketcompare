from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.entities import ProductPriceSnapshot, ProductRaw, Retailer
from app.services.normalization import normalize_text
from providers.mock_providers import AsdaMockProvider, SainsburysMockProvider, TescoMockProvider


def run_ingestion() -> None:
    db: Session = SessionLocal()
    providers = [TescoMockProvider(), SainsburysMockProvider(), AsdaMockProvider()]

    for provider in providers:
        retailer = db.query(Retailer).filter_by(slug=provider.slug).first()
        if not retailer:
            retailer = Retailer(name=provider.slug.title(), slug=provider.slug)
            db.add(retailer)
            db.flush()

        for row in provider.fetch_products():
            raw = ProductRaw(
                retailer_id=retailer.id,
                provider_sku=row["sku"],
                title=row["title"],
                normalized_title=normalize_text(row["title"]),
                brand=row.get("brand"),
                category=row.get("category"),
                size_value=row.get("size_value"),
                size_unit=row.get("size_unit"),
                own_brand=row.get("own_brand", False),
            )
            db.add(raw)
            db.flush()
            db.add(ProductPriceSnapshot(product_raw_id=raw.id, price=row["price"], unit_price=row.get("unit_price")))

    db.commit()
    db.close()


if __name__ == "__main__":
    run_ingestion()
