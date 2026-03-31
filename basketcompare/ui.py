from __future__ import annotations

from .models import BasketPlan


def render_results(plan: BasketPlan) -> dict:
    return {
        "plan": plan.plan_name,
        "total": plan.total_cost_gbp,
        "items": [
            {
                "query": m.query,
                "picked": m.raw_product.title,
                "store": m.raw_product.provider,
                "price": m.raw_product.price_gbp,
                "confidence_band": m.confidence_band.value,
                "confidence_score": m.confidence_score,
                "why_matched": m.reason,
            }
            for m in plan.matched_items
        ],
        "notes": list(plan.notes),
    }
