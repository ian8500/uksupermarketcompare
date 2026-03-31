from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .models import RawProduct


class ProductProvider(Protocol):
    provider_name: str

    def list_products(self) -> list[RawProduct]: ...


@dataclass(frozen=True)
class StaticProductProvider:
    provider_name: str
    _products: tuple[RawProduct, ...]

    def list_products(self) -> list[RawProduct]:
        return list(self._products)
