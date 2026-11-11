"""
Spark check for the full panel — Big Data wildfire project (CSCI 6686).

What this proves: PySpark can read the finished 10-year panel and the
row count matches what the panel script printed when it built the file.
This is the same idea as the Step 1 Spark proof, but on the real panel
instead of the one-year FWI test file.

In plain words: build_panel.py already counted the rows with Pandas.
This script counts them again with Spark. If both agree, we know the
Parquet file is good and Spark can work with it for Step 3 (modelling).
If they disagree, something is wrong with the file — find out before
training any model on it.

Run from the project folder on your Mac, with the virtual environment
activated (see README.md):
    python src/data/check_panel_spark.py

Prerequisites (already done for Step 1):
    pip install -r requirements.txt
    Java 17 (Spark needs it)

Input file (built by build_panel.py on 11 Nov 2026):
    data/processed/panel_2015-2024.parquet  (272.1 MB)

Expected result (measured 11 Nov 2026 from the panel build output):
    4,672,823 rows
    fire_next_day = 1 on 11,307 rows (0.242%)
    fire_same_day = 1 on 11,344 rows (diagnostic only — not the target)
    Rows with any FWI code missing: 0
    Columns: date, latitude, longitude, FFMC, DMC, DC, ISI, BUI, FWI,
             DSR, fire_next_day, fire_same_day
"""

from pathlib import Path

# This file lives at src/data/check_panel_spark.py, so the project root is
# two levels up: src/data -> src -> project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PANEL_FILE = PROJECT_ROOT / "data" / "processed" / "panel_2015-2024.parquet"

EXPECTED_ROWS = 4_672_823
EXPECTED_FIRE_NEXT_DAY = 11_307
EXPECTED_FIRE_SAME_DAY = 11_344


def spark_check() -> dict:
    """Spark reads the panel Parquet file and counts rows and labels."""
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, sum as spark_sum

    spark = (
        SparkSession.builder.appName("wildfire-panel-check")
        .master("local[*]")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    df = spark.read.parquet(str(PANEL_FILE))

    print("Spark schema:")
    df.printSchema()
    print("First 5 rows:")
    df.show(5)

    n = df.count()
    print(f"Spark row count: {n:,}  (expected {EXPECTED_ROWS:,})")

    labels = df.agg(
        spark_sum(col("fire_next_day")).alias("fire_next_day"),
        spark_sum(col("fire_same_day")).alias("fire_same_day"),
    ).collect()[0]
    print(
        f"fire_next_day = 1 on {labels['fire_next_day']:,} rows "
        f"(expected {EXPECTED_FIRE_NEXT_DAY:,})"
    )
    print(
        f"fire_same_day = 1 on {labels['fire_same_day']:,} rows "
        f"(expected {EXPECTED_FIRE_SAME_DAY:,})"
    )

    # Any row missing one of the seven FWI codes? The build said 0.
    fwi_cols = ["FFMC", "DMC", "DC", "ISI", "BUI", "FWI", "DSR"]
    missing = df.filter(
        " OR ".join(f"{c} IS NULL" for c in fwi_cols)
    ).count()
    print(f"Rows with any FWI code missing: {missing:,}  (expected 0)")

    spark.stop()
    return {
        "rows": n,
        "fire_next_day": labels["fire_next_day"],
        "fire_same_day": labels["fire_same_day"],
        "missing": missing,
    }


if __name__ == "__main__":
    if not PANEL_FILE.exists():
        raise SystemExit(
            f"Missing panel file: {PANEL_FILE}\n"
            "Build it first:\n"
            "  python src/data/build_panel.py"
        )

    result = spark_check()

    ok = (
        result["rows"] == EXPECTED_ROWS
        and result["fire_next_day"] == EXPECTED_FIRE_NEXT_DAY
        and result["fire_same_day"] == EXPECTED_FIRE_SAME_DAY
        and result["missing"] == 0
    )
    if ok:
        print("PASS — Spark reads the full panel and every count matches "
              "the build. Step 3 (modelling) can start.")
    else:
        print("MISMATCH — at least one count differs from the panel build. "
              "Do not start modelling until the panel file is checked.")
