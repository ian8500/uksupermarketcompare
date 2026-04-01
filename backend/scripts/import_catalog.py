from __future__ import annotations

import argparse

from app.db import init_db
from app.services.ingestion import import_catalog_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Import retailer catalog data into the normalized store")
    parser.add_argument("--replace", action="store_true", help="Replace existing retailer raw rows before importing")
    args = parser.parse_args()

    init_db()
    result = import_catalog_data(replace_existing=args.replace)
    print("Catalog import complete:", result)


if __name__ == "__main__":
    main()
