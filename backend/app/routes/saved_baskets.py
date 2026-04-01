from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.models import SavedBasketRecord, SavedBasketRerunRequest, SavedBasketUpsertRequest
from app.services.mock_compare_service import build_comparison
from datetime import datetime, UTC

router = APIRouter(prefix="/saved-baskets", tags=["saved-baskets"])

_SAVED: dict[str, SavedBasketRecord] = {}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


@router.get("", response_model=list[SavedBasketRecord])
def list_saved_baskets() -> list[SavedBasketRecord]:
    return list(_SAVED.values())


@router.post("", response_model=SavedBasketRecord)
def create_saved_basket(request: SavedBasketUpsertRequest) -> SavedBasketRecord:
    now = _now_iso()
    record = SavedBasketRecord(
        id=uuid4(),
        shoppingList=request.shoppingList,
        createdAt=now,
        updatedAt=now,
        tags=request.tags,
        notes=request.notes,
    )
    _SAVED[str(record.id)] = record
    return record


@router.put("/{basket_id}", response_model=SavedBasketRecord)
def edit_saved_basket(basket_id: str, request: SavedBasketUpsertRequest) -> SavedBasketRecord:
    existing = _SAVED.get(basket_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Saved basket not found")
    updated = SavedBasketRecord(
        id=existing.id,
        shoppingList=request.shoppingList,
        lastResult=existing.lastResult,
        createdAt=existing.createdAt,
        updatedAt=_now_iso(),
        lastRerunAt=existing.lastRerunAt,
        rerunCount=existing.rerunCount,
        tags=request.tags or existing.tags,
        notes=request.notes if request.notes is not None else existing.notes,
    )
    _SAVED[basket_id] = updated
    return updated


@router.post("/{basket_id}/duplicate", response_model=SavedBasketRecord)
def duplicate_saved_basket(basket_id: str) -> SavedBasketRecord:
    existing = _SAVED.get(basket_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Saved basket not found")
    duplicated_list = existing.shoppingList.model_copy(update={"id": uuid4(), "title": f"{existing.shoppingList.title} (Copy)"})
    now = _now_iso()
    duplicate = SavedBasketRecord(
        id=uuid4(),
        shoppingList=duplicated_list,
        lastResult=existing.lastResult,
        createdAt=now,
        updatedAt=now,
        tags=existing.tags,
        notes=existing.notes,
    )
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
    refreshed = existing.model_copy(
        update={
            "lastResult": comparison.result,
            "lastRerunAt": _now_iso(),
            "rerunCount": existing.rerunCount + 1,
            "updatedAt": _now_iso(),
        }
    )
    _SAVED[basket_id] = refreshed
    return refreshed
