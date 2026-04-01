from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from app.models import GroceryCategory

DEFAULT_SYNONYMS: dict[str, str] = {
    "beanz": "baked beans",
    "yoghurt": "yogurt",
    "fillets": "fillet",
    "loaf": "bread",
    "semi-skimmed": "semi skimmed",
}

BRAND_NORMALIZATION: dict[str, str] = {
    "tesco stores ltd": "tesco",
    "asda stores": "asda",
    "sainsburys": "sainsbury's",
    "kelloggs": "kellogg's",
}

TAG_NORMALIZATION: dict[str, str] = {
    "beanz": "baked beans",
    "free-range": "free range",
    "semi-skimmed": "semi skimmed",
}

CATEGORY_RULES: list[tuple[GroceryCategory, set[str]]] = [
    (GroceryCategory.milk, {"milk"}),
    (GroceryCategory.bread, {"bread", "toastie", "wholemeal"}),
    (GroceryCategory.eggs, {"egg", "eggs"}),
    (GroceryCategory.butter, {"butter", "spread"}),
    (GroceryCategory.pasta, {"pasta", "penne", "spaghetti", "fusilli"}),
    (GroceryCategory.bakedBeans, {"beans", "beanz", "baked beans"}),
    (GroceryCategory.bananas, {"banana", "bananas"}),
    (GroceryCategory.chickenBreast, {"chicken", "breast", "fillet"}),
    (GroceryCategory.cereal, {"cereal", "flakes", "granola", "malted wheats"}),
    (GroceryCategory.cheese, {"cheese", "cheddar", "mozzarella"}),
    (GroceryCategory.tomatoes, {"tomato", "tomatoes"}),
    (GroceryCategory.rice, {"rice", "basmati", "long grain"}),
    (GroceryCategory.yogurt, {"yogurt", "yoghurt", "greek"}),
    (GroceryCategory.apples, {"apple", "apples", "gala", "pink lady"}),
]

SIZE_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>kg|g|l|ml|cl|pack)", flags=re.IGNORECASE)


@dataclass
class NormalizedSize:
    original: str
    value: float | None
    unit: str | None
    normalized_value: float | None
    normalized_unit: str | None


def normalize_text(text: str) -> str:
    lowered = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    cleaned = re.sub(r"[^a-z0-9\s']", " ", lowered)
    return " ".join(cleaned.split())


def normalize_brand(brand: str) -> str:
    base = normalize_text(brand)
    return BRAND_NORMALIZATION.get(base, base)


def normalize_product_name(name: str, synonyms: dict[str, str] | None = None) -> str:
    text = normalize_text(name)
    mapping = {**DEFAULT_SYNONYMS, **(synonyms or {})}
    for synonym, canonical in mapping.items():
        text = re.sub(rf"\b{re.escape(normalize_text(synonym))}\b", normalize_text(canonical), text)
    return " ".join(text.split())


def normalize_tags(tags: list[str]) -> list[str]:
    normalized = [TAG_NORMALIZATION.get(normalize_text(tag), normalize_text(tag)) for tag in tags]
    return sorted(set(filter(None, normalized)))


def normalize_size(size: str) -> NormalizedSize:
    normalized = size.strip().lower()
    match = SIZE_PATTERN.search(normalized)
    if not match:
        return NormalizedSize(original=size, value=None, unit=None, normalized_value=None, normalized_unit=None)

    value = float(match.group("value"))
    unit = match.group("unit").lower()

    if unit == "kg":
        return NormalizedSize(size, value, unit, value * 1000, "g")
    if unit == "l":
        return NormalizedSize(size, value, unit, value * 1000, "ml")
    if unit == "cl":
        return NormalizedSize(size, value, unit, value * 10, "ml")
    return NormalizedSize(size, value, unit, value, unit)


def infer_category(name: str, tags: list[str] | None = None) -> GroceryCategory:
    haystack = normalize_product_name(name)
    if tags:
        haystack = f"{haystack} {' '.join(normalize_tags(tags))}"

    for category, keywords in CATEGORY_RULES:
        if any(keyword in haystack for keyword in keywords):
            return category
    return GroceryCategory.unknown


def build_searchable_text(name: str, brand: str, size: str, tags: list[str], synonyms: dict[str, str] | None = None) -> str:
    normalized_name = normalize_product_name(name, synonyms=synonyms)
    normalized_brand = normalize_brand(brand)
    normalized_size = normalize_size(size)
    normalized_tags = normalize_tags(tags)

    terms = [normalized_name, normalized_brand, *normalized_tags]
    if normalized_size.normalized_value is not None and normalized_size.normalized_unit:
        terms.append(f"{int(normalized_size.normalized_value) if normalized_size.normalized_value.is_integer() else normalized_size.normalized_value}{normalized_size.normalized_unit}")
    return " ".join(filter(None, terms))
