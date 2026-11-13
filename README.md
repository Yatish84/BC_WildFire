# BC Wildfire — Predicting Wildfire Occurrence in British Columbia

**Course project:** CSCI 6686/6886 Big Data Analytics, Fairleigh Dickinson University (Vancouver), Fall 2026
**Instructor:** Dr. Salma Noor
**Team:** Yatish Karkera (2148179) and Bhupinder Bhattarai (2103283)
**Final submission:** 9 December 2026 · **Presentation:** 10 December 2026

## The question

Using daily weather information — the Fire Weather Index (FWI) system codes, including the antecedent drought codes (DC, DMC) — can we predict whether a wildfire is likely to occur in a given area on a given day?

In concrete form, the version this project builds:

> **A map of British Columbia divided into 0.25° squares (about 25 km), predicting which squares are at risk of a wildfire tomorrow — 1 day ahead.**

Each square × day is one row. The label is 1 if at least one wildfire started in that square the next day, 0 otherwise. Escalation (whether a fire that started grows past 200 ha) is kept only as a stretch analysis, not the main question.

## Why this is a Big Data project

The fire list on its own is not big: the NFDB file has 448,618 fires Canada-wide, and only 15,308 in BC in 2015–2024. The volume comes from the weather side — about 2,900 BC land squares × 214 fire-season days × 10 years ≈ **6.2 million square-days** of gridded FWI data — plus tens of millions of station observations used for validation. The project therefore demonstrates managing genuinely large data with a distributed tool (PySpark) and then analysing it with machine learning, not just running a model on a small CSV.

## Data

Only two datasets feed the model. The others are for validation, cross-checking, or a possible later phase.

