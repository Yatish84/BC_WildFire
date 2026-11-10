# BC Wildfire Occurrence — Big Data Analytics Project Plan

**Course:** FDU Vancouver, CSCI 6686 Big Data Analytics (Dr. Salma Noor)
**Team:** Bhupinder Bhattarai (2103283) · Yatish Karkera (2148179)
**Status:** Starting from zero on 9 Nov 2026. This file is the living plan — it is updated as we brainstorm and as decisions are made.
**Final submission:** 9 Dec 2026
**Presentation:** 10 Dec 2026

**Goal, in plain words:** demonstrate how to manage genuinely large data with a distributed tool (PySpark), and then analyse it with machine learning — not just run a model on a small CSV.

---

## Change log

| Date | Change |
|---|---|
| 9 Nov 2026 | First plan written from `bhupinder_&_yatish.docx`. Deliverable 1 (proposal + slides, due 29 Oct) was AI-generated from the in-class form and is not treated as a reliable record. |
| 9 Nov 2026 | **Question corrected:** Yatish clarified the intended question is **occurrence prediction, not escalation**. The in-class form worded it as "will a detected fire escalate past 200 ha?" — that is not what the team meant to answer. Escalation is kept only as a stretch analysis. |
| 9 Nov 2026 | **Spatial unit approved:** a map of BC divided into grid squares (0.25°, about 25 km), predicting which squares are at risk tomorrow — not fire centres. Primary weather source is therefore ERA5 gridded FWI, not station aggregation. |
| 9 Nov 2026 | **ERA5 source resolved:** Zenodo NRCan FWI files end in 2018 and are global (~440 MB/year/variable), so they cannot cover 2015–2024. **ERA5-FWI-SN chosen instead** — Canada-only, 1950–2025, ~25 MB/file, 70 files ≈ 1.7 GB for 2015–2024, verified by opening the 2023 FWI file. See Appendix B. Plan §2.1 and §1.4 updated to match; the Bhupinder brief was rewritten to the corrected grid version (see `workspace/big-data-bhupinder-brief.md`). |
| 9 Nov 2026 | **Literature:** added the peer-reviewed paper describing ERA5-FWI-SN — Benoit et al., *Earth Syst. Sci. Data*, 18, 5995–6015, 2026 (doi: 10.5194/essd-18-5995-2026) — as literature item 3 in §6 and as the full citation in the data-source readme §2. The paper's dataset DOI (10.5683/SP3/4B18XZ) is the one already in the plan. |

---

## 1. The research question

**Using the daily weather information available for an area — the Fire Weather Index (FWI) system codes, including the antecedent drought codes (DC, DMC) — can we predict whether a wildfire is likely to occur in that area on a given day?**

In the form Yatish approved on 9 Nov 2026:

> A map of BC divided into squares, predicting which squares are at risk tomorrow.

### 1.1 What we are predicting

- **Unit of analysis:** one **grid square × day**. Not one fire. Every square, every day, gets a row — including the many days where nothing happened.
- **Grid square:** 0.25° latitude × 0.25° longitude, about 25 km × 25 km. BC is divided into these squares; squares that are mostly ocean or outside BC are dropped in the audit.
- **Target:** `≥1 wildfire started in that square on that day` (yes / no). Binary classification.
- **Timing:** the primary task is **1-day-ahead** prediction. Weather up to today is used to predict a fire **tomorrow**. Using same-day weather to "predict" a fire that already started that day is not a prediction — it is describing the same day. Same-day association is a diagnostic only, not the main result.
- **Predictors:** daily FWI system codes for that square — FWI, FFMC, DMC, DC, ISI, BUI — on the day and lagged (1, 3, 7, 14 days before), plus season/month and the square's location (latitude, longitude). Soil moisture and temperature are phase 2 only (see Section 2).

### 1.2 Why a square, not an exact point

