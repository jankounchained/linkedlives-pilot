"""Convert the locally provided source files to all-String parquet.

Run: uv run python scripts/prepare_data.py [--only dwi] [--check]

No download code (D-04): source files must already be in data/raw/, see README.md,
section "Data (not in git)". Every column is stored as String and nothing is coerced
(D-06); later scripts cast explicitly and report parse failures as findings.
The script prints only paths, counts and dtypes, never rows.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import polars as pl

import project_paths


def require_sources(paths: list[Path]) -> None:
    """Exit with status 2, naming every missing source and pointing to the README."""
    missing = [p for p in paths if not p.exists()]
    if not missing:
        return
    for p in missing:
        print(f"missing source file: {p}", file=sys.stderr)
    print(
        'see README.md, section "Data (not in git)", for where it comes from',
        file=sys.stderr,
    )
    sys.exit(2)


def write_atomic(frame: pl.DataFrame, target: Path) -> None:
    """Write parquet to a pid-suffixed temp file, then rename it onto target.

    A final data/parquet path is therefore either absent or a complete parquet
    from one finished write, even if the run is interrupted or two runs overlap.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.parent / f"{target.name}.{os.getpid()}.tmp"
    try:
        frame.write_parquet(tmp)
        tmp.replace(target)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def convert_dwi() -> None:
    require_sources([project_paths.DWI_XLSX])
    frame = pl.read_excel(
        project_paths.DWI_XLSX,
        sheet_name=project_paths.DWI_SHEET,
        infer_schema_length=0,
    )
    # fastexcel with infer_schema_length=0 already yields String; cast defensively.
    # The leftover Column1 is kept unchanged, nothing else is coerced (D-06).
    non_string = [c for c, t in frame.schema.items() if t != pl.String]
    if non_string:
        frame = frame.with_columns(pl.col(non_string).cast(pl.String))
    write_atomic(frame, project_paths.DWI_PARQUET)
    print(
        f"wrote {project_paths.DWI_PARQUET} rows={frame.height} cols={frame.width}"
    )


def _expected_outputs(only: str | None) -> list[Path]:
    outs: list[Path] = []
    if only in (None, "dwi"):
        outs.append(project_paths.DWI_PARQUET)
    return outs


def _check_parquet(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, "missing"
    try:
        lazy = pl.scan_parquet(path)
        rows = lazy.select(pl.len()).collect().item()
        schema = lazy.collect_schema()
    except Exception as exc:  # report, never crash the check
        return False, f"unreadable: {type(exc).__name__}"
    all_string = all(t == pl.String for t in schema.values())
    ok = all_string
    detail = f"rows={rows} cols={len(schema)} all_string={all_string}"
    if path == project_paths.DWI_PARQUET:
        ok = ok and rows == 83414 and len(schema) == 22
    return ok, detail


def check_outputs(only: str | None) -> int:
    failed = False
    for path in _expected_outputs(only):
        ok, detail = _check_parquet(path)
        print(f"{'OK' if ok else 'FAIL'} {path.name} {detail}")
        failed = failed or not ok
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", choices=["dwi"], help="convert only one source")
    parser.add_argument(
        "--check", action="store_true", help="validate outputs, write nothing"
    )
    args = parser.parse_args()

    if args.check:
        return check_outputs(args.only)
    convert_dwi()
    return 0


if __name__ == "__main__":
    sys.exit(main())
