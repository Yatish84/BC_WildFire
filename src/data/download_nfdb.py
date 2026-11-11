"""
Download the NFDB fire points for Step 2 — Big Data wildfire project.

What it downloads: the National Fire Database point file from
CWFIS / Natural Resources Canada — one row per confirmed wildfire,
with latitude, longitude, report date and agency. This is the
labels file: it says which squares had a fire start on which day.

  URL: https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_pnt/current_version/NFDB_point_txt.zip
  Zip: about 24 MB (25,043,218 bytes, checked 10 Nov 2026)
  Inside: NFDB_point_20260811.txt, about 76 MB, 448,618 fires
          (1930-2025; BC 2015-2024 = 15,308, audited 9 Nov 2026)

Why a script, not just the two curl/unzip commands:
  - Same reason as the ERA5 download script. A command typed once
    in a terminal is gone; a script in src/data/ is a record of
    exactly where the data came from, and Bhupinder (or Dr. Noor,
    or future-you) can re-run it and get the same file.
  - It checks its own work: after unzipping it confirms the .txt
    file is there and counts its rows, so a half-downloaded or
    empty file does not silently flow into the panel.
  - It skips the download if the zip is already on disk with the
    right size, so re-running it is safe.

One honest caveat: the file inside the zip is dated
(NFDB_point_20260811.txt) and CWFIS updates it, so a future
download may contain a differently dated file with a slightly
different fire count. The script finds whatever NFDB_point_*.txt
is inside the zip instead of hard-coding the date, and prints the
row count so you can see if it changed.

Run from the project folder, with the virtual environment activated:
    python src/data/download_nfdb.py

Files go to data/raw/ and are git-ignored.
"""

import urllib.request
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW = PROJECT_ROOT / "data" / "raw"

URL = "https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_pnt/current_version/NFDB_point_txt.zip"
ZIP_FILE = RAW / "NFDB_point_txt.zip"
EXPECTED_ZIP_BYTES = 25_043_218  # checked 10 Nov 2026; warn, don't fail, if it changes


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)

    if ZIP_FILE.exists() and ZIP_FILE.stat().st_size == EXPECTED_ZIP_BYTES:
        print(f"{ZIP_FILE.name} already there ({EXPECTED_ZIP_BYTES:,} bytes), skipping download")
    else:
        print(f"Downloading {URL} ...")
        urllib.request.urlretrieve(URL, ZIP_FILE)
        actual = ZIP_FILE.stat().st_size
        print(f"Downloaded {actual:,} bytes")
        if actual != EXPECTED_ZIP_BYTES:
            print(f"WARNING: expected {EXPECTED_ZIP_BYTES:,} bytes — the file on "
                  "the server may have been updated. Check the row count below.")

    print("Unzipping ...")
    with zipfile.ZipFile(ZIP_FILE) as z:
        z.extractall(RAW)
        print("Files in the zip:", ", ".join(z.namelist()))

    txt_files = sorted(RAW.glob("NFDB_point_*.txt"))
    if not txt_files:
        raise SystemExit("ERROR: no NFDB_point_*.txt found in data/raw/ after unzipping")
    txt = txt_files[0]
    # Count rows without loading the whole file into memory.
    with open(txt, encoding="utf-8", errors="replace") as f:
        n_rows = sum(1 for _ in f) - 1  # minus the header row
    print(f"{txt.name}: {txt.stat().st_size / 1e6:.1f} MB, {n_rows:,} fire rows")
    print("Done. NFDB is in data/raw/.")


if __name__ == "__main__":
    main()
