"""Convert the locally provided source files to all-String parquet.

Run: uv run python scripts/prepare_data.py [--only dwi|census] [--check]

No download code: source files must already be in data/raw/, see README.md,
section "Data (not in git)". Every column is stored as String and nothing is coerced; later scripts cast explicitly and report parse failures as findings.

Only the five census CSV members and the Release 2 Guide are read from the
Digidata zip. Members are streamed with ZipFile.open to fixed file names
in a temporary directory: no extract helpers, no destination path is ever derived
from a member name, and the full 10.6 GB release is never unpacked.

The script prints only paths, counts and dtypes, never rows.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import zipfile
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


def _tmp_path(target: Path) -> Path:
    return target.parent / f"{target.name}.{os.getpid()}.tmp"


def write_atomic(frame: pl.DataFrame, target: Path) -> None:
    """Write parquet to a pid-suffixed temp file, then rename it onto target.

    A final data/parquet path is therefore either absent or a complete parquet
    from one finished write, even if the run is interrupted or two runs overlap.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = _tmp_path(target)
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
    # The leftover Column1 is kept unchanged, nothing else is coerced.
    non_string = [c for c, t in frame.schema.items() if t != pl.String]
    if non_string:
        frame = frame.with_columns(pl.col(non_string).cast(pl.String))
    write_atomic(frame, project_paths.DWI_PARQUET)
    print(
        f"wrote {project_paths.DWI_PARQUET} rows={frame.height} cols={frame.width}"
    )


def _open_zip() -> zipfile.ZipFile:
    require_sources([project_paths.DIGIDATA_ZIP])
    return zipfile.ZipFile(project_paths.DIGIDATA_ZIP)


def _require_member(zf: zipfile.ZipFile, member: str) -> None:
    if member not in set(zf.namelist()):
        print(
            f"missing zip member: {member} in {project_paths.DIGIDATA_ZIP}",
            file=sys.stderr,
        )
        print(
            'see README.md, section "Data (not in git)", for where it comes from',
            file=sys.stderr,
        )
        sys.exit(2)


def _stream_member(zf: zipfile.ZipFile, member: str, dest: Path) -> None:
    """Stream one named zip member to a caller-chosen path (never member-derived)."""
    with zf.open(member) as src, open(dest, "wb") as out:
        shutil.copyfileobj(src, out, length=1024 * 1024)


def convert_census() -> None:
    zf = _open_zip()
    with zf:
        members = {
            year: project_paths.CENSUS_MEMBER.format(year=year)
            for year in project_paths.CENSUS_YEARS
        }
        for member in members.values():
            _require_member(zf, member)
        project_paths.PARQUET_DIR.mkdir(parents=True, exist_ok=True)
        # Same disk as data/ (the system /tmp is a RAM-backed tmpfs).
        with tempfile.TemporaryDirectory(dir=project_paths.DIGIDATA_DIR) as tmpdir:
            for year, member in members.items():
                tmp_csv = Path(tmpdir) / f"census_{year}.csv"
                _stream_member(zf, member, tmp_csv)
                target = project_paths.census_parquet(year)
                tmp_pq = _tmp_path(target)
                try:
                    pl.scan_csv(tmp_csv, infer_schema=False).sink_parquet(tmp_pq)
                    tmp_pq.replace(target)
                except BaseException:
                    tmp_pq.unlink(missing_ok=True)
                    raise
                finally:
                    tmp_csv.unlink(missing_ok=True)
                print(f"wrote {target}")


def extract_guide() -> None:
    zf = _open_zip()
    with zf:
        _require_member(zf, project_paths.GUIDE_MEMBER)
        size = zf.getinfo(project_paths.GUIDE_MEMBER).file_size
        target = project_paths.GUIDE_PDF
        if target.exists() and target.stat().st_size == size:
            print(f"guide already present: {target}")
            return
        tmp = _tmp_path(target)
        try:
            _stream_member(zf, project_paths.GUIDE_MEMBER, tmp)
            tmp.replace(target)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
        print(f"wrote {target} bytes={size}")


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
    elif path.name.startswith("census_"):
        has_handicaps = "handicaps" in schema
        ok = ok and has_handicaps and rows > 0
        detail += f" has_handicaps={has_handicaps}"
    return ok, detail


def check_outputs(only: str | None) -> int:
    failed = False
    paths: list[Path] = []
    if only in (None, "dwi"):
        paths.append(project_paths.DWI_PARQUET)
    if only in (None, "census"):
        paths.extend(project_paths.census_parquet(y) for y in project_paths.CENSUS_YEARS)
    for path in paths:
        ok, detail = _check_parquet(path)
        print(f"{'OK' if ok else 'FAIL'} {path.name} {detail}")
        failed = failed or not ok
    if only in (None, "census"):
        guide = project_paths.GUIDE_PDF
        if guide.exists() and guide.stat().st_size > 0:
            print(f"OK guide {guide.name} bytes={guide.stat().st_size}")
        else:
            print(f"FAIL guide {guide.name} missing")
            failed = True
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--only", choices=["dwi", "census"], help="convert only one source"
    )
    parser.add_argument(
        "--check", action="store_true", help="validate outputs, write nothing"
    )
    args = parser.parse_args()

    if args.check:
        return check_outputs(args.only)
    if args.only in (None, "dwi"):
        convert_dwi()
    if args.only in (None, "census"):
        convert_census()
        extract_guide()
    return 0


if __name__ == "__main__":
    sys.exit(main())
