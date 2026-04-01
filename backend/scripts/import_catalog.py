from __future__ import annotations

import argparse
import os

from app.db import init_db
from app.services.ingestion import import_catalog_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Import retailer catalog data into the normalized store")
    parser.add_argument("--replace", action="store_true", help="Replace existing retailer raw rows before importing")
    parser.add_argument(
        "--tesco-live",
        action="store_true",
        help="Use Tesco live source mode (requires TESCO_THIRD_PARTY_API_KEY or TESCO_OFFICIAL_API_KEY + related base URL settings)",
    )
    args = parser.parse_args()

    if args.tesco_live:
        os.environ["TESCO_SOURCE_MODE"] = os.getenv("TESCO_SOURCE_MODE", "structured")

    init_db()
    result = import_catalog_data(replace_existing=args.replace)
    print("Catalog import complete:", result)


if __name__ == "__main__":
    main()
