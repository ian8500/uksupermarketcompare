import re

from app.models import ParsedItem


def parse_item_input(raw: str, fallback_quantity: int = 1) -> ParsedItem:
    cleaned = raw.strip()
    if not cleaned:
        return ParsedItem(name="", quantity=max(1, fallback_quantity))

    pattern = r"^(\d{1,2})\s*[xX]?\s+(.+)$"
    match = re.match(pattern, cleaned)
    if not match:
        return ParsedItem(name=cleaned, quantity=max(1, fallback_quantity))

    qty = max(1, min(99, int(match.group(1))))
    name = match.group(2).strip()
    if not name:
        return ParsedItem(name=cleaned, quantity=max(1, fallback_quantity))
    return ParsedItem(name=name, quantity=qty)
