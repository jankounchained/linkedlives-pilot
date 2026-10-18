#!/usr/bin/env python3
"""Scan Jupyter notebook cell outputs for record-level content (stdlib only).

This is the automated half of the D-02 rule (notebooks are committed with outputs,
but never with individual records). It is a heuristic backstop on table headers:
it cannot see free text, plots or values. The human review of the rendered
notebooks (plan 01-04) is the final check.

Usage:
    check_notebook_outputs.py [--require-empty] NOTEBOOK...
    check_notebook_outputs.py --self-test

Default mode collects table headers from text/html outputs (th cells) and from
polars text tables in text/plain and stream outputs, then applies:

    Rule A  a header is an identifier column (IDENTIFIER_COLUMNS)
    Rule B  a name column (NAME_COLUMNS) next to a header that is neither a name
            column nor count-like (e.g. a name beside an age)
    Rule C  three or more raw source columns (RAW_COLUMNS) and no count-like header

Count-like headers (n, count, share, pct, ...) mark aggregate tables. With
--require-empty any code cell that still carries outputs or an execution count is
also a violation (the committed notebook source must carry no outputs).
Exit status: 0 clean, 1 violations.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser

IDENTIFIER_COLUMNS = {
    "pa_id",
    "pa_id_1846",
    "pa_id_1850",
    "Column1",
    "Indtastningsnr",
    "løbenr_i_indtastning",
    "Kildehenvisning",
    "Husstands_familienr",
    "Matr_nr_adresse",
    "fødselsdato",
    "inp_FS_RECORD_NBR",
    "inp_FS_HOUSEHOLD_ID",
}

NAME_COLUMNS = {
    "navn",
    "ejernavn",
    "ejendom_navn",
    "inp_PR_NAME",
    "inp_PR_NAME_GN",
    "inp_PR_NAME_SURN",
    "inp_PR_NAME_GN_ORIG",
    "inp_OWNER_NAME_GN_ORIG",
    "inp_OWNER_NAME_SURN_ORIG",
    "gn_norm",
    "sn_norm",
    "owner_norm",
    "name_key",
}

# Union of all census headers (1801 base, then the later additions) and the 22 DWI headers.
_CENSUS_1801 = """pa_id Indtastningsnr Kilde løbenr_i_indtastning Kildehenvisning Stednavn
Husstands_familienr Matr_nr_adresse navn Alder Civilstand nr_ægteskab Erhverv Kommentarer
Stilling_i_husstanden Antal_familier_hus handicaps køn midlertid_oph_sted alder_tal faarb
KIPNr Sogn Type Rigsdel Amt Herred event_subset source_id"""
_CENSUS_1850_ADDS = "fødested trossamfund"
_CENSUS_1860_ADDS = "Adresse gadenr forhus kildekommentar ejernavn"
_CENSUS_1880_ADDS = """Flyttet_kommune hvornår_gift levende_børn døde_børn boligtælling
Erhvervssted fødselsdato Sidste_oph_sted død_ef midlertid_nerverende antal_ægteskab
Matrikel husleje vinduer"""
_CENSUS_1901_ADDS = "fødeaar etage skema_lbnr ejendom_navn Arbejdsplads arbejdssted"
_DWI = """Column1 pa_id source_id inp_PR_NAME inp_PR_NAME_GN inp_PR_NAME_SURN inp_EVENT_TYPE
inp_PR_AGE inp_PR_BIR_PLACE_ORIG inp_PR_SEX_CODE inp_EVENT_YEAR inp_PR_BIR_YEAR_EST
inp_PR_NAME_GN_ORIG inp_FS_RECORD_TYPE inp_PR_MARITAL_STATUS inp_EVENT_PLACE
inp_FS_RECORD_NBR inp_FS_HOUSEHOLD_ID inp_PR_FLAG_FREE_OR_ENSLAVED_ORIG inp_EVENT_PLACE_SUP
inp_OWNER_NAME_GN_ORIG inp_OWNER_NAME_SURN_ORIG"""

RAW_COLUMNS = set(
    " ".join(
        [
            _CENSUS_1801,
            _CENSUS_1850_ADDS,
            _CENSUS_1860_ADDS,
            _CENSUS_1880_ADDS,
            _CENSUS_1901_ADDS,
            _DWI,
        ]
    ).split()
)

_COUNT_EXACT = re.compile(
    r"^(n|len|count|counts|freq|frequency|share|pct|percent|rate|rank)$", re.IGNORECASE
)
_COUNT_SUFFIXES = ("_n", "_count", "_len", "_share", "_pct", "_rate", "_freq")


def is_count_like(header: str) -> bool:
    h = header.strip()
    low = h.lower()
    return bool(
        _COUNT_EXACT.match(h)
        or low.startswith("n_")
        or low.startswith("cum_")
        or low.endswith(_COUNT_SUFFIXES)
    )


# ---------------------------------------------------------------- table headers

class _HtmlHeaders(HTMLParser):
    """Collects, per <table>, the th texts of the first row that has th cells."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[str]] = []
        self._cur: list[str] | None = None
        self._row_th: list[str] = []
        self._in_th = False
        self._buf: list[str] = []
        self._done = True

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == "table":
            self._cur = []
            self._done = False
            self.tables.append(self._cur)
        elif tag == "tr":
            self._row_th = []
        elif tag == "th":
            self._in_th = True
            self._buf = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "th" and self._in_th:
            self._in_th = False
            self._row_th.append("".join(self._buf).strip())
        elif tag == "tr" and self._cur is not None and not self._done:
            cells = [c for c in self._row_th if c]
            if cells:
                self._cur.extend(cells)
                self._done = True

    def handle_data(self, data: str) -> None:
        if self._in_th:
            self._buf.append(data)