A single exact latitude/longitude is too fine. Weather is not measured at every point, and a fire almost never starts at exactly the same coordinates twice, so the probability for one exact point on one day would be near zero, always. A square aggregates enough history for the model to learn from, while still giving a useful map.

### 1.3 Supporting questions

1. Which FWI codes, and which look-back window (1, 3, 7, 14 days), carry the most signal for next-day occurrence?
2. Does the model work equally well across BC, or does it miss fires in some regions (e.g. north vs south, coastal vs interior)?
3. How much faster / more memory-efficient is the PySpark pipeline than a single-machine Pandas baseline as the data grows?

### 1.4 Scope

- **Geography:** British Columbia.
- **Period:** fire seasons (April–October), **2015–2024** — confirmed workable by the audit on 9 Nov 2026, because ERA5-FWI-SN covers 1950–2025 (see Appendix B). Yatish approved this period as the starting point; Bhupinder still to agree. Extend to 2000–2024 only if the first version works and time allows.
- **Stretch goal:** if BC works early, extend to Alberta / western Canada. Not a dependency.
- **Secondary / stretch analysis:** the in-class form's original escalation question — for fires that did start, did they exceed 200 ha, given the weather before the report date? Only after the occurrence pipeline is complete.

---

## 2. Datasets and sources

All links were verified live on 9 Nov 2026 unless noted otherwise. Record the exact URL, access date, file name, size, row count and date range for each dataset in the audit — do not quote counts from the in-class form as fact until you have counted them.

### 2.1 Primary datasets

| # | Dataset | What it is for | Source |
|---|---|---|---|
| 1 | **NFDB fire points** — Canadian National Fire Database, fire point data | The **labels**. One row per real fire, with latitude, longitude, report date (`REP_DATE`), size (`SIZE_HA`) and cause. A fire's lat/lon puts it into a grid square; its date marks that square-day as "fire". | CWFIS / Natural Resources Canada — https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_pnt/current_version/ — `NFDB_point_txt.zip` (24 MB) or `NFDB_point_shp.zip` (40 MB). Use the full point file, not the large-fires-only file. |
| 2 | **ERA5-FWI-SN gridded FWI** — daily gridded Canadian FWI System indices from ERA5 reanalysis | The **main weather input**. Daily FFMC, DMC, DC, ISI, BUI, FWI and DSR for every 0.25° grid square, every day. This is what gives every square its weather, even where there are no weather stations. | UQAM ESCER, via Borealis Dataverse — DOI 10.5683/SP3/4B18XZ — Canada-only NetCDF, one file per variable per year, ~25 MB/file; 70 files ≈ 1.7 GB for 2015–2024. Verified 9 Nov 2026 by opening the 2023 FWI file (see Appendix B). **Do not use the Zenodo NRCan dataset (record 3626193) — its files end in 2018.** |
| 3 | **ERA5 weather and soil moisture** — Copernicus Climate Data Store | **Phase 2 inputs only.** Temperature, humidity, wind, precipitation and soil moisture, per square per day. Add these only after the FWI-only model works. | Copernicus / ECMWF — https://cds.climate.copernicus.eu/ |

### 2.2 Checking and cross-check datasets

| # | Dataset | What it is for | Source |
|---|---|---|---|
| 4 | **CWFIS FWI station observations** (`fwi_obs`) | **Validation.** Real station measurements of the FWI system (tens of millions of station-days; e.g. the 2010s file is 806 MB). Use to check the gridded FWI data against reality, not as the main input for the map. | CWFIS / Natural Resources Canada — https://cwfis.cfs.nrcan.gc.ca/downloads/fwi_obs/ — decade files, e.g. `cwfis_fwi2010s.csv`, `cwfis_fwi2020s.csv.bz2`. Station list: `cwfis_allstn2025.csv`. |
| 5 | **BC Wildfire Fire Incident Locations — Historical** | **Cross-check.** BC-only incident points, plus fire centre / fire zone boundaries for drawing the map. Note: it mixes real fires with suspected fires, nuisance fires and smoke chases, and its coordinates are EPSG:3005 (BC Albers), not lat/lon — reproject before use. | BC Data Catalogue — https://catalogue.data.gov.bc.ca/dataset/bc-wildfire-fire-incident-locations-historical |

