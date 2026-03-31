from dataclasses import dataclass

from rapidfuzz.fuzz import token_set_ratio
from sqlalchemy.orm import Session

from app.models.entities import ProductPriceSnapshot, ProductRaw, Retailer
from app.services.normalization import normalize_text


@dataclass
class MatchResult:
    raw: ProductRaw
    price: float
    unit_price: float | None
    confidence_label: str
    confidence_score: float
    uncertainty_note: str | None


def _confidence(score: float, same_brand: bool, size_diff: bool) -> tuple[str, str | None]:
    if score > 90 and same_brand and not size_diff:
        return "exact", None
    if score > 75 and not size_diff:
        return "close", None
    note = "Comparison uncertainty: pack size or product type may differ"
    return "substitute", note


def match_products(db: Session, query: str, retailer_slugs: list[str]) -> list[MatchResult]:
    nq = normalize_text(query)
    results: list[MatchResult] = []
    retailers = db.query(Retailer).filter(Retailer.slug.in_(retailer_slugs)).all()
    for retailer in retailers:
        products = db.query(ProductRaw).filter(ProductRaw.retailer_id == retailer.id).all()
        best: tuple[ProductRaw, float] | None = None
        for p in products:
            score = token_set_ratio(nq, p.normalized_title)
            if best is None or score > best[1]:
                best = (p, score)
        if best is None:
            continue
        raw, score = best
        snap = (
            db.query(ProductPriceSnapshot)
            .filter(ProductPriceSnapshot.product_raw_id == raw.id)
            .order_by(ProductPriceSnapshot.captured_at.desc())
            .first()
        )
        if not snap:
            continue
        same_brand = (raw.brand or "") in nq if raw.brand else False
        size_diff = False
        label, note = _confidence(score, same_brand, size_diff)
        results.append(
            MatchResult(
                raw=raw,
                price=snap.price,
                unit_price=snap.unit_price,
                confidence_label=label,
                confidence_score=round(score / 100, 2),
                uncertainty_note=note,
            )
        )
    return sorted(results, key=lambda r: r.price)
