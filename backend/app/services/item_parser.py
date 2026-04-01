import re
from decimal import Decimal
from difflib import get_close_matches

from app.models import ParsedItem

UNIT_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s?(?P<unit>kg|g|l|ml|pack|pk)\b", re.IGNORECASE)
QTY_PATTERN = re.compile(r"^(?P<qty>\d{1,2})\s*[xX]?\s+(?P<rest>.+)$")

ALIAS_MAP: dict[str, str] = {
    "yoghurt": "yogurt",
    "beanz": "beans",
    "semi-skimmed": "semi skimmed",
    "wholemeal": "whole meal",
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
}

PREFERENCE_WORDS = {"organic", "own", "branded", "premium", "value", "free range", "semi skimmed", "whole"}


def parse_item_input(raw: str, fallback_quantity: int = 1) -> ParsedItem:
    cleaned = raw.strip()
    if not cleaned:
        return ParsedItem(name="", quantity=max(1, fallback_quantity))

    quantity = max(1, fallback_quantity)
    name = cleaned
    corrections: list[str] = []

    quantity_match = re.match(QTY_PATTERN, cleaned)
    if quantity_match:
        quantity = max(1, min(99, int(quantity_match.group("qty"))))
        name = quantity_match.group("rest").strip()

    size_match = UNIT_PATTERN.search(name)
    size_value = Decimal(size_match.group("value")) if size_match else None
    size_unit = size_match.group("unit").lower() if size_match else None
    if size_match:
        name = UNIT_PATTERN.sub("", name).strip()

    tokens = [token for token in re.split(r"\s+", name.lower()) if token]
    normalized_tokens: list[str] = []
    for token in tokens:
        aliased = ALIAS_MAP.get(token, token)
        if aliased != token:
            corrections.append(f"{token}→{aliased}")
        if aliased not in ALIAS_MAP.values() and aliased not in KNOWN_BRANDS and len(aliased) > 4:
            nearest = get_close_matches(aliased, list(ALIAS_MAP.values()) + sorted(KNOWN_BRANDS), n=1, cutoff=0.85)
            if nearest:
                corrections.append(f"{aliased}→{nearest[0]}")
                aliased = nearest[0]
        normalized_tokens.append(aliased)

    detected_brand = next((token for token in normalized_tokens if token in KNOWN_BRANDS), None)
    preference_tags = sorted([phrase for phrase in PREFERENCE_WORDS if phrase in " ".join(normalized_tokens)])
    parsed_name = " ".join(normalized_tokens).strip()

    if not parsed_name:
        return ParsedItem(name=cleaned, quantity=max(1, fallback_quantity))

    return ParsedItem(
        name=parsed_name,
        quantity=quantity,
        brand=detected_brand,
        requestedSizeValue=size_value,
        requestedSizeUnit=size_unit,
        preferenceTags=preference_tags,
        parsedTokens=normalized_tokens,
        corrections=corrections,
    )
