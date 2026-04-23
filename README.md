# Census 2020 Surname Lookup

Tiny static web app for looking up a surname in the **official U.S. Census 2020 last-name data**.

A user types a surname, the app normalizes it to roughly match the Census surname processing rules, and the UI returns:

- normalized surname
- count
- rank
- PROP100K
- race / Hispanic percentages with the category count shown beneath each percentage

If a surname is absent from the published file, the app does **not** show `0`. It shows:

> Not found in the 2020 Census last-name file; this usually means fewer than 100 occurrences.

## Data vintage

This app uses the official **2020 Census** last-name product released by the Census Bureau on April 14, 2026.

## Project structure

```text
.
|-- app.js
|-- data/
|   `-- surnames.lookup.json
|-- index.html
|-- scripts/
|   `-- build_dataset.py
|-- styles.css
`-- README.md
```

## Run locally

This is a static site. Use any simple local server.

### Python 3

```bash
cd census-surname-lookup
python -m http.server 8000
```

Then open:

```text
http://localhost:8000
```

Do **not** open `index.html` directly via `file://...` because browsers often block `fetch()` for local JSON files in that mode.

## Rebuild the dataset

The checked-in JSON lookup file is derived from the official Census 2020 workbook.

### Option A: build from the official Census workbook (default)

```bash
cd census-surname-lookup
python scripts/build_dataset.py
```

This downloads the official workbook from Census, removes the `ALL OTHER NAMES` aggregate row, and writes:

```text
data/surnames.lookup.json
```

### Option B: build from a local workbook you already downloaded

```bash
python scripts/build_dataset.py --source-xlsx /path/to/Names2020_LastNames_RaceHispanic.xlsx
```

## Data source

Official Census pages and files:

- Census 2020 names page:
  - https://www.census.gov/topics/population/genealogy/data/2020_names.html
- Official workbook containing the complete 2020 last-name table:
  - https://www2.census.gov/topics/genealogy/2020surnames/Names2020_LastNames_RaceHispanic.xlsx
- Census brief for 2020 last names:
  - https://www2.census.gov/library/publications/2026/dec/c2020br-14.pdf

## Assumptions

1. The app uses the published 2020 last-name file only, which includes names occurring **100 or more times**.
2. The app excludes the workbook's `ALL OTHER NAMES` summary row because it is an aggregate bucket, not a surname.
3. Input normalization is intentionally simple and lookup-oriented:
   - uppercase
   - strip diacritics
   - remove spaces
   - remove punctuation/apostrophes/hyphens
   - remove any other non-letter characters

Examples:

- `O'Hara` -> `OHARA`
- `Smith-Jones` -> `SMITHJONES`
- `de la Cruz` -> `DELACRUZ`

4. The app stores the fields needed for the lookup UI in a compact schema-backed JSON payload:
   - `rank`
   - `count`
   - `prop100k`
   - `countwhite`
   - `countblack`
   - `countaian`
   - `countapi`
   - `count2prace`
   - `counthispanic`
5. The UI computes race / Hispanic percentages directly from the official 2020 category counts so the displayed percentages and counts stay aligned.