def html_tables(html: str) -> list[list[str]]:
    parser = _HtmlHeaders()
    parser.feed(html)
    parser.close()
    return [t for t in parser.tables if t]


_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def text_tables(text: str) -> list[list[str]]:
    """Headers of polars text tables: first '│' line after a '┌' line, split on '┆'."""
    tables: list[list[str]] = []
    lines = _ANSI.sub("", text).splitlines()
    for i, line in enumerate(lines[:-1]):
        if line.lstrip().startswith("┌") and lines[i + 1].lstrip().startswith("│"):
            row = lines[i + 1].strip().strip("│")
            cells = [c.strip() for c in row.split("┆")]
            cells = [c for c in cells if c]
            if cells:
                tables.append(cells)
    return tables


# ------------------------------------------------------------------- scanning

def _join(value) -> str:
    if isinstance(value, list):
        return "".join(str(v) for v in value)
    return str(value or "")


def _output_tables(output: dict) -> list[list[str]]:
    tables: list[list[str]] = []
    otype = output.get("output_type")
    if otype in ("display_data", "execute_result"):
        data = output.get("data", {})
        if "text/html" in data:
            tables.extend(html_tables(_join(data["text/html"])))
        if "text/plain" in data:
            tables.extend(text_tables(_join(data["text/plain"])))
    elif otype == "stream":
        tables.extend(text_tables(_join(output.get("text", ""))))
    elif otype == "error":
        tables.extend(text_tables(_join(output.get("traceback", []))))
    return tables


def violations_for_headers(headers: list[str]) -> list[str]:
    found: list[str] = []
    hs = set(headers)
    count_like = any(is_count_like(h) for h in headers)
    if hs & IDENTIFIER_COLUMNS:
        found.append("A")
    names = hs & NAME_COLUMNS
    if names and any(h not in NAME_COLUMNS and not is_count_like(h) for h in headers):
        found.append("B")
    if len(hs & RAW_COLUMNS) >= 3 and not count_like:
        found.append("C")
    return found


def scan_notebook(
    nb: dict, label: str, require_empty: bool
) -> tuple[list[str], int]:
    """Return (violation lines, number of table outputs scanned)."""
    lines: list[str] = []
    seen: set[tuple] = set()
    n_tables = 0
    for idx, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        outputs = cell.get("outputs") or []
        if require_empty and (outputs or cell.get("execution_count") is not None):
            lines.append(
                f"VIOLATION {label} cell={idx} rule=outputs-present headers="
            )
        for output in outputs:
            for headers in _output_tables(output):
                n_tables += 1
                for rule in violations_for_headers(headers):
                    key = (idx, rule, tuple(headers))
                    if key in seen:
                        continue
                    seen.add(key)
                    lines.append(
                        f"VIOLATION {label} cell={idx} rule={rule} "
                        f"headers={','.join(headers)}"
                    )
    return lines, n_tables


