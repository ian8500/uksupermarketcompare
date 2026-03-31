import re

SIZE_RE = re.compile(r"(\d+(?:\.\d+)?)\s?(kg|g|l|ml)", re.I)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", text.lower())).strip()


def parse_size(text: str) -> tuple[float | None, str | None]:
    m = SIZE_RE.search(text)
    if not m:
        return None, None
    return float(m.group(1)), m.group(2).lower()