### 2.3 Sources to avoid

- **Kaggle wildfire CSVs** (small US / global fire datasets): usually a few thousand rows, no FWI codes, no Canadian coverage. They would weaken the Big Data justification.
- **NASA FIRMS hotspots alone:** satellite detections, not confirmed fires with a report date. Good for a map, not for labelling square-days.

---

## 3. What "Big Data" means here

Do not claim all five Vs. Prove the ones that are true:

- **Volume:** the gridded FWI data covers every square in BC, every day, for years — millions of square-days. The station observations are tens of millions of rows / hundreds of MB per decade file. The modelling table itself is large, unlike a fire-centre version (which would be only about 55,000 region-days).
- **Variety:** NetCDF grids + tab-delimited text + compressed CSV (.bz2) + shapefile / KML. Different schemas, different coordinate systems (BC Albers vs lat/lon), different date formats.
- **Veracity:** missing station readings, delayed `REP_DATE`s, fires with 0.0 lat/lon or plotting outside Canada, ambiguous dates, grid cells with no land. The audit must quantify these.
- **Velocity:** honest answer is *low* — this project uses historical archives, not a live stream. Say that plainly in the report.
- **Value:** a daily risk map helps fire centres prepare crews and equipment for tomorrow — but only if the model is honest about where it misses fires.

### 3.1 The Big Data experiment (required by the course)

Compare **the same** preparation + aggregation workload in PySpark vs single-machine Pandas, at **25%, 50% and 100%** of the audited records. Same machine, same input, same operations, repeated runs. Measure execution time, peak memory and scaling efficiency. Hypothesis only (not a conclusion in advance): Spark may be slower on the smallest slice and faster as data grows. This experiment, not the model accuracy, is what makes the project a Big Data project.

---

## 4. Pipeline

```
ERA5 gridded FWI (BC squares, daily)      NFDB fire points (BC, report dates)
        │                                            │
        ▼                                            ▼
  Ingest (Spark reads NetCDF,               Ingest (Spark reads .txt,
  partitioned by year)                       no full decompress needed)
        │                                            │
        ▼                                            ▼
  Clean: check grid coverage,               Clean: drop 0.0 coords,
  parse dates, flag missing cells           outside-BC, missing REP_DATE,
                                            dedupe
        │                                            │
        ▼                                            ▼
  Build lag features per square-day:        Assign each fire to its
  FWI / FFMC / DMC / DC / ISI / BUI        grid square + report date
  today + 1 / 3 / 7 / 14-day means
        │                                            │
        └──────────────┬─────────────────────────────┘
                       ▼
        Build the square-day panel:
        every BC land square × every day
        (fire season, Apr–Oct)
        label = ≥1 fire started in that
        square the NEXT day (1-day-ahead)
        features = FWI codes today + lags,
        month, lat, lon
                       │
                       ▼
        Train / validation / test — TIME-ordered
        (train ≤2021, validate 2022–23, test 2024)
        — never shuffle randomly, never use
        weather after the prediction day (leakage)
                       │
                       ▼
        Models (PySpark MLlib): logistic regression
        (baseline, interpretable) → decision tree →
        random forest. Baseline: always predict "no fire".
                       │
                       ▼
        Evaluate: precision, recall, F1, PR-AUC,
        confusion matrix, false-negative rate
        by region + by year. Calibration check.
        Map: predicted risk per square for
        example high-risk days.
                       │
                       ▼
        Scaling experiment (Spark vs Pandas)
        + visualisations + final report / slides
```

### 4.1 Key technical decisions (write these down in the audit)

