from __future__ import annotations

from dataclasses import dataclass

from .matching import ConfidenceScorer
from .models import BasketPlan, CanonicalProduct, ConfidenceBand, DebugRow, ProductMatch, RawProduct
from .normalization import CanonicalProductNormalizer
from .providers import ProductProvider


@dataclass
class BasketComparisonService:
    providers: dict[str, ProductProvider]
    normalizer: CanonicalProductNormalizer = CanonicalProductNormalizer()
    scorer: ConfidenceScorer = ConfidenceScorer()

    def _catalog(self) -> list[tuple[RawProduct, CanonicalProduct]]:
        catalog: list[tuple[RawProduct, CanonicalProduct]] = []
        for provider in self.providers.values():
            for raw in provider.list_products():
                catalog.append((raw, self.normalizer.normalize(raw)))
        return catalog

    def compare(self, desired_items: list[str], allow_substitutions: bool = False) -> dict[str, BasketPlan]:
        catalog = self._catalog()
        matches_all = tuple(self._best_match(item, catalog, allow_substitutions) for item in desired_items)
        matches_all = tuple(m for m in matches_all if m)

        by_store: dict[str, list[ProductMatch]] = {}
        for match in matches_all:
            by_store.setdefault(match.raw_product.provider, []).append(match)

        all_plan = BasketPlan(
            plan_name="cheapest_basket_overall",
            matched_items=matches_all,
            total_cost_gbp=round(sum(m.raw_product.price_gbp for m in matches_all), 2),
            notes=("Picks cheapest acceptable item per query across all stores.",),
        )

        single_store_plan = min(
            (
                BasketPlan(
                    plan_name=f"single_store_{store}",
                    matched_items=tuple(items),
                    total_cost_gbp=round(sum(i.raw_product.price_gbp for i in items), 2),
                    notes=("Picks best matches constrained to one store.",),
                )
                for store, items in by_store.items()
                if len(items) == len(desired_items)
            ),
            key=lambda p: p.total_cost_gbp,
            default=BasketPlan("single_store_unavailable", tuple(), 0.0, ("No store fulfilled all items",)),
        )

        own_brand_plan = self._own_brand_plan(desired_items, catalog) if allow_substitutions else BasketPlan(
            "cheapest_with_own_brand_subs_disabled", tuple(), 0.0, ("Substitutions not enabled",)
        )

        return {
            "cheapest_basket_overall": all_plan,
            "cheapest_single_store_basket": single_store_plan,
            "cheapest_with_own_brand_substitutions": own_brand_plan,
        }

    def debug_rows(self) -> list[DebugRow]:
        rows: list[DebugRow] = []
        for raw, canonical in self._catalog():
            rows.append(
                DebugRow(
                    raw_product=raw,
                    canonical=canonical,
                    metadata={
                        "normalized_pack": canonical.pack_size.normalized_amount if canonical.pack_size else None,
                        "tokens": canonical.searchable_tokens,
                    },
                )
            )
        return rows

    def _best_match(
        self,
        query: str,
        catalog: list[tuple[RawProduct, CanonicalProduct]],
        allow_substitutions: bool,
        provider_filter: str | None = None,
    ) -> ProductMatch | None:
        query_raw = RawProduct("query", "Q", query, "", 0.0, "")
        query_can = self.normalizer.normalize(query_raw)
        candidates: list[ProductMatch] = []

        for raw, canonical in catalog:
            if provider_filter and raw.provider != provider_filter:
                continue
            score, band, reason = self.scorer.score(query_can, canonical)
            if band == ConfidenceBand.NONE:
                continue
            if not allow_substitutions and band == ConfidenceBand.SUBSTITUTE:
                continue
            candidates.append(
                ProductMatch(
                    query=query,
                    wanted_pack_size=query_can.pack_size,
                    raw_product=raw,
                    canonical_product=canonical,
                    confidence_score=round(score, 3),
                    confidence_band=band,
                    reason=reason,
                )
            )

        if not candidates:
            return None
        return sorted(candidates, key=lambda c: (-c.confidence_score, c.raw_product.price_gbp))[0]

    def _own_brand_plan(self, desired_items: list[str], catalog: list[tuple[RawProduct, CanonicalProduct]]) -> BasketPlan:
        selections: list[ProductMatch] = []
        for query in desired_items:
            best = self._best_match(query, catalog, allow_substitutions=True)
            if not best:
                continue
            if best.confidence_band != ConfidenceBand.EXACT:
                own_brand_candidates = [
                    (raw, can)
                    for raw, can in catalog
                    if can.normalized_brand in {"tesco", "sainsbury's", "asda"}
                    and can.category == best.canonical_product.category
                ]
                own_best = self._best_match(
                    query,
                    own_brand_candidates,
                    allow_substitutions=True,
                )
                if own_best:
                    selections.append(own_best)
                    continue
            selections.append(best)

        return BasketPlan(
            plan_name="cheapest_with_own_brand_substitutions",
            matched_items=tuple(selections),
            total_cost_gbp=round(sum(s.raw_product.price_gbp for s in selections), 2),
            notes=("Own-brand substitutions enabled for non-exact matches.",),
        )
