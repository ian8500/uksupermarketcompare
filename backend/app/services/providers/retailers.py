from __future__ import annotations

import logging
import os
from pathlib import Path

from app.services.providers.base import ProviderProduct, SeedFileProvider
from app.services.providers.live_sources import (
    LiveSourceError,
    TescoLiveSourceConfig,
    TescoOfficialApiSource,
    TescoThirdPartyApiSource,
)

IMPORT_DIR = Path(__file__).resolve().parents[2] / "data" / "imports"
logger = logging.getLogger(__name__)


class TescoProvider(SeedFileProvider):
    def __init__(self) -> None:
        super().__init__(IMPORT_DIR / "tesco.json")
        self.config = TescoLiveSourceConfig.from_env()
        self._official = TescoOfficialApiSource(self.config)
        self._third_party = TescoThirdPartyApiSource(self.config)
        self._active_source = "seed"
        self._last_import_report: dict[str, int | str] = {"source": "seed", "fetched": 0, "skipped": 0, "rejected": 0, "mapped": 0}

    @property
    def active_source(self) -> str:
        return self._active_source

    @property
    def last_import_report(self) -> dict[str, int | str]:
        return dict(self._last_import_report)

    def load_products(self) -> list[ProviderProduct]:
        requested = self.config.mode
        ordered_sources = []
        if requested == "official":
            ordered_sources = [self._official]
        elif requested in {"thirdparty", "structured"}:
            ordered_sources = [self._third_party]
        elif requested == "seed":
            ordered_sources = []
        else:  # auto
            ordered_sources = [self._official, self._third_party]

        for source in ordered_sources:
            if not source.is_configured():
                logger.info("Tesco source skipped source=%s reason=not-configured", source.source_name)
                continue
            try:
                live_products = source.fetch_products()
                if live_products:
                    self._active_source = source.source_name
                    self._last_import_report = {
                        "source": source.source_name,
                        "fetched": int(source.last_fetch_report.get("fetched", len(live_products))),
                        "skipped": int(source.last_fetch_report.get("skipped", 0)),
                        "rejected": int(source.last_fetch_report.get("rejected", 0)),
                        "mapped": int(source.last_fetch_report.get("mapped", len(live_products))),
                    }
                    logger.info("Tesco provider using live source=%s rows=%d", source.source_name, len(live_products))
                    return live_products
                logger.warning("Tesco source returned zero products source=%s", source.source_name)
            except LiveSourceError as exc:
                logger.warning("Tesco source failed source=%s error=%s", source.source_name, exc)

        self._active_source = "seed"
        logger.info("Tesco provider fallback=seed mode=%s", requested)
        seed_products = super().load_products()
        self._last_import_report = {"source": "seed", "fetched": len(seed_products), "skipped": 0, "rejected": 0, "mapped": len(seed_products)}
        return seed_products


class AsdaProvider(SeedFileProvider):
    def __init__(self) -> None:
        super().__init__(IMPORT_DIR / "asda.json")


class SainsburysProvider(SeedFileProvider):
    def __init__(self) -> None:
        super().__init__(IMPORT_DIR / "sainsburys.json")
