from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.models import SavedBasketRecord, SavedBasketRerunRequest, SavedBasketUpsertRequest
from app.services.mock_compare_service import build_comparison

router = APIRouter(prefix="/saved-baskets", tags=["saved-baskets"])

_SAVED: dict[str, SavedBasketRecord] = {}


@router.get("", response_model=list[SavedBasketRecord])
def list_saved_baskets() -> list[SavedBasketRecord]:
    return list(_SAVED.values())


@router.post("", response_model=SavedBasketRecord)
def create_saved_basket(request: SavedBasketUpsertRequest) -> SavedBasketRecord:
    record = SavedBasketRecord(id=uuid4(), shoppingList=request.shoppingList)
    _SAVED[str(record.id)] = record
    return record


@router.put("/{basket_id}", response_model=SavedBasketRecord)
def edit_saved_basket(basket_id: str, request: SavedBasketUpsertRequest) -> SavedBasketRecord:
    existing = _SAVED.get(basket_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Saved basket not found")
    updated = SavedBasketRecord(id=existing.id, shoppingList=request.shoppingList, lastResult=existing.lastResult)
    _SAVED[basket_id] = updated
    return updated


@router.post("/{basket_id}/duplicate", response_model=SavedBasketRecord)
def duplicate_saved_basket(basket_id: str) -> SavedBasketRecord:
    existing = _SAVED.get(basket_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Saved basket not found")
    duplicated_list = existing.shoppingList.model_copy(update={"id": uuid4(), "title": f"{existing.shoppingList.title} (Copy)"})
    duplicate = SavedBasketRecord(id=uuid4(), shoppingList=duplicated_list, lastResult=existing.lastResult)
    _SAVED[str(duplicate.id)] = duplicate
    return duplicate


@router.post("/{basket_id}/rerun", response_model=SavedBasketRecord)
def rerun_saved_basket(basket_id: str, request: SavedBasketRerunRequest) -> SavedBasketRecord:
    existing = _SAVED.get(basket_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Saved basket not found")

    comparison = build_comparison(
        request.model_copy(update={"shoppingList": existing.shoppingList})
    )
    refreshed = existing.model_copy(update={"lastResult": comparison.result})
    _SAVED[basket_id] = refreshed
    return refreshed
