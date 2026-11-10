# Data Sources — README

**Project:** BC Wildfire Occurrence Prediction (FDU, CSCI 6686 Big Data Analytics)
**Team:** Bhupinder Bhattarai · Yatish Karkera
**Last updated:** 9 Nov 2026 — this file is updated as we brainstorm and audit the data.

This file is written for a layman. No background in wildfires or data science is needed. If a word is unfamiliar, it is explained where it is first used.

---

## The project in one paragraph

We divide British Columbia into squares on a map (about 25 km across). For each square, for each day in fire season, we look at the weather — how hot, dry and windy it was, and how dry the forest fuel had become over the previous weeks. Then we ask the computer: based on all the past days like this, how likely is a wildfire to start in this square tomorrow?

To do that we need two kinds of information: **where fires actually happened in the past**, and **what the weather was like in every square, every day**. The datasets below give us exactly those two things.

---

## How the data fits together

```
Past fires (NFDB)  +  Past weather (ERA5 gridded FWI)
        │                          │
        ▼                          ▼
  Which square, on which day,   What was the weather in
  did a fire start?              that square, that day?
        │                          │
        └──────────┬───────────────┘
                   ▼
        One table: square × day
        weather + "fire? yes / no"
                   │
                   ▼
        Machine-learning model learns
        which weather patterns came
        before a fire
```

The other datasets are for checking our work, not for building the main table.

---

## 1. NFDB fire points — where fires happened

**Full name:** Canadian National Fire Database (NFDB), fire point data
**Who provides it:** Canadian Wildland Fire Information System (CWFIS), Natural Resources Canada
**Link:** https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_pnt/current_version/
**File we downloaded:** `NFDB_point_txt.zip` (24 MB), containing `NFDB_point_20260811.txt` (79 MB)

**In plain English:** a list of almost every wildfire reported in Canada, one row per fire. It is the official record, collected from the provinces, territories and Parks Canada.

**What we checked on 9 Nov 2026:** the file has **448,618 fires**, from 1930 to 2025. In British Columbia alone there are 156,570 fires. In 2015–2024 there are 15,308 BC fires, and 14,980 of those were in fire season (April to October).

**What each column means:**

| Column | Meaning, in plain English |
|---|---|
| NFDBFIREID | A unique ID for the fire, e.g. `BC-2023-2023-C23369` |
| SRC_AGENCY | Which province or territory reported it — `BC`, `AB`, `ON`, and so on. We keep only `BC` |
| NAT_PARK | National park name, if the fire was in a park. Empty in 99% of rows |
| FIRE_ID | The agency's own ID for the fire |
| FIRENAME | The name given to the fire, if it had one. Empty in 85% of rows |
| LATITUDE | How far north the fire was. This puts the fire in a grid square |
| LONGITUDE | How far east/west the fire was. This also puts the fire in a grid square |
| YEAR | The year of the fire. `-999` means the year is unknown (95 rows) |
| MONTH | The month of the fire |
| DAY | The day of the fire |
| REP_DATE | The date the fire was reported. This is the date we use to label the square-day |
| ATTK_DATE | The date crews first attacked the fire. Empty in 99.8% of rows, so we cannot use it |
| OUT_DATE | The date the fire was declared out. Empty in 48% of rows |
| SIZE_HA | The final size of the fire, in hectares. 1 hectare is about the size of a sports field |
| CAUSE | The cause, standardised: `N` = natural / lightning, `H` = human, `U` = unknown |
| CAUSE2 | The cause as the agency originally wrote it, before standardising |
| FIRE_TYPE | The type of fire (for example `Wildfire`, `Surface`, `Ground`). No national standard, empty in 32% of rows |
| RESPONSE | How crews responded, for example `FUL` = full response. Empty in 85% of rows |
| PROTZONE | The protection zone, as the agency wrote it. No national standard, empty in 82% of rows |
| PRESCRIBED | Whether it was a planned, controlled burn (codes 0–4). Empty in 99.6% of rows |
| MORE_INFO | Free-text extra information, for example "NE of Alkali Creek". Empty in 88% of rows |
| CFS_NOTE1 | A note added by the Canadian Forest Service when they put the file together |
| CFS_NOTE2 | A second Forest Service note. Empty in 99.8% of rows |
| ACQ_DATE | The date the data was received from the agency |

