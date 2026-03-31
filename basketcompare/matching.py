from __future__ import annotations

from dataclasses import dataclass

from .models import CanonicalProduct, ConfidenceBand, PackSize


@dataclass(frozen=True)
class ConfidenceScorer:
    exact_threshold: float = 0.85
    close_threshold: float = 0.70

    def score(self, wanted: CanonicalProduct, candidate: CanonicalProduct) -> tuple[float, ConfidenceBand, str]:
        token_overlap = self._jaccard(wanted.searchable_tokens, candidate.searchable_tokens)
        brand_score = 1.0 if wanted.normalized_brand == candidate.normalized_brand else 0.7
        category_score = 1.0 if wanted.category == candidate.category else 0.4
        pack_score = self._pack_score(wanted.pack_size, candidate.pack_size)

        final = (token_overlap * 0.45) + (brand_score * 0.25) + (category_score * 0.15) + (pack_score * 0.15)

        if token_overlap >= 0.95 and brand_score == 1.0 and category_score == 1.0 and pack_score >= 0.95:
            return max(final, 0.95), ConfidenceBand.EXACT, "Exact match on core identity attributes"
        if final >= self.exact_threshold:
            return final, ConfidenceBand.EXACT, "Strong token, brand, category and pack alignment"
        if final >= self.close_threshold:
            return final, ConfidenceBand.CLOSE, "Near match; minor differences in brand, naming, or size"
        if final >= 0.45:
            return final, ConfidenceBand.SUBSTITUTE, "Substitution candidate in same broad category"
        return final, ConfidenceBand.NONE, "Insufficient similarity"

    def _jaccard(self, left: tuple[str, ...], right: tuple[str, ...]) -> float:
        a = set(left)
        b = set(right)
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    def _pack_score(self, wanted: PackSize | None, candidate: PackSize | None) -> float:
        if wanted is None and candidate is None:
            return 1.0
        if wanted is None or candidate is None:
            return 0.5
        if wanted.normalized_unit != candidate.normalized_unit:
            return 0.0
        diff = abs(wanted.normalized_amount - candidate.normalized_amount)
        pct_diff = diff / max(wanted.normalized_amount, 1)
        if pct_diff <= 0.02:
            return 1.0
        if pct_diff <= 0.10:
            return 0.8
        if pct_diff <= 0.25:
            return 0.6
        return 0.3