- **Grid:** 0.25° squares. Confirm the exact number of BC land squares in the audit.
- **Period:** fire season April–October, starting 2015–2024. Winter days add mostly "no fire" rows and little signal.
- **Lag features:** DC and DMC build up over weeks, so include 7- and 14-day means, not just day-0 values. For the 1-day-ahead task, all features must come from day t or earlier to predict day t+1.
- **Class imbalance:** most square-days have no fire (well over 99%). Use class weights, and judge by recall on fire days and PR-AUC — never by overall accuracy alone.
- **Leakage rule:** no weather from after the prediction day, no same-day fire information in the features, no future days in training.
- **Reproducibility:** one repo, fixed Spark/Python versions, random seeds, a README with exact download URLs + dates, and scripts that re-run from raw downloads to the panel.

---

## 5. Models and evaluation

| Model | Role | Why |
|---|---|---|
| Always predict "no fire" | Baseline | Tells you what accuracy-without-skill looks like; any model must beat it on recall for fire days, not just accuracy. |
| Logistic regression (regularised, PySpark MLlib) | Interpretable baseline | Coefficients show which FWI codes matter; easy to explain in the presentation. |
| Decision tree | Interpretable non-linear model | Shows thresholds (e.g. FWI above X + DC above Y). |
| Random forest | Main candidate | Usually strongest on tabular data; feature importance for the discussion. |

**Metrics:** precision, recall (especially recall on fire days — a missed fire day is the costly error), F1, PR-AUC, confusion matrix, calibration.

**By-group:** false-negative rate by region (north / south / coastal / interior) and by year, to answer the fairness question — is the model less reliable in some parts of BC?

**If the model is weak, that is still a result.** A documented, fairly evaluated model with honest regional failure analysis scores better than an inflated accuracy number. Do not tune the threshold on the test set.

---

## 6. Literature

Deliverable 1 requires ≥8 relevant sources, ≥5 peer-reviewed, IEEE style, preferably recent. Three solid ones so far:

1. P. Jain et al., "Drivers and impacts of the record-breaking 2023 wildfire season in Canada," *Nature Communications*, vol. 15, 2024.
2. C. C. Hanes et al., "Fire-regime changes in Canada over the last half century," *Canadian Journal of Forest Research*, vol. 49, no. 3, 2019.
3. C. Benoit, J. Durand, P. Gachon, J. Boucher, and Y. Boulanger, "A daily gridded dataset of the Fire Weather Index across Canada, with calculations based on the sun's elevation," *Earth System Science Data*, vol. 18, pp. 5995–6015, 2026, doi: 10.5194/essd-18-5995-2026. This is the peer-reviewed paper describing ERA5-FWI-SN, the main weather source for the model (dataset 2 in §2.1). The authors compared their gridded FWI against CWFIS station FWI for 1 May–30 Sep, 2015–2024, for all available stations — the same window and the same station check planned for Step 1 — so the BC-only check can be compared against their Canada-wide comparison. No validation figure from the paper is quoted here; check its comparison table before citing one.

**Search plan (do this in Step 1, together):** Google Scholar / FDU library — "wildfire prediction FWI machine learning Canada", "grid cell wildfire occurrence prediction", "ERA5 FWI wildfire", "random forest fire occurrence", "Spark wildfire big data". For each paper record: dataset, method, framework, findings, limitations — then write the comparison table the course requires. Do not cite a paper you have not at least read the abstract + methods of.

---

## 7. Timeline — 9 Nov to 10 Dec (4 weeks, starting from zero)