**What we actually use:** `LATITUDE` and `LONGITUDE` (which square), `REP_DATE` (which day), and `SRC_AGENCY` (to keep only BC). `SIZE_HA` and `CAUSE` are useful for describing the fires. `SIZE_HA` would also be used if we later look at the stretch question — did a fire grow past 200 hectares?

**Is this file "big data" on its own? No — and that matters.** The downloaded file is 24 MB compressed, 76 MB uncompressed, with 448,618 rows in total. BC on its own is 156,570 rows over all years, 42,305 in 2000–2024, and 15,308 in 2015–2024. A file that size fits easily in a spreadsheet or in Pandas on one machine. The Big Data volume in this project comes from the weather side, not from this list: the ERA5 gridded weather covers every square in BC, every day, for years (millions of square-days), and the CWFIS station observations are tens of millions of rows. This file is the labels; the weather is the volume.

**What to be careful about:** the record is not perfect. Some fires have missing report dates, some dates are delayed by a day or two, and some early records are less reliable. We count and report these problems in the audit instead of hiding them.

---

## 2. ERA5-FWI-SN gridded FWI — what the weather was, in every square

**Full name:** ERA5-FWI-SN — a daily gridded dataset of the Fire Weather Index across Canada
**Who provides it:** ESCER Centre, University of Québec at Montréal (UQAM), using ERA5 weather data from the European Centre for Medium-Range Weather Forecasts (ECMWF)
**Link:** https://doi.org/10.5683/SP3/4B18XZ (Borealis Dataverse)

**The paper that describes this dataset:** C. Benoit, J. Durand, P. Gachon, J. Boucher, and Y. Boulanger, "A daily gridded dataset of the Fire Weather Index across Canada, with calculations based on the sun's elevation," *Earth System Science Data*, vol. 18, pp. 5995–6015, published 25 Aug 2026, https://doi.org/10.5194/essd-18-5995-2026. In plain words: this is the peer-reviewed paper for the main weather source that creates the model. It explains how the gridded FWI was built from hourly ERA5 weather using the sun's position at noon, and it checks the gridded FWI against real station FWI (CWFIS) for 1 May–30 Sep, 2015–2024 — the same check we plan for BC in Step 1, so we can compare our BC result against their Canada-wide one. No figure from their comparison is quoted here; check the paper's comparison table before citing a number.

**In plain English:** for every square on the map, for every day, a set of numbers that describe how dangerous the fire weather was. Unlike weather stations, which only exist in some places, this covers every square — including remote parts of northern BC. That is why it is our main weather source.

**What the numbers mean (the FWI system):**

The Fire Weather Index system turns temperature, humidity, wind and rain into a small set of codes. Think of them as layers of dryness:

| Code | Full name | What it measures, in plain English |
|---|---|---|
| FFMC | Fine Fuel Moisture Code | How dry the thin, surface fuel is — leaves, twigs, needles. Changes fast, day to day. Dry surface fuel catches fire easily |
| DMC | Duff Moisture Code | How dry the loosely packed layer under the surface is. Builds up over about two weeks |
| DC | Drought Code | How dry the deep, compact soil and fuel is. Builds up over weeks. This is the slow drought signal |
| ISI | Initial Spread Index | How fast a fire would spread once it starts, combining wind and the dry surface fuel |
| BUI | Buildup Index | How much fuel is available to burn, combining the DMC and DC |
| FWI | Fire Weather Index | The overall score, combining spread and fuel. High FWI means a fire would be intense and hard to control |
| DSR | Daily Severity Rating | A related score for how severe the day's fire weather was |

**Why the drought codes matter:** a fire is much more likely after weeks without rain than after one hot day. DC and DMC remember that history. That is why we look back 7 and 14 days, not just at today.

**Format:** one NetCDF file per variable per year, Canada only, 0.25° grid (about 25 km), WGS84 lat/lon. Each file has three dimensions — `time` (365 days), `lat` (166 values, 83.0° down to 41.75°), `lon` (354 values, −141.0° to −52.75°) — and one data variable (for example, the FWI file contains only `FWI`).

