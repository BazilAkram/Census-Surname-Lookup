#!/usr/bin/env python3
"""
Build a compact surname lookup JSON from the official U.S. Census 2020 last-name file.

Default source:
    https://www2.census.gov/topics/genealogy/2020surnames/Names2020_LastNames_RaceHispanic.xlsx

The workbook contains the complete 2020 last-name table. This script removes the
aggregate "ALL OTHER NAMES" row and writes a compact lookup JSON:

    data/surnames.lookup.json

The output format is:
    {
      "schema": [
        "rank",
        "count",
        "prop100k",
        "countwhite",
        "countblack",
        "countaian",
        "countapi",
        "count2prace",
        "counthispanic"
      ],
      "surnames": {
        "SMITH": [1, 2369644, 792.79, 1611236, 535967, 19744, 16139, 103611, 82947],
        ...
      }
    }

The UI computes the displayed percentages directly from the stored category counts.
"""

from __future__ import annotations

import argparse
import io
import json
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path, PurePosixPath

OFFICIAL_XLSX_URL = (
    "https://www2.census.gov/topics/genealogy/2020surnames/"
    "Names2020_LastNames_RaceHispanic.xlsx"
)
EXCLUDED_NAME = "ALL OTHER NAMES"
OUTPUT_SCHEMA = [
    "rank",
    "count",
    "prop100k",
    "countwhite",
    "countblack",
    "countaian",
    "countapi",
    "count2prace",
    "counthispanic",
]
WORKSHEET_HEADERS = [
    "LAST NAME",
    "RANK",
    "FREQUENCY (COUNT)",
    "PROPORTION PER 100,000 POPULATION",
    "CUMULATIVE PROPORTION",
    "NON-HISPANIC OR LATINO WHITE ALONE",
    "NON-HISPANIC OR LATINO BLACK OR AFRICAN AMERICAN ALONE",
    "NON-HISPANIC OR LATINO AMERICAN INDIAN AND ALASKA NATIVE ALONE",
    "NON-HISPANIC OR LATINO ASIAN AND NATIVE HAWAIIAN AND OTHER PACIFIC ISLANDER ALONE",
    "NON-HISPANIC OR LATINO TWO OR MORE RACES",
    "HISPANIC OR LATINO ORIGIN",
]
SPREADSHEET_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def fetch_workbook_bytes(url: str) -> bytes:
    with urllib.request.urlopen(url) as response:
        return response.read()


def workbook_first_sheet_path(zf: zipfile.ZipFile) -> str:
    workbook_root = ET.fromstring(zf.read("xl/workbook.xml"))
    first_sheet = workbook_root.find(f"{SPREADSHEET_NS}sheets/{SPREADSHEET_NS}sheet")
    if first_sheet is None:
        raise ValueError("Workbook does not contain any worksheets.")

    rel_id = first_sheet.attrib.get(f"{{{REL_NS}}}id")
    if rel_id is None:
        raise ValueError("Could not resolve the first worksheet relationship id.")

    rels_root = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    for relationship in rels_root.findall(f"{PACKAGE_REL_NS}Relationship"):
        if relationship.attrib.get("Id") != rel_id:
            continue

        target = relationship.attrib["Target"].lstrip("/")
        if target.startswith("xl/"):
            return target
        return str(PurePosixPath("xl") / PurePosixPath(target))

    raise ValueError(f"Could not resolve worksheet path for relationship id {rel_id}.")


def read_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []

    shared_strings_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    shared_strings: list[str] = []

    for item in shared_strings_root.findall(f"{SPREADSHEET_NS}si"):
        shared_strings.append("".join(item.itertext()))

    return shared_strings


def column_letters_to_index(cell_reference: str) -> int:
    letters = []
    for char in cell_reference:
        if not char.isalpha():
            break
        letters.append(char)

    index = 0
    for letter in letters:
        index = (index * 26) + (ord(letter.upper()) - ord("A") + 1)

    return index - 1


