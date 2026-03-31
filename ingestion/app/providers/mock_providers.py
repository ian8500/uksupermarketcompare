import json
from pathlib import Path

from .base import Provider


class JsonMockProvider(Provider):
    def __init__(self, slug: str):
        self.slug = slug

    def fetch_products(self) -> list[dict]:
        fixture = Path(__file__).resolve().parents[2] / "fixtures" / f"{self.slug}.json"
        return json.loads(fixture.read_text())


class TescoMockProvider(JsonMockProvider):
    def __init__(self):
        super().__init__("tesco")


class SainsburysMockProvider(JsonMockProvider):
    def __init__(self):
        super().__init__("sainsburys")


class AsdaMockProvider(JsonMockProvider):
    def __init__(self):
        super().__init__("asda")