**What we checked on 9 Nov 2026:** we downloaded the FWI file for 2023 (`Risque-ESCER_ERA5_FWI_daily_2023_Can_0p25grid.nc`, 25 MB) and opened it. It covers 1 Jan–31 Dec 2023, 365 days. In the BC box (lat 48–60°, lon −139° to −114°) there are 4,949 grid cells, of which 2,925 had a value on 18 Aug 2023 — the rest are ocean, outside Canada, or outside the fire season (FWI is not calculated in winter; the Kelowna cell is NaN on 15 Jan 2023 and 25.3 on 18 Aug 2023, in the middle of the 2023 fire season). Across all of 2023, the BC box has 501,266 non-missing values out of 1,806,385 cell-days. For 2015–2024, the seven main variables (FFMC, DMC, DC, ISI, BUI, FWI, DSR) are 70 files totalling about 1.7 GB — large, but manageable, and we subset to BC and fire season before modelling.

**How big is it after flattening? (measured 9 Nov 2026, FWI 2023):** flattening one variable for one year, BC only, fire season (Apr–Oct), gives **494,049 rows** — 21.3 MB as a CSV, 6.6 MB as Parquet. Seven variables × ten years as seven separate flattened tables would be **34.6 million rows in total** — about 461 MB as Parquet, about 1.5 GB as CSV. Joining those seven tables on (date, latitude, longitude) gives one joined panel of **4.94 million rows** for 2015–2024, roughly 150–200 MB as Parquet. The key step is to subset to the BC box *before* flattening: flattening the full Canada grid first would be 21.4 million values per variable per year, and doing that for seven variables over ten years would be tens of gigabytes for no benefit.

**Correction, 9 Nov 2026:** an earlier version of this file listed the Zenodo "Global Fire Weather Indices" dataset (record 3626193) as the primary gridded FWI source. Checking it properly showed it is **not suitable**: its files end in 2018, each annual file is global (not Canada-only) and about 440 MB, so seven variables for ten years would be tens of gigabytes and would still miss 2019–2024. It is removed as a primary source. ERA5-FWI-SN above replaces it. The Zenodo dataset is kept only as a historical reference for pre-2019 work, if ever needed.

---

## 3. ERA5 weather and soil moisture — extra inputs (phase 2 only)

**Full name:** ERA5 hourly data on single levels from 1940 to present
**Who provides it:** Copernicus Climate Change Service (C3S), European Centre for Medium-Range Weather Forecasts (ECMWF)
**Link:** https://cds.climate.copernicus.eu/ (dataset: `reanalysis-era5-single-levels`, DOI 10.24381/cds.adbb2d47)

**In plain English:** the raw weather that the FWI codes are made from, plus soil moisture. It is a reanalysis — past weather recreated by combining past observations with a weather model — so there is a value for every place and every hour, even where no station existed.

**Important: most of this is not new information.** Temperature, humidity, wind and rain are already inside the FWI codes (Section 2). Adding them again adds little. The one genuinely new thing is **soil moisture** — how wet the ground itself is — which the FWI system only approximates through the Drought Code.

**Variables that would matter for us (if we add this in phase 2):**

| Variable (CDS name) | What it is, in plain English |
|---|---|
| `2m_temperature` | Air temperature 2 metres above the ground, in Kelvin (convert to °C). Use the daily maximum |
| `2m_dewpoint_temperature` | Dew point temperature at 2 m. Combined with temperature, this gives relative humidity |
| `total_precipitation` | Total rain (and snow) that fell, in metres. Add up over the day |
| `10m_u_component_of_wind` / `10m_v_component_of_wind` | Wind blowing east-west and north-south, 10 m above the ground. Combined, they give wind speed and direction |
| `volumetric_soil_water_layer_1` | Soil water in the top layer, 0–7 cm deep, in m³/m³ (fraction of the soil that is water). The most relevant layer for surface fuel |
| `volumetric_soil_water_layer_2` | Soil water, 7–28 cm deep |
| `volumetric_soil_water_layer_3` | Soil water, 28–100 cm deep |
| `volumetric_soil_water_layer_4` | Soil water, 100–289 cm deep |
| `soil_temperature_level_1` to `_level_4` | Soil temperature at the same four depths, in Kelvin |
| `snow_depth` / `snow_cover` | How much snow is on the ground. Useful for knowing when the fire season starts and ends |

