from __future__ import annotations

from .models import RawProduct
from .providers import ProductProvider, StaticProductProvider


def _build_seed_data() -> dict[str, tuple[RawProduct, ...]]:
    return {
        "tesco": (
            RawProduct("tesco", "T001", "Tesco British Semi Skimmed Milk 2L", "Tesco", 1.65, "dairy"),
            RawProduct("tesco", "T002", "Heinz Baked Beans 4 x 415g", "Heinz", 3.75, "tinned"),
            RawProduct("tesco", "T003", "Tesco Free Range Eggs 12 pack", "Tesco", 2.90, "eggs"),
            RawProduct("tesco", "T004", "Tesco Fusilli Pasta 500g", "Tesco", 0.95, "dry"),
            RawProduct("tesco", "T005", "Cathedral City Mature Cheddar 350g", "Cathedral City", 3.95, "dairy"),
            RawProduct("tesco", "T006", "Tesco Apple Juice 1L", "Tesco", 1.20, "drinks"),
        ),
        "sainsburys": (
            RawProduct("sainsburys", "S001", "Sainsbury's Semi Skimmed Milk 2 Litre", "Sainsbury's", 1.70, "dairy"),
            RawProduct("sainsburys", "S002", "Branston Baked Beans 4x410g", "Branston", 2.95, "tinned"),
            RawProduct("sainsburys", "S003", "Woodland Free Range Eggs 12 Count", "Woodland", 2.55, "eggs"),
            RawProduct("sainsburys", "S004", "Sainsbury's Penne Pasta 500 g", "Sainsbury's", 0.85, "dry"),
            RawProduct("sainsburys", "S005", "Pilgrims Choice Mature Cheddar 350g", "Pilgrims Choice", 3.50, "dairy"),
            RawProduct("sainsburys", "S006", "Sainsbury's Orange Juice 1L", "Sainsbury's", 1.10, "drinks"),
        ),
        "asda": (
            RawProduct("asda", "A001", "ASDA Semi Skimmed Milk 2L", "ASDA", 1.55, "dairy"),
            RawProduct("asda", "A002", "Heinz Baked Beans 415g", "Heinz", 1.05, "tinned"),
            RawProduct("asda", "A003", "ASDA Free Range Eggs Mixed Weight 12pk", "ASDA", 2.50, "eggs"),
            RawProduct("asda", "A004", "ASDA Fusilli 500g", "ASDA", 0.78, "dry"),
            RawProduct("asda", "A005", "ASDA Mature Cheddar 400g", "ASDA", 2.89, "dairy"),
            RawProduct("asda", "A006", "ASDA Apple Juice from Concentrate 1 L", "ASDA", 0.95, "drinks"),
        ),
    }


class SeededProviderRegistry:
    def __init__(self) -> None:
        seed = _build_seed_data()
        self.providers: dict[str, ProductProvider] = {
            name: StaticProductProvider(provider_name=name, _products=products)
            for name, products in seed.items()
        }

    def all_products(self) -> list[RawProduct]:
        return [item for provider in self.providers.values() for item in provider.list_products()]
