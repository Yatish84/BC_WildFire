"""
Download the ERA5-FWI-SN files for Step 2 — Big Data wildfire project.

What it downloads: the 7 main FWI variables (FFMC, DMC, DC, ISI, BUI,
FWI, DSR) for 2015-2024 — 70 NetCDF files, about 1.7 GB in total —
from the Borealis Dataverse (DOI 10.5683/SP3/4B18XZ).

How downloading works here (worth understanding):
  - Dataverse gives every file a numeric ID. To download a file you
    ask for https://borealisdata.ca/api/access/datafile/<id> and the
    server redirects you to the actual file. No account or API key
    is needed — these files are open.
  - Doing this by hand in a browser would mean 70 separate clicks,
    and nobody could reproduce exactly what you downloaded. A script
    with the full list of IDs in it is the reproducible version:
    run it again and you get the same 70 files.
  - The script skips any file that is already on disk with the
    right size, so you can stop it and re-run it safely — it picks
    up where it left off instead of starting over.

Run from the project folder, with the virtual environment activated:
    python src/data/download_era5_fwi.py

Files go to data/raw/ and are git-ignored (they are far too big for
GitHub). FWI 2023 is already there if you ran the Spark proof — the
script will skip it.
"""

import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW = PROJECT_ROOT / "data" / "raw"

BASE_URL = "https://borealisdata.ca/api/access/datafile/"

