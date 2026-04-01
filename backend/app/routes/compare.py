import logging

from fastapi import APIRouter, HTTPException

from app.models import CompareRequest, CompareResponse
from app.services.mock_compare_service import build_comparison

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post('/compare', response_model=CompareResponse)
def compare(request: CompareRequest) -> CompareResponse:
    try:
        return build_comparison(request)
    except Exception as exc:
        logger.exception("compare request failed supermarkets=%s error=%s", [s.name for s in request.supermarkets], exc)
        raise HTTPException(status_code=500, detail="Comparison failed") from exc
