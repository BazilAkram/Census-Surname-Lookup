#!/usr/bin/env python3
"""
Build a tiny surname lookup JSON from the official U.S. Census 2010 surname file.

Default source:
    https://www2.census.gov/topics/genealogy/2010surnames/names.zip

The ZIP contains the complete surname CSV. This script extracts the CSV,
drops the aggregate "ALL OTHER NAMES" row, and writes a compact lookup JSON:

    data/surnames-2010.lookup.json

The output format is:
    {
      "SMITH": [1, 2442977],
      "JOHNSON": [2, 1932812],
      ...
    }

where each value is:
    [rank, count]
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

OFFICIAL_ZIP_URL = "https://www2.census.gov/topics/genealogy/2010surnames/names.zip"
CSV_FILENAME = "Names_2010Census.csv"
EXCLUDED_NAME = "ALL OTHER NAMES"


def fetch_official_csv_bytes(url: str) -> bytes:
    with urllib.request.urlopen(url) as response:
        return response.read()


def extract_csv_from_zip(zip_bytes: bytes, csv_filename: str) -> str:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        with zf.open(csv_filename) as csv_file:
            return csv_file.read().decode("utf-8-sig")


def read_csv_text(csv_text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(csv_text)))


def read_csv_path(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build_lookup(rows: list[dict[str, str]]) -> dict[str, list[int]]:
    lookup: dict[str, list[int]] = {}

    for row in rows:
        name = row["name"].strip()
        if name == EXCLUDED_NAME:
            continue

        lookup[name] = [int(row["rank"]), int(row["count"])]

    return lookup


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-csv",
        type=Path,
        help="Optional local path to Names_2010Census.csv. If omitted, the script downloads the official Census ZIP.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/surnames-2010.lookup.json"),
        help="Output JSON path.",
    )
    args = parser.parse_args()

    if args.source_csv:
        rows = read_csv_path(args.source_csv)
    else:
        print(f"Downloading official Census ZIP from {OFFICIAL_ZIP_URL} ...")
        zip_bytes = fetch_official_csv_bytes(OFFICIAL_ZIP_URL)
        csv_text = extract_csv_from_zip(zip_bytes, CSV_FILENAME)
        rows = read_csv_text(csv_text)

    lookup = build_lookup(rows)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(lookup, f, ensure_ascii=True, separators=(",", ":"))

    print(f"Wrote {len(lookup):,} surnames to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