**Format and access — different from the other datasets:** there is no single zip file to download. You request the data from the Copernicus Climate Data Store, by variable, year, month and area (the BC box), using a free CDS account and the CDS API. The data comes back as NetCDF (or GRIB) files, hourly, on a 0.25° grid — the same grid size as the FWI data, so the squares line up.

**Size — why we must aggregate to daily first:** the data is **hourly**, 24 values per day instead of 1. For the BC box, one variable for one fire season is roughly 25 million hourly values; for ten years it is roughly 250 million values per variable. We would never feed hourly values to the model. The first step is to turn them into daily values in the download or in processing — daily maximum temperature, total daily precipitation, daily mean soil moisture, and so on — which brings each variable back to about 500,000 square-days per year, the same size as the FWI tables.

**Alternative for soil moisture specifically — ERA5-Land:** a land-only version of ERA5, at finer resolution (0.1°, about 11 km), hourly, 1950 to present, DOI 10.24381/cds.68d2bb30. It is better for soil moisture than standard ERA5, because it is designed for land variables. Same CDS access, same need to aggregate to daily.

**What we have not yet audited:** no ERA5 file has been downloaded yet. File sizes, exact variable names and the CDS request itself are still to be checked in Step 1, if we decide to add this in phase 2.

---

## 4. CWFIS station weather observations — checking the gridded data

**Full name:** CWFIS Fire Weather Index observations (`fwi_obs`)
**Who provides it:** CWFIS, Natural Resources Canada
**Link:** https://cwfis.cfs.nrcan.gc.ca/downloads/fwi_obs/

**In plain English:** the same FWI codes, but measured at real weather stations on the ground, instead of calculated for a grid. One row per station per day, at noon local time, with the day's weather and the FWI codes calculated from it. These are real measurements, not a model — which is exactly why they are useful for checking the gridded data.

**What we use it for:** checking, not as the main input. If the gridded data says a square was very dry on a certain day, do the nearby stations agree? If they do not, we need to know why. We do **not** use station data as the main input for the map, because stations do not cover every square — there are about 370 BC stations with data in 2024, versus about 2,925 BC grid squares.

**Files (checked live 9 Nov 2026, directory listing):** decade files, one per decade — `cwfis_fwi2000s.csv` (429 MB), `cwfis_fwi2010s.csv` (806 MB), `cwfis_fwi2020s.csv.bz2` (89 MB compressed) — plus single-year files such as `fwi2024.csv.bz2` (13 MB compressed). The station list is `cwfis_allstn2026.csv` (546 KB, 2,839 stations Canada-wide, 467 in BC), with each station's latitude, longitude, elevation and province. Note: provincial fire-weather station networks are **not** included in these files — only federal / Meteorological Service of Canada stations and a few others.

**Columns (23, from the real 2024 file):** `aes` (station ID), `wmo` (World Meteorological Organization station number), `rep_date` (date and time of the reading, noon), `temp` (temperature, °C), `td` (dew point, °C), `rh` (relative humidity, %), `ws` (wind speed), `wg` (wind gust), `wdir` (wind direction), `pres` (pressure), `vis` (visibility), `precip` (rain, mm), `rndays` (rain days), `sog` (snow on ground), then the calculated codes `ffmc`, `dmc`, `dc`, `bui`, `isi`, `fwi`, `dsr`, plus `opts` and `calcstatus` (notes on how the codes were calculated).

**What we checked on 9 Nov 2026:** we downloaded `fwi2024.csv.bz2` (13 MB) and opened it. It has **632,186 rows** for Canada in 2024. Joining it to the station list, **82,965 rows are from BC stations**, from **370 BC stations** that reported in 2024, covering 1 Jan–31 Dec 2024. **15,835 of those BC rows (about 19%) have no FWI value** — mostly outside the fire season, when the codes are not calculated. The station's latitude and longitude are **not** in the FWI file itself — you have to join it to the station list on the station ID (`aes`) to know where each station is.