def run(paths: list[str], require_empty: bool) -> int:
    all_lines: list[str] = []
    total_tables = 0
    for path in paths:
        try:
            with open(path, encoding="utf-8") as fh:
                nb = json.load(fh)
        except (OSError, ValueError) as exc:
            print(f"ERROR cannot read notebook {path}: {type(exc).__name__}", file=sys.stderr)
            return 1
        lines, n = scan_notebook(nb, path, require_empty)
        all_lines.extend(lines)
        total_tables += n
    if all_lines:
        print("\n".join(all_lines))
        return 1
    print(f"OK {len(paths)} notebook(s), {total_tables} table output(s) scanned")
    return 0


# ------------------------------------------------------------------ self-test

def _html_out(headers: list[str]) -> dict:
    ths = "".join(f"<th>{h}</th>" for h in headers)
    tds = "".join("<td>str</td>" for _ in headers)
    html = f"<table><thead><tr>{ths}</tr><tr>{tds}</tr></thead><tbody></tbody></table>"
    return {"output_type": "display_data", "data": {"text/html": [html]}, "metadata": {}}


def _text_out(headers: list[str], stream: bool = False) -> dict:
    top = "┌" + "┬".join("─" * 8 for _ in headers) + "┐"
    head = "│ " + " ┆ ".join(headers) + " │"
    text = f"shape: (3, {len(headers)})\n{top}\n{head}\n╞════╡\n"
    if stream:
        return {"output_type": "stream", "name": "stdout", "text": [text]}
    return {"output_type": "execute_result", "data": {"text/plain": [text]}, "metadata": {}, "execution_count": 1}


def _nb(*outputs: dict) -> dict:
    return {
        "cells": [
            {"cell_type": "code", "source": "x", "outputs": list(outputs), "execution_count": 1 if outputs else None, "metadata": {}}
        ]
    }


def self_test() -> int:
    failures: list[str] = []

    def expect(name: str, nb: dict, require_empty: bool, rules: set[str]) -> None:
        lines, _ = scan_notebook(nb, "fixture", require_empty)
        got = {re.search(r"rule=(\S+)", ln).group(1) for ln in lines}
        if got != rules:
            failures.append(f"{name}: expected {sorted(rules)}, got {sorted(got)}")

    expect("clean frequency table (html)", _nb(_html_out(["handicaps_norm", "n"])), False, set())
    expect("clean frequency table (text)", _nb(_text_out(["handicaps_norm", "n"])), False, set())
    expect("pa_id header (rule A)", _nb(_html_out(["pa_id", "handicaps"])), False, {"A"})
    expect("name beside age (rule B)", _nb(_html_out(["inp_PR_NAME_GN", "inp_PR_AGE"])), False, {"B"})
    expect(
        "stream text table with navn and alder_tal (rule B)",
        _nb(_text_out(["navn", "alder_tal"], stream=True)),
        False,
        {"B"},
    )
    expect("name with count is aggregate", _nb(_html_out(["gn_norm", "n"])), False, set())
    expect("three raw columns (rule C)", _nb(_html_out(["Sogn", "Amt", "Herred"])), False, {"C"})
    expect("raw columns with share are aggregate", _nb(_html_out(["Sogn", "Amt", "Herred", "share"])), False, set())
    expect("output present under --require-empty", _nb(_html_out(["handicaps_norm", "n"])), True, {"outputs-present"})
    expect("no outputs under --require-empty", _nb(), True, set())

    if failures:
        for f in failures:
            print(f"SELF-TEST FAIL {f}", file=sys.stderr)
        return 1
    print("SELF-TEST OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan notebook outputs for record-level tables.")
    parser.add_argument("notebooks", nargs="*", metavar="NOTEBOOK")
    parser.add_argument("--require-empty", action="store_true", help="also flag any code cell with outputs or an execution count")
    parser.add_argument("--self-test", action="store_true", help="run built-in fixtures")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.notebooks:
        parser.error("give at least one notebook, or --self-test")
    return run(args.notebooks, args.require_empty)


if __name__ == "__main__":
    sys.exit(main())
