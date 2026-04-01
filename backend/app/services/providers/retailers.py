from __future__ import annotations

import logging
import os
from pathlib import Path

from app.services.providers.base import ProviderProduct, SeedFileProvider
from app.services.providers.live_sources import LiveSourceError, TescoStructuredApiSource

IMPORT_DIR = Path(__file__).resolve().parents[2] / "data" / "imports"
logger = logging.getLogger(__name__)


class TescoProvider(SeedFileProvider):
    def __init__(self) -> None:
        super().__init__(IMPORT_DIR / "tesco.json")
        self.live_mode = os.getenv("TESCO_SOURCE_MODE", "seed").strip().lower()
        self._live_source = TescoStructuredApiSource()

    def load_products(self) -> list[ProviderProduct]:
        if self.live_mode in {"structured", "official", "thirdparty", "scrape"}:
            try:
                live_products = self._live_source.fetch_products()
                if live_products:
                    logger.info("Tesco provider returning live rows=%d mode=%s", len(live_products), self.live_mode)
                    return live_products
                logger.warning("Tesco live source returned zero products; falling back to seed data")
            except LiveSourceError as exc:
                logger.warning("Tesco live source unavailable mode=%s error=%s; using seed fallback", self.live_mode, exc)
        return super().load_products()


class AsdaProvider(SeedFileProvider):
    def __init__(self) -> None:
        super().__init__(IMPORT_DIR / "asda.json")


class SainsburysProvider(SeedFileProvider):
    def __init__(self) -> None:
        super().__init__(IMPORT_DIR / "sainsburys.json")
