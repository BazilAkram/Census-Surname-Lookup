# Census 2010 Surname Lookup

Tiny static web app for looking up a surname in the **official U.S. Census 2010 surname data**.

A user types a surname, the app normalizes it to roughly match the Census surname processing rules, and the UI returns:

- normalized surname
- count
- rank

If a surname is absent from the published file, the app does **not** show `0`. It shows:

> Not found in the 2010 Census surname file; this usually means fewer than 100 occurrences.

## Why this app uses 2010, not 2020

This app uses the official **2010 Census surname** product. The Census Bureau has public surname products for 2010 and 2000; there is no equivalent public official 2020 surname table bundled here.

## Project structure

```text
.
├── app.js
├── data/
│   └── surnames-2010.lookup.json
├── index.html
├── scripts/
│   └── build_dataset.py
├── styles.css
└── README.md
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

The checked-in JSON lookup file is derived from the official Census 2010 surname CSV.

### Option A: build from the official Census ZIP (default)

```bash
cd census-surname-lookup
python scripts/build_dataset.py
```

This downloads the official ZIP from Census, extracts the CSV, removes the `ALL OTHER NAMES` aggregate row, and writes:

```text
data/surnames-2010.lookup.json
```

### Option B: build from a local CSV you already downloaded

```bash
python scripts/build_dataset.py --source-csv /path/to/Names_2010Census.csv
```

## Data source

Official Census pages and files:

- Census genealogy page for 2010 surnames:
  - https://www.census.gov/topics/population/genealogy/data/2010_surnames.html
- Census developer page for the 2010 surname product:
  - https://www.census.gov/data/developers/data-sets/surnames/2010.html
- Official ZIP containing the complete surname files:
  - https://www2.census.gov/topics/genealogy/2010surnames/names.zip
- Technical documentation:
  - https://www2.census.gov/topics/genealogy/2010surnames/surnames.pdf

## Assumptions

1. The app uses the published 2010 surname file only, which includes surnames occurring **100 or more times**.
2. The app excludes the CSV's `ALL OTHER NAMES` summary row because it is an aggregate bucket, not a surname.
3. Input normalization is intentionally simple and lookup-oriented:
   - uppercase
   - strip diacritics
   - remove spaces
   - remove punctuation/apostrophes/hyphens
   - remove any other non-letter characters

Examples:

- `O’Hara` → `OHARA`
- `Smith-Jones` → `SMITHJONES`
- `de la Cruz` → `DELACRUZ`

4. The app stores only the fields needed for this lookup UI: surname → `[rank, count]`.
