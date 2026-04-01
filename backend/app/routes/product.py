from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict

from app.services.product_service import get_product_detail

router = APIRouter()


class ProductDetailResponse(BaseModel):
    model_config = ConfigDict(extra="allow")


@router.get("/product/{product_id}", response_model=ProductDetailResponse)
def product_detail(product_id: str, barcode: str | None = Query(None), enrich: bool = Query(True)) -> ProductDetailResponse:
    payload = get_product_detail(product_id=product_id, barcode=barcode, enrich=enrich)
    if not payload:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductDetailResponse(**payload)