**How the check works in practice:** for a given day, take a station's FWI and compare it with the gridded FWI in the square that station sits in. If they track each other closely, the gridded data is trustworthy. If they diverge in a region or a year, that is something to report — and it is also a limit of the model in that region. In concrete steps: (1) join each station to its grid square using the station list's latitude/longitude; (2) pair the station FWI with the gridded FWI for the same square on the same day; (3) measure how close they are — correlation and average difference; (4) break that down by region (north / south / coastal / interior) and by year, so a single overall number does not hide a weak region; (5) report the result as a data-quality finding in the report, not as a model input.

---

## 5. BC Wildfire fire incident locations — a BC-only cross-check

**Who provides it:** Government of British Columbia, BC Data Catalogue
**Link:** https://catalogue.data.gov.bc.ca/dataset/bc-wildfire-fire-incident-locations-historical

**In plain English:** BC's own list of past wildfire incidents, as points on a map. Each point is a place where BC Wildfire Service tracked *something* — a real fire, a suspected fire, a nuisance fire (for example a small fire that was not a wildfire), or a smoke chase (someone reported smoke, crews went to look, and there may have been no fire at all).

**Will it be used to create the model? No.** The model learns from the NFDB fire list, because NFDB only lists confirmed fires, with a report date and a final size. The BC list cannot be used for that job, because it mixes real fires with suspected fires and smoke chases. If we trained on it, the model would learn that some squares had a fire when they did not — it would be learning from wrong answers.

**So what is it used for? A cross-check — a second opinion.** Think of it like this. NFDB says: "there was a fire in this square on 18 August 2023." We then look at the BC list and ask: "did BC Wildfire also record something in that square, around that date?" If the two lists agree most of the time, we can trust our NFDB labels more. If they disagree a lot — for example, if BC lists many fires that NFDB missed, or the dates are often different — that is something we have to report, because it means our labels may be incomplete.

**What it is also used for:** the related BC datasets give the boundaries of BC's fire centres and fire zones (for example, Cariboo, Kamloops, Coastal, Southeast). We use those boundaries to draw the map and to report results by region — for example, "the model caught 80% of fires in the south, but only 50% in the north."

**File details (audited 9 Nov 2026 from a real download):** downloaded from the BC openmaps WFS service (`WHSE_LAND_AND_NATURAL_RESOURCE.PROT_HISTORICAL_INCIDENTS_SP`), 2015–2024, saved as `data/bc_incidents/bc_incidents_2015_2024.geojson` (19 MB). The service returns at most 10,000 records per request, so it was downloaded in three pages and combined — **27,835 incidents in total**. The geometry is in a BC-specific map format (EPSG:3005, BC Albers), but the file also carries `LATITUDE` and `LONGITUDE` fields directly, so no conversion is needed to compare it with NFDB.

**Columns (19):** `FIRE_NUMBER` (e.g. C10376), `FIRE_YEAR`, `RESPONSE_TYPE_DESC` (Full / Modified / Monitor), `IGNITION_DATE`, `FIRE_OUT_DATE`, `FIRE_CAUSE` (Lightning / Person / Unknown), `FIRE_LABEL`, `FIRE_CENTRE` (codes 2–7), `ZONE`, `FIRE_ID`, `FIRE_TYPE`, `INCIDENT_NAME`, `GEOGRAPHIC_DESCRIPTION`, `LATITUDE`, `LONGITUDE`, `CURRENT_SIZE` (hectares), `FEATURE_CODE`, `OBJECTID`, `SE_ANNO_CAD_DATA`.

**What we found in 2015–2024:**

| | Count |
|---|---|
| All incidents | 27,835 |
| Type "Fire" (real fires) | 15,319 |
| All other types | 12,516 (45.0%) — Nuisance Fire 6,298; Smoke Chase 4,024; Field Activity 970; Duplicate 486; Field Activity Other 408; Training 108; Prescribed Fire 107; Unknown 65; plus a few Agency Assist, Fuels Management, Other Emergency, Landslide and Flood |
| Missing ignition date | 9,403 overall — but **0** among "Fire" type; all the missing dates are non-fire types |
| Missing size | 4,757 |
| Size 0 ha | 3,139 |
| Size over 200 ha | 857 |

