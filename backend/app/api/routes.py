import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import Basket, BasketItem, ProductMatch, ProductPriceSnapshot, ProductRaw, SavedList
from app.schemas.common import (
    BasketCompareRequest,
    ListParseRequest,
    ListParseResponse,
    ParsedItem,
    SavedListIn,
    SavedListOut,
)
from app.services.basket import compare_basket, create_saved_list

router = APIRouter()


@router.post("/lists/parse", response_model=ListParseResponse)
def parse_list(payload: ListParseRequest):
    rows = [r.strip() for r in payload.text.splitlines() if r.strip()]
    items = [ParsedItem(text=r) for r in rows]
    return ListParseResponse(items=items)


@router.post("/baskets/compare")
def compare(payload: BasketCompareRequest, db: Session = Depends(get_db)):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Basket needs at least one item")
    return compare_basket(db, payload.items, payload.retailers)


@router.get("/baskets/{basket_id}")
def get_basket(basket_id: int, db: Session = Depends(get_db)):
    basket = db.query(Basket).filter(Basket.id == basket_id).first()
    if not basket:
        raise HTTPException(status_code=404, detail="Not found")
    items = db.query(BasketItem).filter(BasketItem.basket_id == basket_id).all()
    return {"id": basket.id, "name": basket.name, "items": [i.query_text for i in items]}


@router.post("/saved-lists", response_model=SavedListOut)
def save_list(payload: SavedListIn, db: Session = Depends(get_db)):
    obj = create_saved_list(db, payload.name, payload.items, payload.user_id)
    return SavedListOut(id=obj.id, name=obj.name, items=json.loads(obj.items_json))


@router.get("/saved-lists", response_model=list[SavedListOut])
def list_saved_lists(db: Session = Depends(get_db)):
    rows = db.query(SavedList).all()
    return [SavedListOut(id=r.id, name=r.name, items=json.loads(r.items_json)) for r in rows]


@router.get("/products/search")
def search_products(q: str, db: Session = Depends(get_db)):
    items = db.query(ProductRaw).filter(ProductRaw.normalized_title.contains(q.lower())).limit(20).all()
    out = []
    for p in items:
        snap = db.query(ProductPriceSnapshot).filter(ProductPriceSnapshot.product_raw_id == p.id).first()
        out.append({"id": p.id, "name": p.title, "retailer": p.retailer.slug, "price": snap.price if snap else None})
    return out


@router.get("/admin/matches")
def admin_matches(db: Session = Depends(get_db)):
    rows = db.query(ProductMatch).order_by(ProductMatch.id.desc()).limit(100).all()
    return [{"query": r.query_text, "confidence": r.confidence_label, "score": r.confidence_score} for r in rows]
