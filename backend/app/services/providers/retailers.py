from __future__ import annotations

from pathlib import Path

from app.services.providers.base import SeedFileProvider

IMPORT_DIR = Path(__file__).resolve().parents[2] / "data" / "imports"


class TescoProvider(SeedFileProvider):
    def __init__(self) -> None:
        super().__init__(IMPORT_DIR / "tesco.json")


class AsdaProvider(SeedFileProvider):
    def __init__(self) -> None:
        super().__init__(IMPORT_DIR / "asda.json")


class SainsburysProvider(SeedFileProvider):
    def __init__(self) -> None:
        super().__init__(IMPORT_DIR / "sainsburys.json")
