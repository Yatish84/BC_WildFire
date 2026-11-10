"""
Step 1 Spark proof — Big Data wildfire project (CSCI 6686).

What this proves: PySpark can read the flattened FWI data and count rows.
PySpark cannot read NetCDF directly, so there are two steps:

  1. xarray flattens the 2023 FWI NetCDF file (a stack of daily maps)
     into one row per square per day, saved as Parquet.
  2. Spark reads that Parquet file and counts the rows.

Run from the project folder on your Mac:
    python3 spark_proof.py

Prerequisites (install once):
    pip install xarray netCDF4 pyarrow pyspark
    Java 17 (Spark needs it):  brew install openjdk@17

Expected result (measured 9 Nov 2026 from the real 2023 file):
    494,049 rows — FWI, BC box only (lat 48-60, lon -139 to -114),
    fire season Apr-Oct, missing (NaN) values dropped.
    Parquet file: about 6.6 MB.
If your count differs, do not ignore it — the flattening step is wrong
somewhere (wrong box, wrong months, or NaNs kept).
"""

from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
NC_FILE = DATA / "ERA5FWISN_FWI_2023.nc"  # 25 MB, downloaded 9 Nov 2026
PARQUET_FILE = DATA / "fwi_2023_bc_fire_season.parquet"

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
        raise SystemExit(f"Missing input file: {NC_FILE}")

    n_flat = flatten_to_parquet()
    print(f"Flattened rows (xarray): {n_flat:,}  (expected {EXPECTED_ROWS:,})")

    n_spark = spark_count()
    print(f"Spark row count: {n_spark:,}  (expected {EXPECTED_ROWS:,})")

    if n_flat == EXPECTED_ROWS and n_spark == EXPECTED_ROWS:
        print("PASS — Spark proof complete. Step 1 can be ticked off.")
    else:
        print("MISMATCH — counts do not match the measured 494,049. Check the "
              "BC box, the Apr-Oct window, and whether NaNs were dropped.")
