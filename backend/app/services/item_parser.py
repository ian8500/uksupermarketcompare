import re
from decimal import Decimal

from app.models import ParsedItem

QTY_PATTERN = re.compile(r"^(?P<qty>\d{1,2})\s*[xX]?\s+(?P<rest>.+)$")
UNIT_PATTERN = re.compile(r"\b(?P<value>\d+(?:\.\d+)?)\s?(?P<unit>kg|g|l|ml|pack|pk)\b", re.IGNORECASE)
PUNCT_PATTERN = re.compile(r"[^a-z0-9\s']+")

SYNONYM_MAP: dict[str, str] = {
    "beans": "baked beans",
    "beanz": "baked beans",
    "yoghurt": "yogurt",
    "yoghurts": "yogurt",
    "yogurts": "yogurt",
    "toms": "tomatoes",
    "spag": "pasta",
}

KNOWN_BRANDS = {
    "heinz",
    "lurpak",
    "barilla",
    "kellogg",
    "kellogg's",
    "cathedral",
    "cravendale",
    "tilda",
    "warburtons",
    "tesco",
    "asda",
    "sainsbury's",
}

PREFERENCE_WORDS = {
    "cheap",
    "organic",
    "own brand",
    "own",
    "value",
    "premium",
    "branded",
    "free range",
    "semi skimmed",
    "whole",
}


def _normalize_text(raw: str) -> str:
    lowered = raw.lower().strip()
    lowered = lowered.replace("-", " ")
    cleaned = PUNCT_PATTERN.sub(" ", lowered)
    return re.sub(r"\s+", " ", cleaned).strip()


def _extract_quantity(text: str, fallback_quantity: int) -> tuple[int, str]:
    quantity = max(1, fallback_quantity)
    quantity_match = QTY_PATTERN.match(text)
    if not quantity_match:
        return quantity, text

    quantity = max(1, min(99, int(quantity_match.group("qty"))))
    return quantity, quantity_match.group("rest").strip()


def _extract_size(text: str) -> tuple[Decimal | None, str | None, str]:
    size_match = UNIT_PATTERN.search(text)
    if not size_match:
        return None, None, text

    value = Decimal(size_match.group("value"))
    unit = size_match.group("unit").lower()
    remaining = UNIT_PATTERN.sub(" ", text, count=1)
    return value, unit, re.sub(r"\s+", " ", remaining).strip()


def _extract_preferences(text: str) -> tuple[list[str], str]:
    preferences = sorted([pref for pref in PREFERENCE_WORDS if pref in text])
    remaining = text
    for pref in sorted(preferences, key=len, reverse=True):
        remaining = re.sub(rf"\b{re.escape(pref)}\b", " ", remaining)
    return preferences, re.sub(r"\s+", " ", remaining).strip()


def _extract_brand(tokens: list[str]) -> tuple[str | None, list[str]]:
    detected_brand = next((token for token in tokens if token in KNOWN_BRANDS), None)
    if not detected_brand:
        return None, tokens
    return detected_brand, [token for token in tokens if token != detected_brand]


def _normalize_synonyms(text: str) -> str:
    normalized_tokens: list[str] = []
    for token in text.split():
        mapped = SYNONYM_MAP.get(token, token)
        normalized_tokens.extend(mapped.split())
    return " ".join(normalized_tokens).strip()




def _normalize_intent(tokens: list[str]) -> str:
    intent = " ".join(tokens).strip()
    intent = re.sub(r"\bbaked\s+baked\s+beans\b", "baked beans", intent)
    return re.sub(r"\s+", " ", intent).strip()

def parse_item_input(raw: str, fallback_quantity: int = 1) -> ParsedItem:
    cleaned = raw.strip()
    if not cleaned:
        return ParsedItem(rawText="", quantity=max(1, fallback_quantity), intent="")

    normalized = _normalize_text(cleaned)
    quantity, remainder = _extract_quantity(normalized, fallback_quantity)
    size_value, size_unit, remainder = _extract_size(remainder)
    preferences, remainder = _extract_preferences(remainder)

    remainder = _normalize_synonyms(remainder)
    tokens = [token for token in remainder.split(" ") if token]
    brand, intent_tokens = _extract_brand(tokens)
    intent = _normalize_intent(intent_tokens)

    if not intent:
        intent = _normalize_synonyms(remainder) or normalized

    return ParsedItem(
        rawText=cleaned,
        quantity=quantity,
        intent=intent,
        brand=brand,
        size={"value": size_value, "unit": size_unit} if size_value is not None and size_unit is not None else None,
        preferences=preferences,
    )
