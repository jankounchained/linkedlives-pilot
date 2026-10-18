"""Single source of truth for where project data lives (stdlib only).

Data is gitignored and exists only in the MAIN checkout. GSD executors can run in a
git worktree, where data/ does not exist, so the data root is resolved through the
common git dir, which always points at the main checkout. Override with the
LINKING_LAB_DATA environment variable (absolute path of the data directory).

CLI: python scripts/project_paths.py [data|raw|parquet|rendered|outputs]
prints that absolute directory (default: data) and nothing else on stdout.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def main_checkout_root() -> Path:
    """Root of the main checkout (parent of the common git dir); REPO_ROOT without git."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return REPO_ROOT
    if not out:
        return REPO_ROOT
    return Path(out).parent


if "LINKING_LAB_DATA" in os.environ:
    DATA_ROOT = Path(os.environ["LINKING_LAB_DATA"])
else:
    DATA_ROOT = main_checkout_root() / "data"

RAW_DIR = DATA_ROOT / "raw"
DIGIDATA_DIR = RAW_DIR / "digidata_14001"
DIGIDATA_ZIP = DIGIDATA_DIR / "14001.zip"
GUIDE_PDF = DIGIDATA_DIR / "Link_Lives Release 2 Guide (2025).pdf"
LINKING_LAB_DIR = RAW_DIR / "linking_lab"
DWI_XLSX = LINKING_LAB_DIR / "MF_census_1850_1846_cl.xlsx"
DWI_SHEET = "MF_census_1850_1846_cl"
PARQUET_DIR = DATA_ROOT / "parquet"
OUTPUTS_DIR = DATA_ROOT / "outputs"
RENDERED_DIR = DATA_ROOT / "rendered"
DWI_PARQUET = PARQUET_DIR / "dwi_1846_1850.parquet"

CENSUS_YEARS = (1801, 1850, 1860, 1880, 1901)
CENSUS_MEMBER = "Data/CSV/main_datasets/census_{year}__v1__cl.csv"
GUIDE_MEMBER = "Dokumenter/Link_Lives Release 2 Guide (2025).pdf"


def census_parquet(year: int) -> Path:
    return PARQUET_DIR / f"census_{year}.parquet"


_CLI_DIRS = {
    "data": DATA_ROOT,
    "raw": RAW_DIR,
    "parquet": PARQUET_DIR,
    "rendered": RENDERED_DIR,
    "outputs": OUTPUTS_DIR,
}

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "data"
    if which not in _CLI_DIRS:
        print(f"usage: project_paths.py [{'|'.join(_CLI_DIRS)}]", file=sys.stderr)
        sys.exit(2)
    print(_CLI_DIRS[which])
