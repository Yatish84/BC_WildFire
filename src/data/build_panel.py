"""
Step 2 — Build the square-day panel. Big Data wildfire project (CSCI 6686).

Decision confirmed by Yatish, 2026-11-10: a fire is assigned to a
square by rounding its latitude/longitude to the NEAREST 0.25-degree
grid point (see load_fire_square_days). Each grid point is the centre
of its square, so the fire belongs to the square whose centre it is
closest to. The alternative (floor to the cell below) was explained
and not chosen.

What this builds, in plain words:
  One row per BC grid square per day (fire season, Apr-Oct, 2015-2024),
  with the seven FWI codes for that day, plus a label that says whether
  a real fire started in that same square the NEXT day (1-day-ahead).
  That joined table — about 4.9 million rows — is what the model trains on.

Why the panel looks like this:
  - Squares are the 0.25-degree grid cells from the ERA5-FWI-SN files.
    A square is identified by its latitude/longitude as printed in the
    file (multiples of 0.25, e.g. lat 50.0, lon -119.5).
  - A fire is assigned to a square by rounding its latitude/longitude
    to the nearest 0.25-degree grid point. That is the same grid the
    weather is on, so weather and fires line up exactly.
  - The label is NEXT-day, not same-day: features on day t predict a
    fire on day t+1. Using same-day weather to "predict" a fire that
    already started that day would not be a prediction. The same-day
    fire flag is kept as a separate diagnostic column only.
  - Only squares/days that have FWI data become rows. A square-day
    with no FWI value (ocean, outside Canada, outside fire season)
    has no weather to learn from, so it is not in the panel.

Two traps this script is built to avoid — read these before changing it:
  1. Filter NFDB by SRC_AGENCY == 'BC' FIRST, before using lat/lon.
     The BC lat/lon box (lat 48-60, lon -139 to -114) also contains
     9,524 Alberta fires (2015-2024) plus 548 Parks Canada fires.
     Labelling by box alone would mark BC squares as "fire" for fires
     that were reported in Alberta. Checked 10 Nov 2026 from the real
     NFDB file: box-only = 25,406 fires; SRC_AGENCY='BC' = 15,321.
  2. The audit's "15,308 BC fires" counts by the YEAR column, while
     this script labels by REP_DATE (the report date). Those differ
     by 13 fires (e.g. 2 fires with REP_DATE in Jul 2023 but YEAR=2024).
     REP_DATE is used here because the label is about *when* the fire
     was reported. The script prints both counts so the difference
     stays visible instead of being silently papered over.

Run from the project folder on your Mac, with the virtual environment
activated (see README.md):
    python src/data/build_panel.py                # full build, 2015-2024
    python src/data/build_panel.py --years 2023 --variables FWI
                                                    # small test run first

Prerequisites: the 70 NetCDF files in data/raw/ (see
src/data/download_era5_fwi.py) and NFDB_point_20260811.txt in data/raw/.
Outputs: per-variable flattened Parquet in data/interim/ (resumable —
already-flattened files are skipped), and the finished panel in
data/processed/panel_2015_2024.parquet (or panel_<years>.parquet for a
subset run). Expected full-panel size: ~4.9 million rows.
"""

import argparse
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW = PROJECT_ROOT / "data" / "raw"
INTERIM = PROJECT_ROOT / "data" / "interim"
PROCESSED = PROJECT_ROOT / "data" / "processed"

VARIABLES = ["FFMC", "DMC", "DC", "ISI", "BUI", "FWI", "DSR"]
YEARS = list(range(2015, 2025))

# BC box, as in spark_proof.py. Latitude is stored north-to-south in
# the files, so the slice runs 60 down to 48.
LAT_SLICE = slice(60, 48)
LON_SLICE = slice(-139, -114)
SEASON = ("04-01", "10-31")  # Apr 1 to Oct 31, each year


def nc_path(var: str, year: int) -> Path | None:
    """Find the NetCDF file for one variable and year, or None."""
    proper = RAW / f"Risque-ESCER_ERA5_{var}_daily_{year}_Can_0p25grid.nc"
    if proper.exists():
        return proper
    # The Spark-proof file kept its short name (FWI 2023 only).
    legacy = RAW / "ERA5FWISN_FWI_2023.nc"
    if var == "FWI" and year == 2023 and legacy.exists():
        return legacy
    return None