**The cross-check against NFDB — and it is a good result:** the "Fire" type count, 15,319, is almost identical to the NFDB BC count for 2015–2024, 15,308 — a difference of just 11. Year by year they track closely too (for example 2023: BC 2,296 vs NFDB 2,280; 2024: BC 1,697 vs NFDB 1,725). The over-200-ha counts are close as well (BC 857 vs NFDB 849). That does not prove every fire matches one-to-one — that check still needs to be done, matching by location and date — but at the count level the two lists agree well, which is encouraging for the NFDB labels. The layer is updated on 1 April each year with the previous fire season's data.

---

## Glossary

- **Grid square / cell:** one square of the map, 0.25° (about 25 km) across. The unit we predict for.
- **Square-day:** one square on one day. One row in our main table.
- **NetCDF:** a file format for gridded, multi-dimensional data, used widely in weather and climate science. It is not a table of rows and columns like a CSV. Instead it stores a 3D block of numbers — in our case, time × latitude × longitude — plus a description of itself (what the numbers are, what units, who made the file, what map projection). Think of it as a stack of maps: one map per day, each map is a grid of squares, and each square holds one number. The FWI file for 2023, for example, is 365 maps × 166 latitudes × 354 longitudes, about 21 million numbers, one variable (`FWI`) per file. To use it in a machine-learning model we flatten it: each square-day becomes one row — date, latitude, longitude, FWI value — and we do the same for the other six codes, then join them on date + square.
- **FWI system:** the Canadian Fire Weather Index system — the set of codes in Section 2 that turn weather into fire danger.
- **Antecedent:** what happened before. Antecedent drought means the dryness that built up over the previous days and weeks.
- **Reanalysis (ERA5):** weather recreated for the past by combining past observations with a weather model, so there is a value for every place and every day, even where no station existed.
- **Label:** the answer we train the model to predict — in our case, "did a fire start in this square tomorrow, yes or no?"
- **Leakage:** accidentally giving the model information from the future. For example, using tomorrow's weather to "predict" tomorrow's fire is not a prediction.

---

## Change log

| Date | Change |
|---|---|
| 9 Nov 2026 | File created. NFDB section written from the real downloaded file (`NFDB_point_20260811.txt`, 448,618 fires). ERA5 gridded FWI, ERA5 weather/soil moisture, CWFIS station observations and BC incident locations described from their verified source pages; their audit numbers are still to be added. |
| 9 Nov 2026 | ERA5-FWI-SN audited from a real downloaded file (FWI 2023, 25 MB, opened and checked). Primary gridded FWI source corrected from the Zenodo dataset to ERA5-FWI-SN — the Zenodo files end in 2018 and are global, about 440 MB per file, so they do not cover 2019–2024. |
| 9 Nov 2026 | ERA5 weather and soil moisture section expanded from the CDS documentation: variable names, soil layers, hourly format, CDS API access, and why it is phase 2 only (most of it is already inside the FWI codes; soil moisture is the genuinely new part). No ERA5 file downloaded yet. |
| 9 Nov 2026 | CWFIS station FWI observations audited from a real downloaded file (`fwi2024.csv.bz2`, 13 MB): 632,186 rows Canada-wide in 2024, 82,965 from 370 BC stations, 19% of BC rows with no FWI value. Station list `cwfis_allstn2026.csv`: 2,839 stations Canada-wide, 467 in BC. |
| 9 Nov 2026 | BC Wildfire incident locations audited from a real download (WFS, 2015–2024, 19 MB GeoJSON, 27,835 incidents): "Fire" type 15,319 vs NFDB BC 15,308 — counts agree closely; 45% of incidents are non-fire types (Nuisance Fire 6,298, Smoke Chase 4,024, etc.); missing ignition dates are all in non-fire types. |
| 9 Nov 2026 | Added the full citation for the ERA5-FWI-SN paper — Benoit et al., *Earth Syst. Sci. Data*, 18, 5995–6015, 2026, doi: 10.5194/essd-18-5995-2026 — in §2, with a plain-words note that it is the peer-reviewed description of the main weather source and that its station comparison (1 May–30 Sep, 2015–2024) matches the Step 1 check. Same citation added as literature item 3 in the plan (§6). |