def parse_numeric_or_text(value: str) -> int | float | str:
    number = float(value)
    if number.is_integer():
        return int(number)
    return number


def cell_value(cell: ET.Element, shared_strings: list[str]) -> int | float | str | None:
    cell_type = cell.attrib.get("t")

    if cell_type == "inlineStr":
        inline_string = cell.find(f"{SPREADSHEET_NS}is")
        if inline_string is None:
            return None
        return "".join(inline_string.itertext())

    value_node = cell.find(f"{SPREADSHEET_NS}v")
    if value_node is None or value_node.text is None:
        return None

    raw_value = value_node.text
    if cell_type == "s":
        return shared_strings[int(raw_value)]
    if cell_type == "str":
        return raw_value

    try:
        return parse_numeric_or_text(raw_value)
    except ValueError:
        return raw_value


def iter_sheet_rows(xlsx_bytes: bytes):
    with zipfile.ZipFile(io.BytesIO(xlsx_bytes)) as zf:
        shared_strings = read_shared_strings(zf)
        sheet_path = workbook_first_sheet_path(zf)

        with zf.open(sheet_path) as sheet_xml:
            for _, element in ET.iterparse(sheet_xml, events=("end",)):
                if element.tag != f"{SPREADSHEET_NS}row":
                    continue

                cells: dict[int, int | float | str | None] = {}
                for cell in element.findall(f"{SPREADSHEET_NS}c"):
                    ref = cell.attrib.get("r")
                    if not ref:
                        continue
                    cells[column_letters_to_index(ref)] = cell_value(cell, shared_strings)

                if cells:
                    max_index = max(cells)
                    yield [cells.get(index) for index in range(max_index + 1)]

                element.clear()


def parse_required_int(value: int | float | str | None) -> int:
    if value is None:
        raise ValueError("Expected an integer value but found an empty cell.")
    return int(value)


def parse_required_float(value: int | float | str | None) -> float:
    if value is None:
        raise ValueError("Expected a numeric value but found an empty cell.")
    return float(value)


def parse_count(value: int | float | str | None) -> int:
    if value is None:
        return 0
    return int(value)


def build_lookup(rows) -> dict[str, list[int | float]]:
    lookup: dict[str, list[int | float]] = {}

    next(rows, None)
    next(rows, None)
    headers = next(rows, None)
    if headers != WORKSHEET_HEADERS:
        raise ValueError(f"Unexpected worksheet headers: {headers!r}")

    for row in rows:
        if not row or row[0] is None:
            continue

        name = str(row[0]).strip()
        if name == EXCLUDED_NAME:
            continue

        lookup[name] = [
            parse_required_int(row[1]),
            parse_required_int(row[2]),
            round(parse_required_float(row[3]), 2),
            parse_count(row[5]),
            parse_count(row[6]),
            parse_count(row[7]),
            parse_count(row[8]),
            parse_count(row[9]),
            parse_count(row[10]),
        ]

    return lookup


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-xlsx",
        type=Path,
        help="Optional local path to Names2020_LastNames_RaceHispanic.xlsx. If omitted, the script downloads the official Census workbook.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/surnames.lookup.json"),
        help="Output JSON path.",
    )
    args = parser.parse_args()

    if args.source_xlsx:
        xlsx_bytes = args.source_xlsx.read_bytes()
    else:
        print(f"Downloading official Census workbook from {OFFICIAL_XLSX_URL} ...")
        xlsx_bytes = fetch_workbook_bytes(OFFICIAL_XLSX_URL)

    lookup = {"schema": OUTPUT_SCHEMA, "surnames": build_lookup(iter_sheet_rows(xlsx_bytes))}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as file_obj:
        json.dump(lookup, file_obj, ensure_ascii=True, separators=(",", ":"))

    print(f"Wrote {len(lookup['surnames']):,} surnames to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