# (variable, year, dataverse file id, size in bytes, filename)
# File list taken from the Dataverse API on 10 Nov 2026.
FILES = [
    ("BUI", 2015, 977778, 24689755, "Risque-ESCER_ERA5_BUI_daily_2015_Can_0p25grid.nc"),
    ("BUI", 2016, 977676, 24732153, "Risque-ESCER_ERA5_BUI_daily_2016_Can_0p25grid.nc"),
    ("BUI", 2017, 977780, 23979948, "Risque-ESCER_ERA5_BUI_daily_2017_Can_0p25grid.nc"),
    ("BUI", 2018, 977649, 20731112, "Risque-ESCER_ERA5_BUI_daily_2018_Can_0p25grid.nc"),
    ("BUI", 2019, 977651, 23602160, "Risque-ESCER_ERA5_BUI_daily_2019_Can_0p25grid.nc"),
    ("BUI", 2020, 965124, 22758363, "Risque-ESCER_ERA5_BUI_daily_2020_Can_0p25grid.nc"),
    ("BUI", 2021, 965125, 24261469, "Risque-ESCER_ERA5_BUI_daily_2021_Can_0p25grid.nc"),
    ("BUI", 2022, 965123, 24387060, "Risque-ESCER_ERA5_BUI_daily_2022_Can_0p25grid.nc"),
    ("BUI", 2023, 965122, 25434907, "Risque-ESCER_ERA5_BUI_daily_2023_Can_0p25grid.nc"),
    ("BUI", 2024, 965126, 26079941, "Risque-ESCER_ERA5_BUI_daily_2024_Can_0p25grid.nc"),
    ("DC", 2015, 977143, 24213547, "Risque-ESCER_ERA5_DC_daily_2015_Can_0p25grid.nc"),
    ("DC", 2016, 977061, 24332379, "Risque-ESCER_ERA5_DC_daily_2016_Can_0p25grid.nc"),
    ("DC", 2017, 977027, 23530748, "Risque-ESCER_ERA5_DC_daily_2017_Can_0p25grid.nc"),
    ("DC", 2018, 977028, 20399821, "Risque-ESCER_ERA5_DC_daily_2018_Can_0p25grid.nc"),
    ("DC", 2019, 977093, 23199218, "Risque-ESCER_ERA5_DC_daily_2019_Can_0p25grid.nc"),
    ("DC", 2020, 965067, 22388935, "Risque-ESCER_ERA5_DC_daily_2020_Can_0p25grid.nc"),
    ("DC", 2021, 965071, 23794604, "Risque-ESCER_ERA5_DC_daily_2021_Can_0p25grid.nc"),
    ("DC", 2022, 965069, 23939062, "Risque-ESCER_ERA5_DC_daily_2022_Can_0p25grid.nc"),
    ("DC", 2023, 965073, 24906529, "Risque-ESCER_ERA5_DC_daily_2023_Can_0p25grid.nc"),
    ("DC", 2024, 965077, 25543645, "Risque-ESCER_ERA5_DC_daily_2024_Can_0p25grid.nc"),
    ("DMC", 2015, 977386, 24650853, "Risque-ESCER_ERA5_DMC_daily_2015_Can_0p25grid.nc"),
    ("DMC", 2016, 977251, 24715248, "Risque-ESCER_ERA5_DMC_daily_2016_Can_0p25grid.nc"),
    ("DMC", 2017, 977254, 23961589, "Risque-ESCER_ERA5_DMC_daily_2017_Can_0p25grid.nc"),
    ("DMC", 2018, 977355, 20719079, "Risque-ESCER_ERA5_DMC_daily_2018_Can_0p25grid.nc"),
    ("DMC", 2019, 977388, 23606105, "Risque-ESCER_ERA5_DMC_daily_2019_Can_0p25grid.nc"),
    ("DMC", 2020, 965093, 22741645, "Risque-ESCER_ERA5_DMC_daily_2020_Can_0p25grid.nc"),
    ("DMC", 2021, 965091, 24264525, "Risque-ESCER_ERA5_DMC_daily_2021_Can_0p25grid.nc"),
    ("DMC", 2022, 965090, 24363180, "Risque-ESCER_ERA5_DMC_daily_2022_Can_0p25grid.nc"),
    ("DMC", 2023, 965082, 25369084, "Risque-ESCER_ERA5_DMC_daily_2023_Can_0p25grid.nc"),
    ("DMC", 2024, 965095, 26034858, "Risque-ESCER_ERA5_DMC_daily_2024_Can_0p25grid.nc"),
    ("DSR", 2015, 978023, 25782655, "Risque-ESCER_ERA5_DSR_daily_2015_Can_0p25grid.nc"),
    ("DSR", 2016, 977956, 25842812, "Risque-ESCER_ERA5_DSR_daily_2016_Can_0p25grid.nc"),
    ("DSR", 2017, 977875, 25084938, "Risque-ESCER_ERA5_DSR_daily_2017_Can_0p25grid.nc"),
    ("DSR", 2018, 978024, 21653586, "Risque-ESCER_ERA5_DSR_daily_2018_Can_0p25grid.nc"),
    ("DSR", 2019, 977877, 24653588, "Risque-ESCER_ERA5_DSR_daily_2019_Can_0p25grid.nc"),
    ("DSR", 2020, 965134, 23776260, "Risque-ESCER_ERA5_DSR_daily_2020_Can_0p25grid.nc"),
    ("DSR", 2021, 965131, 25362751, "Risque-ESCER_ERA5_DSR_daily_2021_Can_0p25grid.nc"),
    ("DSR", 2022, 965140, 25532362, "Risque-ESCER_ERA5_DSR_daily_2022_Can_0p25grid.nc"),
    ("DSR", 2023, 965133, 26575285, "Risque-ESCER_ERA5_DSR_daily_2023_Can_0p25grid.nc"),
    ("DSR", 2024, 965141, 27243214, "Risque-ESCER_ERA5_DSR_daily_2024_Can_0p25grid.nc"),
    ("FFMC", 2015, 976789, 23472934, "Risque-ESCER_ERA5_FFMC_daily_2015_Can_0p25grid.nc"),
    ("FFMC", 2016, 976862, 23548448, "Risque-ESCER_ERA5_FFMC_daily_2016_Can_0p25grid.nc"),
    ("FFMC", 2017, 976819, 22802046, "Risque-ESCER_ERA5_FFMC_daily_2017_Can_0p25grid.nc"),
    ("FFMC", 2018, 976865, 19691676, "Risque-ESCER_ERA5_FFMC_daily_2018_Can_0p25grid.nc"),
    ("FFMC", 2019, 976902, 22479109, "Risque-ESCER_ERA5_FFMC_daily_2019_Can_0p25grid.nc"),
    ("FFMC", 2020, 965055, 21675626, "Risque-ESCER_ERA5_FFMC_daily_2020_Can_0p25grid.nc"),
    ("FFMC", 2021, 965056, 23111232, "Risque-ESCER_ERA5_FFMC_daily_2021_Can_0p25grid.nc"),
    ("FFMC", 2022, 965053, 23212810, "Risque-ESCER_ERA5_FFMC_daily_2022_Can_0p25grid.nc"),
    ("FFMC", 2023, 965061, 24162767, "Risque-ESCER_ERA5_FFMC_daily_2023_Can_0p25grid.nc"),
    ("FFMC", 2024, 965066, 24801826, "Risque-ESCER_ERA5_FFMC_daily_2024_Can_0p25grid.nc"),
    ("FWI", 2015, 976634, 25485530, "Risque-ESCER_ERA5_FWI_daily_2015_Can_0p25grid.nc"),
    ("FWI", 2016, 976593, 25537781, "Risque-ESCER_ERA5_FWI_daily_2016_Can_0p25grid.nc"),
    ("FWI", 2017, 976595, 24749015, "Risque-ESCER_ERA5_FWI_daily_2017_Can_0p25grid.nc"),
    ("FWI", 2018, 976732, 21376913, "Risque-ESCER_ERA5_FWI_daily_2018_Can_0p25grid.nc"),
    ("FWI", 2019, 976759, 24374744, "Risque-ESCER_ERA5_FWI_daily_2019_Can_0p25grid.nc"),
    ("FWI", 2020, 965022, 23509694, "Risque-ESCER_ERA5_FWI_daily_2020_Can_0p25grid.nc"),
    ("FWI", 2021, 965040, 25050483, "Risque-ESCER_ERA5_FWI_daily_2021_Can_0p25grid.nc"),
    ("FWI", 2022, 965050, 25187730, "Risque-ESCER_ERA5_FWI_daily_2022_Can_0p25grid.nc"),
    ("FWI", 2023, 965043, 26205385, "Risque-ESCER_ERA5_FWI_daily_2023_Can_0p25grid.nc"),
    ("FWI", 2024, 965024, 26890863, "Risque-ESCER_ERA5_FWI_daily_2024_Can_0p25grid.nc"),
    ("ISI", 2015, 977519, 25216758, "Risque-ESCER_ERA5_ISI_daily_2015_Can_0p25grid.nc"),
    ("ISI", 2016, 977447, 25292541, "Risque-ESCER_ERA5_ISI_daily_2016_Can_0p25grid.nc"),
    ("ISI", 2017, 977598, 24517133, "Risque-ESCER_ERA5_ISI_daily_2017_Can_0p25grid.nc"),
    ("ISI", 2018, 977599, 21167694, "Risque-ESCER_ERA5_ISI_daily_2018_Can_0p25grid.nc"),
    ("ISI", 2019, 977478, 24134676, "Risque-ESCER_ERA5_ISI_daily_2019_Can_0p25grid.nc"),
    ("ISI", 2020, 965107, 23291478, "Risque-ESCER_ERA5_ISI_daily_2020_Can_0p25grid.nc"),
    ("ISI", 2021, 965098, 24817552, "Risque-ESCER_ERA5_ISI_daily_2021_Can_0p25grid.nc"),
    ("ISI", 2022, 965109, 24949386, "Risque-ESCER_ERA5_ISI_daily_2022_Can_0p25grid.nc"),
    ("ISI", 2023, 965110, 25965320, "Risque-ESCER_ERA5_ISI_daily_2023_Can_0p25grid.nc"),
    ("ISI", 2024, 965106, 26640414, "Risque-ESCER_ERA5_ISI_daily_2024_Can_0p25grid.nc"),
]


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    total = len(FILES)
    print(f"Downloading {total} files (~1.7 GB) into {RAW}")
    for i, (var, year, file_id, size, filename) in enumerate(FILES, start=1):
        dest = RAW / filename
        # Skip files already downloaded correctly — safe to re-run.
        if dest.exists() and dest.stat().st_size == size:
            print(f"[{i}/{total}] {filename} — already there, skipping")
            continue
        print(f"[{i}/{total}] {filename} ({size / 1e6:.1f} MB) ... ", end="", flush=True)
        # The Dataverse URL redirects to the real file; urlretrieve follows it.
        urllib.request.urlretrieve(BASE_URL + str(file_id), dest)
        actual = dest.stat().st_size
        if actual != size:
            print(f"WARNING: size mismatch — got {actual} bytes, expected {size}")
        else:
            print("done")
    print("All downloads finished. Check with: ls -lh data/raw/ | head")


if __name__ == "__main__":
    main()