def flatten_one(var: str, year: int, force: bool = False) -> Path:
    """Flatten one NetCDF file to Parquet (BC box, fire season only).

    Same steps as spark_proof.py, so the counts should match there:
    FWI 2023 must give 494,049 rows. The date is stored as text
    ("2023-08-18") because Spark refuses nanosecond timestamps.
    """
    import xarray as xr

    out = INTERIM / f"{var}_{year}_bc.parquet"
    if out.exists() and not force:
        print(f"  {var} {year}: already flattened, skipping")
        return out
    nc_file = nc_path(var, year)
    if nc_file is None:
        raise SystemExit(f"Missing NetCDF file for {var} {year} in {RAW}")
    ds = xr.open_dataset(nc_file)
    bc = ds.sel(lat=LAT_SLICE, lon=LON_SLICE)
    bc = bc.sel(time=slice(f"{year}-{SEASON[0]}", f"{year}-{SEASON[1]}"))
    df = bc[var].to_dataframe().reset_index()
    df = df.dropna(subset=[var])
    df = df.rename(columns={"time": "date", "lat": "latitude", "lon": "longitude"})
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df.to_parquet(out, index=False)
    print(f"  {var} {year}: {len(df):,} rows -> {out.name}")
    return out


def load_fire_square_days() -> set[tuple[str, float, float]]:
    """BC fires as (date, lat_grid, lon_grid) — one entry per square-day.

    Filter order matters (see trap 1 in the header): agency first,
    then date, then the lat/lon box as a sanity check only.
    """
    nfdb = RAW / "NFDB_point_20260811.txt"
    if not nfdb.exists():
        raise SystemExit(f"Missing NFDB file: {nfdb}")
    fires = pd.read_csv(
        nfdb,
        usecols=["SRC_AGENCY", "LATITUDE", "LONGITUDE", "REP_DATE", "YEAR"],
        low_memory=False,
    )
    n_total = len(fires)
    fires = fires[fires["SRC_AGENCY"] == "BC"]
    fires = fires.dropna(subset=["REP_DATE"])
    fires["date"] = pd.to_datetime(fires["REP_DATE"]).dt.strftime("%Y-%m-%d")
    # Sanity check: every BC-agency fire should sit inside the BC box.
    in_box = (
        fires["LATITUDE"].between(48, 60) & fires["LONGITUDE"].between(-139, -114)
    )
    print(f"  NFDB: {n_total:,} fires in file; {len(fires):,} BC-agency fires "
          f"with a report date ({(~in_box).sum()} outside the BC box)")
    fires = fires[in_box]
    # Round each fire to the nearest 0.25-degree grid point.
    fires["latitude"] = (fires["LATITUDE"] * 4).round() / 4
    fires["longitude"] = (fires["LONGITUDE"] * 4).round() / 4
    # Several fires can start in the same square on the same day; the
    # label is ">=1 fire", so keep one row per square-day.
    square_days = set(
        zip(fires["date"], fires["latitude"], fires["longitude"])
    )
    print(f"  NFDB: {len(square_days):,} distinct fire square-days "
          f"(all dates in the file, 1930-2025)")
    return square_days


