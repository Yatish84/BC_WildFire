"""
Step 1 Spark proof — Big Data wildfire project (CSCI 6686).

What this proves: PySpark can read the flattened FWI data and count rows.
PySpark cannot read NetCDF directly, so there are two steps:

  1. xarray flattens the 2023 FWI NetCDF file (a stack of daily maps)
     into one row per square per day, saved as Parquet.
  2. Spark reads that Parquet file and counts the rows.

Run from the project folder on your Mac, with the virtual environment
activated (see README.md):
    python src/data/spark_proof.py

Prerequisites (install once):
    pip install -r requirements.txt
    Java 17 (Spark needs it):  brew install openjdk@17

Input file (download first, into data/raw/):
    ERA5FWISN_FWI_2023.nc  (25 MB)
    https://borealisdata.ca/api/access/datafile/965043
    (Dataverse file id 965043 — Risque-ESCER_ERA5_FWI_daily_2023_Can_0p25grid.nc)
    Or from the terminal, in the project folder:
    curl -L -o data/raw/ERA5FWISN_FWI_2023.nc \
        https://borealisdata.ca/api/access/datafile/965043

Expected result (measured 9 Nov 2026 from the real 2023 file):
    494,049 rows — FWI, BC box only (lat 48-60, lon -139 to -114),
    fire season Apr-Oct, missing (NaN) values dropped.
    Parquet file: about 6.6 MB, written to data/interim/.
If your count differs, do not ignore it — the flattening step is wrong
somewhere (wrong box, wrong months, or NaNs kept).
"""

from pathlib import Path

# This file lives at src/data/spark_proof.py, so the project root is
# two levels up: src/data -> src -> project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW = PROJECT_ROOT / "data" / "raw"
INTERIM = PROJECT_ROOT / "data" / "interim"
NC_FILE = RAW / "ERA5FWISN_FWI_2023.nc"  # 25 MB, download first (see above)
PARQUET_FILE = INTERIM / "fwi_2023_bc_fire_season.parquet"

EXPECTED_ROWS = 494_049


def flatten_to_parquet() -> int:
    """Step 1: NetCDF -> Parquet, BC box, fire season only."""
    import xarray as xr

    ds = xr.open_dataset(NC_FILE)
    # One data variable in this file: FWI. Dimensions: time x lat x lon.
    bc = ds.sel(lat=slice(60, 48), lon=slice(-139, -114))
    bc = bc.sel(time=slice("2023-04-01", "2023-10-31"))
    df = bc["FWI"].to_dataframe().reset_index()
    df = df.dropna(subset=["FWI"])
    df = df.rename(columns={"time": "date", "lat": "latitude", "lon": "longitude"})
    # Store the date as plain text ("2023-08-18"), not as a timestamp.
    # Why: xarray/pandas write timestamps in nanoseconds, and Spark
    # refuses Parquet files with nanosecond timestamps
    # ([PARQUET_TYPE_ILLEGAL] INT64 (TIMESTAMP(NANOS,false))).
    # We only need the day, not a time of day, so text loses nothing
    # and Spark reads it without complaint.
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df.to_parquet(PARQUET_FILE, index=False)
    return len(df)


def spark_count() -> int:
    """Step 2: Spark reads the Parquet file and counts rows."""
    from pyspark.sql import SparkSession

    spark = (
        SparkSession.builder.appName("wildfire-spark-proof")
        .master("local[*]")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    df = spark.read.parquet(str(PARQUET_FILE))
    n = df.count()
    print("Spark schema:")
    df.printSchema()
    print("First 5 rows:")
    df.show(5)
    spark.stop()
    return n


if __name__ == "__main__":
    if not NC_FILE.exists():
        raise SystemExit(
            f"Missing input file: {NC_FILE}\n"
            "Download it first (see the instructions at the top of this file):\n"
            "  curl -L -o data/raw/ERA5FWISN_FWI_2023.nc "
            "https://borealisdata.ca/api/access/datafile/965043"
        )

    n_flat = flatten_to_parquet()
    print(f"Flattened rows (xarray): {n_flat:,}  (expected {EXPECTED_ROWS:,})")

    n_spark = spark_count()
    print(f"Spark row count: {n_spark:,}  (expected {EXPECTED_ROWS:,})")

    if n_flat == EXPECTED_ROWS and n_spark == EXPECTED_ROWS:
        print("PASS — Spark proof complete. Step 1 can be ticked off.")
    else:
        print("MISMATCH — counts do not match the measured 494,049. Check the "
              "BC box, the Apr-Oct window, and whether NaNs were dropped.")
