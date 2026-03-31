from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Unit(str, Enum):
    G = "g"
    KG = "kg"
    ML = "ml"
    L = "l"
    COUNT = "count"


class ConfidenceBand(str, Enum):
    EXACT = "exact"
    CLOSE = "close"
    SUBSTITUTE = "substitute"
    NONE = "none"


@dataclass(frozen=True)
class PackSize:
    quantity: float
    unit: Unit
    multiplier: int = 1

    @property
    def normalized_amount(self) -> float:
        if self.unit == Unit.KG:
            return self.quantity * 1000 * self.multiplier
        if self.unit == Unit.L:
            return self.quantity * 1000 * self.multiplier
        return self.quantity * self.multiplier

    @property
    def normalized_unit(self) -> Unit:
        if self.unit == Unit.KG:
            return Unit.G
        if self.unit == Unit.L:
            return Unit.ML
        return self.unit


@dataclass(frozen=True)
class RawProduct:
    provider: str
    sku: str
    title: str
    brand: str
    price_gbp: float
    category: str


@dataclass(frozen=True)
class CanonicalProduct:
    canonical_name: str
    normalized_brand: str
    category: str
    pack_size: PackSize | None
    searchable_tokens: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ProductMatch:
    query: str
    wanted_pack_size: PackSize | None
    raw_product: RawProduct
    canonical_product: CanonicalProduct
    confidence_score: float
    confidence_band: ConfidenceBand
    reason: str


@dataclass(frozen=True)
class BasketPlan:
    plan_name: str
    matched_items: tuple[ProductMatch, ...]
    total_cost_gbp: float
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DebugRow:
    raw_product: RawProduct
    canonical: CanonicalProduct
    metadata: dict[str, Any]