def build_panel(variables, years, force: bool = False) -> Path:
    """Flatten, join, label, and save the panel. Returns its path."""
    INTERIM.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    print("Step 1 — flatten NetCDF files (BC box, Apr-Oct):")
    flat: dict[tuple[str, int], Path] = {}
    for var in variables:
        for year in years:
            flat[(var, year)] = flatten_one(var, year, force=force)

    print("Step 2 — join the seven variables on date + square:")
    # Two steps, in this order — getting them mixed up was a real bug
    # (fixed 11 Nov 2026). First, STACK the years for each variable:
    # FFMC 2015 + FFMC 2016 + ... are rows of the same table, one on
    # top of the other (pd.concat), not columns to merge. Only then,
    # JOIN the seven variables side by side on date + square, so each
    # square-day gets all seven codes in one row. Merging year-by-year
    # instead tries to merge FFMC 2015 with FFMC 2016, and both have a
    # column called FFMC — Pandas refuses the duplicate
    # (MergeError: duplicate columns 'FFMC_x', 'FFMC_y').
    per_variable = []
    for var in variables:
        year_frames = [pd.read_parquet(flat[(var, year)]) for year in years]
        stacked = pd.concat(year_frames, ignore_index=True)
        print(f"  {var}: {len(stacked):,} rows across {len(years)} years")
        per_variable.append(stacked)
    panel = per_variable[0]
    for df in per_variable[1:]:
        panel = panel.merge(df, on=["date", "latitude", "longitude"], how="outer")
    print(f"  joined panel: {len(panel):,} rows")
    print(f"  rows with any FWI code missing: "
          f"{panel[variables].isna().any(axis=1).sum():,}")

    print("Step 3 — add the fire labels (1-day-ahead):")
    fire_days = load_fire_square_days()
    # A fire on day t+1 labels the panel row for day t. Shift the fire
    # dates back by one day, then look them up against panel rows.
    panel["date_dt"] = pd.to_datetime(panel["date"])
    panel["next_date"] = (panel["date_dt"] + pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d")
    panel["fire_next_day"] = [
        1 if (d, lat, lon) in fire_days else 0
        for d, lat, lon in zip(panel["next_date"], panel["latitude"], panel["longitude"])
    ]
    panel["fire_same_day"] = [
        1 if (d, lat, lon) in fire_days else 0
        for d, lat, lon in zip(panel["date"], panel["latitude"], panel["longitude"])
    ]
    panel = panel.drop(columns=["date_dt", "next_date"])
    n_pos = int(panel["fire_next_day"].sum())
    print(f"  fire_next_day = 1 on {n_pos:,} of {len(panel):,} rows "
          f"({100 * n_pos / len(panel):.3f}%)")
    print(f"  fire_same_day = 1 on {int(panel['fire_same_day'].sum()):,} rows "
          f"(diagnostic only — not the target)")

    # Coverage check — do NOT skip this. Some real fires have no FWI
    # row to learn from (FWI is not calculated for some squares/days,
    # mostly early in the season and on coastal squares). Those fires
    # cannot appear as positives in the panel, so they cap recall.
    # Tested on 2023 (FWI only), test run 10 Nov 2026: 200 of 1,993
    # fire square-days (10.0%) had no panel row the day before the fire.
    panel_keys = set(zip(panel["date"], panel["latitude"], panel["longitude"]))
    lo = f"{min(years)}-04-01"
    hi = f"{max(years)}-11-01"  # Nov 1 fires label the Oct 31 rows
    in_range = [d for d in fire_days if lo <= d[0] <= hi]
    missing_prev = [
        d for d in in_range
        if ((pd.to_datetime(d[0]) - pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
            d[1], d[2]) not in panel_keys
    ]
    print(f"  coverage: {len(in_range):,} fire square-days in {lo} to {hi}; "
          f"{len(missing_prev):,} ({100 * len(missing_prev) / max(len(in_range), 1):.1f}%) "
          f"have no panel row the day before the fire — those fires "
          f"cannot be predicted from this panel as built")

    years_label = f"{min(years)}-{max(years)}" if len(years) > 1 else str(years[0])
    out = PROCESSED / f"panel_{years_label}.parquet"
    panel.to_parquet(out, index=False)
    print(f"Saved: {out} ({out.stat().st_size / 1e6:.1f} MB)")
    print("  Columns:", ", ".join(panel.columns))
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", type=int, nargs="+", default=YEARS,
                        help="years to build, e.g. --years 2023")
    parser.add_argument("--variables", nargs="+", default=VARIABLES,
                        help="variables to include, e.g. --variables FWI")
    parser.add_argument("--force", action="store_true",
                        help="re-flatten files already in data/interim/")
    args = parser.parse_args()

    missing = [(v, y) for v in args.variables for y in args.years
               if nc_path(v, y) is None]
    if missing:
        print("Downloads not complete — these files are missing from data/raw/:")
        for var, year in missing:
            print(f"  {var} {year}: "
                  f"Risque-ESCER_ERA5_{var}_daily_{year}_Can_0p25grid.nc")
        print("Run src/data/download_era5_fwi.py first (it resumes where "
              "it left off), then re-run this script.")
        raise SystemExit(1)

    build_panel(args.variables, args.years, force=args.force)
    print("Done. Next: check the panel in Spark, then Step 3 modelling.")
