import json

from sqlalchemy.orm import Session

from app.models.entities import Basket, BasketItem, SavedList
from app.schemas.common import BasketCompareResponse, CompareItemResult, MatchedProduct
from app.services.matching import match_products


def _build_comparison(
    db: Session, items: list[str], retailers: list[str], basket_id: int
) -> BasketCompareResponse:
    results: list[CompareItemResult] = []
    store_totals: dict[str, float] = {r: 0.0 for r in retailers}
    own_brand_savings = 0.0

    for item in items:
        matches = match_products(db, item, retailers)
        output_matches: list[MatchedProduct] = []
        branded = [m for m in matches if not m.raw.own_brand]
        own = [m for m in matches if m.raw.own_brand]
        if branded and own:
            own_brand_savings += max(0.0, min(b.price for b in branded) - min(o.price for o in own))

        for m in matches:
            store_totals[m.raw.retailer.slug] += m.price
            size = f"{m.raw.size_value:g}{m.raw.size_unit}" if m.raw.size_value and m.raw.size_unit else None
            output_matches.append(
                MatchedProduct(
                    product_name=m.raw.title,
                    supermarket=m.raw.retailer.name,
                    price=m.price,
                    unit_price=m.unit_price,
                    size=size,
                    brand=m.raw.brand,
                    own_brand=m.raw.own_brand,
                    confidence=m.confidence_label,
                    confidence_score=m.confidence_score,
                    uncertainty=m.uncertainty_note,
                )
            )
        results.append(CompareItemResult(query=item, matches=output_matches))

    cheapest = sum(min((m.price for m in match_products(db, i, retailers)), default=0) for i in items)

    return BasketCompareResponse(
        basket_id=basket_id,
        results=results,
        cheapest_overall_basket=round(cheapest, 2),
        cheapest_single_store_basket={k: round(v, 2) for k, v in store_totals.items()},
        own_brand_savings=round(own_brand_savings, 2),
    )


def compare_basket(db: Session, items: list[str], retailers: list[str]) -> BasketCompareResponse:
    basket = Basket(name="Quick Compare")
    db.add(basket)
    db.flush()

    for item in items:
        db.add(BasketItem(basket_id=basket.id, query_text=item, quantity=1))

    db.commit()
    return _build_comparison(db, items, retailers, basket.id)


def compare_existing_basket(db: Session, basket_id: int, retailers: list[str]) -> BasketCompareResponse:
    items = db.query(BasketItem).filter(BasketItem.basket_id == basket_id).all()
    return _build_comparison(db, [item.query_text for item in items], retailers, basket_id)


def create_saved_list(db: Session, name: str, items: list[str], user_id: int | None) -> SavedList:
    obj = SavedList(name=name, items_json=json.dumps(items), user_id=user_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
