from fastapi import APIRouter

from app.models import CompareRequest, CompareResponse
from app.services.mock_compare_service import build_comparison

router = APIRouter()


@router.post('/compare', response_model=CompareResponse)
def compare(request: CompareRequest) -> CompareResponse:
    return build_comparison(request)