| When | What | Who (proposed) | Done when… |
|---|---|---|---|
| **9–12 Nov** | **Step 1 — Data audit.** Download ERA5 gridded FWI + NFDB point file. Count squares, rows and fires, check fields, check BC coverage, check missingness. Confirm grid, period and scope in writing. Set up repo + Spark environment and prove it runs. | Both together (this is the learning step — do not split it) | A one-page audit note with real counts + a Spark job that reads one FWI file and counts rows. |
| **13–18 Nov** | **Step 2 — Cleaning + panel.** Grid assignment, FWI cleaning, lag features, square-day panel with 1-day-ahead labels, saved as Parquet. | Bhupinder: data preparation + documentation | Panel exists, with a data-quality log: % fires dropped and why, % squares with missing FWI. |
| **19–25 Nov** | **Step 3 — Modelling.** Baseline + logistic regression + decision tree + random forest in PySpark MLlib, time-ordered splits. | Yatish: modelling + benchmarking | All four models trained and evaluated on the validation set; no test-set peeking yet. |
| **26 Nov–2 Dec** | **Step 4 — Evaluation + scaling experiment.** Final test evaluation, by-region false negatives, calibration, risk maps for example days, Spark vs Pandas at 25/50/100%. | Both: evaluation + writing | Scaling table + evaluation tables complete, with repeated runs. |
| **3–8 Dec** | **Step 5 — Report + slides.** Final report (Deliverable 2), charts, pipeline diagram, risk maps, limitations + ethics section. | Both: writing + presentation | Report draft done 6 Dec, so 7–8 Dec is buffer, not writing. |
| **9 Dec** | Final submission | — | Submitted. |
| **10 Dec** | Presentation | Both | Presented. |

### 7.1 Risks and mitigations

1. **Gridded FWI files are bigger / messier than expected** → start with 2015–2024, fire season only; extend backwards only if time allows. The audit decides this, not optimism.
2. **Station coverage is uneven / gridded data has gaps in the north** → report coverage per region; cross-check gridded FWI against station observations (Dataset 4).
3. **Spark setup eats a week** → prove Spark reads one file in Step 1. If local Spark will not run, use Databricks Community Edition / Google Colab with PySpark as a documented fallback — decide by 12 Nov, not 25 Nov.
4. **One partner goes quiet / uneven work** → both must be able to explain the whole pipeline in the presentation; keep a shared task log from day one.
5. **Model performs poorly** → report it honestly with the by-region analysis; a weak-but-honest model with a good scaling experiment is a passable project, a faked strong one is not.

---

## 8. Division of labour

- **Bhupinder:** data preparation + documentation (audit, cleaning rules, grid assignment, data-quality log).
- **Yatish:** modelling + benchmarking (MLlib models, evaluation, Spark vs Pandas experiment).
- **Both:** evaluation, writing, presentation — and both must understand the whole pipeline end to end.

**Working method for learning (what Yatish asked for):** do Step 1 together, in the open, one notebook at a time — explain the idea in plain English first, then build it, run it, and check the result together. No background scripts that Yatish has not seen run.

---

## 9. Decisions still open

1. **Period / source — resolved by the audit, Bhupinder to agree:** 2015–2024, fire season April–October, ERA5-FWI-SN (see Appendix B). Yatish approved the grid version; Bhupinder has not yet confirmed it.
2. **Environment:** local PySpark on your Macs, or Databricks Community / Colab — what do you both already have installed?
3. **Repo:** where will the code live (GitHub, shared folder)? Who creates it?
4. **Phase 2 variables:** add ERA5 soil moisture / temperature after the FWI-only model works, or keep it FWI-only?

---

---

## Appendix A — NFDB audit (9 Nov 2026, checked from the real file)