| Dataset | Role | Source |
|---|---|---|
| **ERA5-FWI-SN gridded FWI** | Main weather input — daily FFMC, DMC, DC, ISI, BUI, FWI, DSR for every 0.25° square | ESCER, UQAM, via Borealis Dataverse, DOI 10.5683/SP3/4B18XZ. Canada-only, 1950–present, NetCDF, ~25 MB per file; 70 files ≈ 1.7 GB for 2015–2024. Described in Benoit et al., *Earth Syst. Sci. Data* 18, 5995–6015, 2026, doi:10.5194/essd-18-5995-2026. |
| **NFDB fire points** | Labels — one row per confirmed fire, with latitude, longitude and report date | CWFIS / Natural Resources Canada. 448,618 fires Canada-wide; 15,308 in BC 2015–2024 (14,980 in Apr–Oct). |
| CWFIS station FWI observations | Validation only — checks the gridded FWI against real station measurements | CWFIS / Natural Resources Canada. 2024 file: 632,186 rows Canada-wide, 82,965 from 370 BC stations. |
| BC Wildfire fire incident locations (historical) | Cross-check only — compares against the NFDB labels | BC Data Catalogue. 27,835 incidents 2015–2024, of which 15,319 are real fires (vs NFDB's 15,308); 45% are non-fire types such as nuisance fires and smoke chases, so it is not used as training data. |
| ERA5 weather and soil moisture | Phase 2 only — after the FWI-only model works | Copernicus Climate Data Store. Mostly duplicates what is already inside the FWI codes; soil moisture is the only genuinely new signal. |

**Data is not committed to this repo.** The files are large (gigabytes) and some are downloaded on demand. See `docs/data-source-readme.md` for the full audit — real counts from files actually opened, in plain English — and `src/data/` for the download scripts.

Do **not** use the Zenodo "Global Fire Weather Indices" dataset as the gridded FWI source: its files end in 2018 and are global (~440 MB each), so they cannot cover 2019–2024.

## Tech stack

- **Python** — the language for everything
- **Apache Spark via PySpark (MLlib)** — cleaning, joining, aggregating, and modelling at scale. Models: logistic regression, decision tree, random forest, vs an always-predict-"no fire" baseline
- **Pandas** — only as the single-machine comparison in the Spark vs Pandas scaling experiment (25% / 50% / 100% of the data)
- **xarray + netCDF4** — opening NetCDF files and flattening them to rows (PySpark cannot read NetCDF directly)
- **Parquet** — the storage format for the flattened data and the joined square-day panel
- **Jupyter** — exploration and the audit notebooks
- No database is used: files on disk plus Spark DataFrames are the storage. See the plan for why.

## Project structure

```
BC_WildFire/
├── README.md                 # this file
├── requirements.txt          # Python dependencies
├── data/
│   ├── raw/                  # downloaded files, exactly as received — never edit
│   ├── interim/              # intermediate outputs (flattened per-variable tables)
│   ├── processed/            # the joined square-day panel (Parquet) the model trains on
│   └── external/             # reference data (e.g. fire-centre/zone boundaries)
├── notebooks/
│   └── 01_data_audit.ipynb   # Step 1: exploring and counting each dataset
├── src/
│   ├── data/                 # download, cleaning and panel-building scripts
│   ├── features/             # lag features (1/3/7/14-day means, 1-day-ahead labels)
│   ├── models/               # training scripts (logistic regression, tree, forest)
│   └── evaluation/           # metrics, by-region false negatives, risk maps
├── reports/
│   └── figures/              # charts and risk maps for the report and slides
└── docs/
    ├── plan.md               # the full project plan (living document)
    └── data-source-readme.md # every data source, in plain English, with audit numbers
```

**Why this layout?** A data-science project has three kinds of things that must never be mixed up: data as it arrived (`data/raw`, read-only), code that transforms it (`src/`, versioned), and results (`reports/`). Notebooks are for exploring and learning; anything used twice moves into `src/` so it can be re-run. If you change `data/raw`, you can no longer prove what your results came from — so you don't.

## Getting started

```bash
# 1. Clone the repo
git clone https://github.com/Yatish84/BC_WildFire.git
cd BC_WildFire

# 2. Create and activate a virtual environment (Python 3.11+)
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Java is required for Spark (check with: java -version)
#    macOS: brew install openjdk@17

# 5. Download the data (see docs/data-source-readme.md for the sources)
#    The scripts in src/data/ fetch the NFDB file and the ERA5-FWI-SN files
#    into data/raw/. Large files are git-ignored and never committed.
```

## Workflow (the five steps)

| When | Step | What |
|---|---|---|
| 9–12 Nov | **1 — Data audit** | Download each dataset, open the real files, count rows/columns/missing values, check BC coverage. Prove Spark reads one FWI file. |
| 13–18 Nov | **2 — Cleaning + panel** | Grid assignment, FWI cleaning, lag features, square-day panel with 1-day-ahead labels, saved as Parquet. |
| 19–25 Nov | **3 — Modelling** | Baseline + logistic regression + decision tree + random forest in PySpark MLlib, time-ordered splits (train ≤2021, validate 2022–23, test 2024). |
| 26 Nov–2 Dec | **4 — Evaluation + scaling** | Final test evaluation, false negatives by region and year, risk maps, Spark vs Pandas at 25/50/100%. |
| 3–8 Dec | **5 — Report + slides** | Draft done 6 Dec; 7–8 Dec is buffer. |

## Evaluation

Time-ordered splits only — never shuffle randomly, and never use weather after the prediction day. Judged on recall on fire days, precision, F1 and PR-AUC (never accuracy alone — well over 99% of square-days have no fire), plus the false-negative rate by region (north / south / coastal / interior) and by year. A weak but honestly evaluated model is a reportable result; do not tune the threshold on the test set.

## Status

**Step 1 complete (10 Nov 2026)** — data audit done, and the Spark proof passed: xarray flattened 494,049 rows from the 2023 FWI file and Spark counted 494,049 rows back. Environment is local PySpark on macOS (Java 17).

**Step 2 complete (11 Nov 2026)** — the full square-day panel is built and checked: `data/processed/panel_2015-2024.parquet` (272.1 MB), **4,672,823 rows** — every BC 0.25° square × every fire-season day, 2015–2024 — with all seven FWI codes (FFMC, DMC, DC, ISI, BUI, FWI, DSR) and a 1-day-ahead label. `fire_next_day = 1` on **11,307 rows (0.242%)**; 0 rows have any FWI code missing. Fires are assigned to the nearest 0.25° grid point. Honest limit: 1,676 of 12,983 fire square-days (12.9%) have no panel row the day before the fire, so recall is capped at 87.1% before modelling. Spark re-read the panel and confirmed every count (commit `34572b1`).

**Step 3 in progress** — exploring the panel first (`notebooks/02_exploration.ipynb`): FWI on fire days is much higher than on non-fire days (median 14.5 vs 2.4), the fire rate climbs smoothly with FWI (0.09% at FWI 0–5 to 1.20% at FWI 30+), and the seven codes carry roughly four or five distinct signals (DMC ≈ BUI, ISI ≈ FWI ≈ DSR; DC is the most independent). Modelling (logistic regression, decision tree, random forest vs always-predict-no-fire baseline) comes next, on time-ordered splits.

## Licence

MIT — see `LICENSE`.
