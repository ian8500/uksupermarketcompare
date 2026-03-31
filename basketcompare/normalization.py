from __future__ import annotations

import re
from dataclasses import dataclass

from .models import CanonicalProduct, PackSize, RawProduct, Unit

STOPWORDS = {
    "the",
    "and",
    "with",
    "fresh",
    "british",
    "pack",
    "value",
    "range",
    "by",
    "for",
}

PACK_REGEXES: tuple[tuple[re.Pattern[str], Unit], ...] = (
    (re.compile(r"(?P<qty>\d+(?:\.\d+)?)\s?kg\b", re.I), Unit.KG),
    (re.compile(r"(?P<qty>\d+(?:\.\d+)?)\s?g\b", re.I), Unit.G),
    (re.compile(r"(?P<qty>\d+(?:\.\d+)?)\s?ml\b", re.I), Unit.ML),
    (re.compile(r"(?P<qty>\d+(?:\.\d+)?)\s?l\b", re.I), Unit.L),
    (re.compile(r"(?P<qty>\d+)\s?(?:ct|count|pk|pack)\b", re.I), Unit.COUNT),
)

MULTIPACK_REGEX = re.compile(r"(?P<multi>\d+)\s?[x×]\s?(?P<qty>\d+(?:\.\d+)?)\s?(?P<unit>kg|g|ml|l|ct)", re.I)


@dataclass(frozen=True)
class CanonicalProductNormalizer:
    """Normalizes raw products into canonical product fields."""

    def normalize(self, raw: RawProduct) -> CanonicalProduct:
        normalized_brand = self._normalize_brand(raw.brand)
        pack = self.parse_pack_size(raw.title)
        tokens = tuple(self._tokenize(raw.title))
        canonical_name = " ".join(t for t in tokens if not t.isdigit())
        return CanonicalProduct(
            canonical_name=canonical_name,
            normalized_brand=normalized_brand,
            category=raw.category.lower(),
            pack_size=pack,
            searchable_tokens=tokens,
        )

    def parse_pack_size(self, text: str) -> PackSize | None:
        if m := MULTIPACK_REGEX.search(text):
            unit_text = m.group("unit").lower()
            unit = Unit.COUNT if unit_text == "ct" else Unit(unit_text)
            return PackSize(
                quantity=float(m.group("qty")),
                unit=unit,
                multiplier=int(m.group("multi")),
            )

        for regex, unit in PACK_REGEXES:
            if m := regex.search(text):
                qty = float(m.group("qty"))
                return PackSize(quantity=qty, unit=unit)
        return None

    def _tokenize(self, text: str) -> list[str]:
        lowered = text.lower()
        lowered = re.sub(r"(\d+)\s*[x×]\s*(\d+)", r"\1 x \2", lowered)
        lowered = re.sub(r"(\d)([a-z])", r"\1 \2", lowered)
        lowered = re.sub(r"([a-z])(\d)", r"\1 \2", lowered)
        cleaned = re.sub(r"[^a-zA-Z0-9 ]", " ", lowered)
        return [t for t in cleaned.split() if t not in STOPWORDS]

    def _normalize_brand(self, brand: str) -> str:
        return re.sub(r"\s+", " ", brand.strip().lower())