- **File downloaded:** `NFDB_point_txt.zip` (24 MB) from https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_pnt/current_version/
- **File inside:** `NFDB_point_20260811.txt`, 79.4 MB, **448,618 fires** (plus header), years 1930–2025, plus 95 rows with year −999 (unknown).
- **BC:** 156,570 fires in total; **15,308 in 2015–2024**, of which 14,980 in Apr–Oct. By year 2015–2024: 1,863 / 1,068 / 1,349 / 2,089 / 834 / 668 / 1,649 / 1,783 / 2,280 / 1,725. Causes in BC 2015–2024: Natural/lightning 9,697, Human 5,322, Unknown 289. Fires over 200 ha in BC 2015–2024: 849. No BC 2015–2024 rows have 0.0 lat/lon or a missing `REP_DATE`.
- **Columns (24):** see the table in the chat reply of 9 Nov 2026. The columns we actually use for the grid model are `LATITUDE`, `LONGITUDE`, `REP_DATE` (to label the square-day), plus `SRC_AGENCY` (filter to BC), `SIZE_HA` and `CAUSE` (descriptive / stretch analysis only). Columns that are mostly empty in the full file — `ATTK_DATE` (99.8% missing), `NAT_PARK` (99.0%), `PRESCRIBED` (99.6%), `CFS_NOTE2` (99.8%), `RESPONSE` (85.0%), `FIRENAME` (84.6%), `PROTZONE` (81.8%) — are not used.

*Sources checked 9 Nov 2026: CWFIS NFDB download index and FWI observation index (live directory listings), CWFIS data-services how-to, BC Data Catalogue incident-locations page, Zenodo ERA5 FWI record 3626193. Record counts in the in-class form (400k+ fires, 50M+ weather records, 1980–2020) are treated as claims to verify in the audit, not as facts.*

## Appendix B — ERA5 gridded FWI audit (9 Nov 2026, resolved: ERA5-FWI-SN chosen)

**Decision resolved 9 Nov 2026: use ERA5-FWI-SN for 2015–2024. Do not use the Zenodo dataset.**

- **Zenodo index record:** https://zenodo.org/records/3626193 (published 23 Jan 2020, v1.0). It holds only metadata + a download script — the actual data live in 14 separate sub-records, one per variable (FFMC, DMC, DC, ISI, BUI, FWI, DSR) × two DC start-up methods (default DC=15, and overwintered DC).
- **Coverage — why Zenodo was rejected:** the overwintered FWI record (https://zenodo.org/records/3539654, DOI 10.5281/zenodo.3539654) runs **1979–2018 only** — 40 annual files, 17.7 GB in total for FWI alone. There is no 2019–2024 file. File sizes (overwintered FWI, global, per year): 2015: 455.9 MB; 2016: 461.6 MB; 2017: 457.9 MB; 2018: 437.9 MB.
- **ERA5-FWI-SN (chosen):** DOI 10.5683/SP3/4B18XZ, UQAM ESCER, Canada-only, 1950–2025, 0.25° (~31 km), solar-noon method, NetCDF + GeoTIFF, one file per variable per year, about 25 MB per file. Variables: FFMC, DMC, DC, ISI, BUI, FWI, DSR, plus small files DSRc, FSL, Onset, WinterOnset. For 2015–2024, the seven main variables are 70 files, about 1.7 GB.
- **Verified by opening a real file, 9 Nov 2026:** `Risque-ESCER_ERA5_FWI_daily_2023_Can_0p25grid.nc` (25 MB, file id 965043). Dimensions: `time` 365 days (1 Jan–31 Dec 2023), `lat` 166 values (83.0° down to 41.75°), `lon` 354 values (−141.0° to −52.75°), one data variable `FWI`, WGS84 / EPSG:4326, 0.25°. BC box (lat 48–60°, lon −139° to −114°): 4,949 cells, 2,925 non-missing on 18 Aug 2023; Kelowna cell FWI 25.3 on 18 Aug 2023, NaN on 15 Jan 2023 (FWI is not calculated outside the fire season). BC box, all of 2023: 501,266 non-missing values out of 1,806,385 cell-days.
- **Panel size estimate (updated):** about 2,900 BC land squares × 214 fire-season days × 10 years ≈ 6.2M square-days before dropping missing values. Still a real Big Data panel.
- **Alternative not chosen:** CEMS Fire Danger Indices (Copernicus, DOI 10.24381/cds.0e89c522, daily, 0.25°, global, 1940–present) — also covers 2019–2024, but needs a free CDS account + API, unlike the open ERA5-FWI-SN download.
