#!/usr/bin/env python3
"""Compute A0 and Krippendorff nominal alpha for three-seat gold checkout panels.

Lab analysis only — not wired into run_proofs.sh. Published alphas use the
`krippendorff` package. If that package is missing, a stdlib binary nominal
fallback runs; it is not bit-identical to the package on non-constant tables,
so regenerate published JSON only with `krippendorff` installed.

`--panel expansion` (default) scores the corpus-expand seat files. `--panel thrash`
scores the experiment (d) thrash-screen seat files. `--panel expand-e` scores the
experiment (e) thrash-expand seat files. `--panel thrash-de` pools (d) and (e)
(17 prefixes). Seat filenames can be overridden with `--sonnet-file`,
`--composer-file`, and `--grok-file`.

An all-`not_yet` table has Do = De = 0. Nominal α is undefined there (the
`krippendorff` package raises ValueError; a de==0 convention of 1.0 is not an
H5 pass and does not unlock gold).
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

PROOFS = Path(__file__).resolve().parent
GOLD = PROOFS / "validated" / "gold"

SEAT_ORDER = ("sonnet", "composer", "grok")

# Default seat JSONLs per panel. `--panel` selects one; `--sonnet-file` /
# `--composer-file` / `--grok-file` override filenames (gold-dir relative or path).
PANELS: dict[str, dict[str, Any]] = {
    "expansion": {
        "generated_for": "experiment (c) corpus-expand-hybrid-panel-original",
        "schedule": "P0 first_at=75 interval=15",
        "seat_files": {
            "sonnet": "expansion-checkout-verdicts-sonnet-20261001.jsonl",
            "composer": "expansion-checkout-verdicts-composer-20261001.jsonl",
            "grok": "expansion-checkout-verdicts-grok-20261001.jsonl",
        },
        "out": GOLD / "expansion-panel-agreement-20261001.json",
        "notes": [
            "Expansion workers: 0aab88c525de, 036ff3ed4a89, 0853bc21d3aa (20 pooled prefixes).",
            "A0 null on all three — no unanimous checkout even though raw agreement is high (prevalence of not_yet).",
            "H5 fails on expansion-only α; usable gold for A0 tuning still blocked. No Jev sweep.",
        ],
    },
    "thrash": {
        "generated_for": "experiment (d) ubuntu-thrash-screen-before-pack-v1",
        "schedule": "P0 first_at=75 interval=15",
        "pack_source": "thrash-screen-judge-packs-20261001-204508.jsonl",
        "seat_files": {
            "sonnet": "thrash-screen-checkout-verdicts-sonnet-20261001.jsonl",
            "composer": "thrash-screen-checkout-verdicts-composer-20261001.jsonl",
            "grok": "thrash-screen-checkout-verdicts-grok-20261001.jsonl",
        },
        "out": GOLD / "thrash-screen-panel-agreement-20261001.json",
        "notes": [
            "Thrash-screen workers: ca977b9ca0dd (3 cps), daf933273c8f (4), 7b00225cb824 (5); 12 pooled prefixes.",
            "A0 is 90 on ca977b9ca0dd (Sonnet alone at 75; unanimous from 90) and null on daf933273c8f and 7b00225cb824.",
            "H5 passes on thrash-only nominal alpha (>= 0.40) with only one non-null A0. Jev/stats sweep stays blocked on that single-A0 caveat. No behaviour change.",
        ],
    },
    "expand-e": {
        "generated_for": "experiment (e) ubuntu-thrash-high-score-expand-v1",
        "schedule": "P0 first_at=75 interval=15",
        "pack_source": "thrash-expand-e-judge-packs-20261001-210125.jsonl",
        "seat_files": {
            "sonnet": "thrash-expand-e-checkout-verdicts-sonnet-20261001.jsonl",
            "composer": "thrash-expand-e-checkout-verdicts-composer-20261001.jsonl",
            "grok": "thrash-expand-e-checkout-verdicts-grok-20261001.jsonl",
        },
        "out": GOLD / "thrash-expand-e-panel-agreement-20261001.json",
        "notes": [
            "Thrash-expand (e) workers: e8aa4f271927 (1 cp), 5163c22a6a3e (2), a318f4b89a6a (2); 5 pooled prefixes.",
            "Strict ca977 shape (no Edit/Write AND max_reread>=8 AND compact>=8) was empty on the remaining open-pajero-maps T>=75 pool (n=26). These three workers are the pre-registered best-available research panel, not a shape-gate pass.",
            "A0 is null on e8aa4f271927, 5163c22a6a3e, and a318f4b89a6a. Earliest checkout is null on every seat (0/5 checkout_recommended).",
            "Nominal alpha is undefined on an all-not_yet table (Do = De = 0). krippendorff.alpha raises ValueError (domain must contain more than one value). The stdlib de==0 branch would return 1.0; that convention is not the reported value, is not an H5 pass, and does not unlock gold or Jev.",
            "Experiment (e) adds zero checkouts and zero non-null A0. Jev/stats sweep stays blocked until >=2 workers have non-null A0. No behaviour change.",
        ],
    },
    "thrash-de": {
        "generated_for": "experiments (d)+(e) thrash-screen plus thrash-expand",
        "schedule": "P0 first_at=75 interval=15",
        "pack_source": [
            "thrash-screen-judge-packs-20261001-204508.jsonl",
            "thrash-expand-e-judge-packs-20261001-210125.jsonl",
        ],
        "seat_files": {
            "sonnet": [
                "thrash-screen-checkout-verdicts-sonnet-20261001.jsonl",
                "thrash-expand-e-checkout-verdicts-sonnet-20261001.jsonl",
            ],
            "composer": [
                "thrash-screen-checkout-verdicts-composer-20261001.jsonl",
                "thrash-expand-e-checkout-verdicts-composer-20261001.jsonl",
            ],
            "grok": [
                "thrash-screen-checkout-verdicts-grok-20261001.jsonl",
                "thrash-expand-e-checkout-verdicts-grok-20261001.jsonl",
            ],
        },
        "out": GOLD / "thrash-de-panel-agreement-20261001.json",
        "notes": [
            "Pooled thrash table: (d) 12 prefixes plus (e) 5 prefixes = 17. Workers do not overlap.",
            "Non-null A0 remains one worker: ca977b9ca0dd at 90. (e) workers e8aa4f271927, 5163c22a6a3e, and a318f4b89a6a are A0 null (0/5 checkout on every seat).",
            "Combined nominal alpha is 0.8377 (numeric H5 floor passes). The lift from (d)'s 0.8276 is five unanimous not_yet prefixes, not a new checkout. It does not replace P0 or expansion alpha. h5_pass on this table is not a gold unlock: non-null A0 count is still 1, so Jev and any stats sweep stay blocked.",
            "All-not_yet prefixes from (e) must not be read as a second gold exit. No behaviour change.",
        ],
    },
}

# Backward-compatible alias for the expansion seat map.
SEAT_FILES = PANELS["expansion"]["seat_files"]


def _load_sonnet_p0(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("signed") and row.get("role") == "reviewer_final":
            rows.append(row)
    return rows


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _unit_key(row: dict[str, Any]) -> tuple[str, int]:
    return (row["worker_id"], int(row["checkpoint_turn"]))


def build_matrix(
    seat_rows: dict[str, list[dict[str, Any]]],
    seat_order: tuple[str, ...],
) -> tuple[list[tuple[str, int]], list[list[int]]]:
    by_unit: dict[tuple[str, int], dict[str, int]] = defaultdict(dict)
    for seat in seat_order:
        for row in seat_rows[seat]:
            key = _unit_key(row)
            if seat in by_unit[key]:
                raise SystemExit(f"duplicate unit {key} for seat {seat}")
            by_unit[key][seat] = int(row["checkout_recommended"])
    keys = sorted(by_unit.keys())
    incomplete = [k for k in keys if any(s not in by_unit[k] for s in seat_order)]
    if incomplete:
        raise SystemExit(f"units missing a seat: {incomplete[:5]}")
    matrix = [[by_unit[k][s] for s in seat_order] for k in keys]
    return keys, matrix


def a0_unanimous(keys: list[tuple[str, int]], matrix: list[list[int]]) -> dict[str, int | None]:
    workers = sorted({k[0] for k in keys})
    out: dict[str, int | None] = {}
    for worker in workers:
        gold: int | None = None
        for (wid, turn), vals in zip(keys, matrix):
            if wid != worker:
                continue
            if all(v == 1 for v in vals):
                gold = turn
                break
        out[worker] = gold
    return out


def earliest_checkout_by_seat(
    keys: list[tuple[str, int]],
    matrix: list[list[int]],
    seat_order: tuple[str, ...],
) -> dict[str, dict[str, int | None]]:
    workers = sorted({k[0] for k in keys})
    out: dict[str, dict[str, int | None]] = {s: {} for s in seat_order}
    for seat_idx, seat in enumerate(seat_order):
        for worker in workers:
            earliest: int | None = None
            for (wid, turn), vals in zip(keys, matrix):
                if wid != worker:
                    continue
                if vals[seat_idx] == 1:
                    earliest = turn
                    break
            out[seat][worker] = earliest
    return out


def checkout_positive_counts(
    keys: list[tuple[str, int]],
    matrix: list[list[int]],
    seat_order: tuple[str, ...],
) -> dict[str, int]:
    counts = {s: 0 for s in seat_order}
    for vals in matrix:
        for seat_idx, seat in enumerate(seat_order):
            counts[seat] += vals[seat_idx]
    return counts


def cohen_kappa_binary(a: list[int], b: list[int]) -> float:
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    p1 = sum(a) / n
    p2 = sum(b) / n
    pe = p1 * p2 + (1 - p1) * (1 - p2)
    if pe >= 1.0:
        return 0.0
    return (po - pe) / (1 - pe)


def krippendorff_alpha_nominal_binary(matrix: list[list[int]]) -> float:
    """Nominal alpha for binary labels; units with <2 coders are skipped."""
    try:
        import krippendorff  # type: ignore
        import numpy as np

        arr = np.array(matrix, dtype=float)
        try:
            return float(
                krippendorff.alpha(
                    reliability_data=arr.T,
                    level_of_measurement="nominal",
                )
            )
        except ValueError as exc:
            # Single-category tables: "There has to be more than one value in the domain."
            # Do = De = 0, so nominal alpha is undefined. Do not coerce that to 1.0.
            if "more than one value" in str(exc):
                return float("nan")
            raise
    except ImportError:
        pass

    # Stdlib fallback: coincidence matrix for values 0 and 1 (V=2).
    value_counts: list[tuple[int, int]] = []
    for row in matrix:
        n1 = sum(row)
        n0 = len(row) - n1
        if n0 + n1 < 2:
            continue
        value_counts.append((n0, n1))
    if not value_counts:
        return float("nan")

    def coincidences(n0: int, n1: int) -> list[list[float]]:
        pairable = max(n0 + n1, 2)
        denom = pairable * (pairable - 1)
        o00 = n0 * (n0 - 1) / denom
        o11 = n1 * (n1 - 1) / denom
        o01 = 2 * n0 * n1 / denom
        return [[o00, o01], [o01, o11]]

    o = [[0.0, 0.0], [0.0, 0.0]]
    for n0, n1 in value_counts:
        c = coincidences(n0, n1)
        for i in range(2):
            for j in range(2):
                o[i][j] += c[i][j]

    n_v = [o[0][0] + o[0][1], o[1][0] + o[1][1]]
    n_total = n_v[0] + n_v[1]
    if n_total <= 0:
        return float("nan")
    e = [
        [n_v[0] * (n_v[0] - 1) / (n_total - 1), n_v[0] * n_v[1] / (n_total - 1)],
        [n_v[1] * n_v[0] / (n_total - 1), n_v[1] * (n_v[1] - 1) / (n_total - 1)],
    ]
    d_nominal = [[0.0, 1.0], [1.0, 0.0]]
    do = sum(o[i][j] * d_nominal[i][j] for i in range(2) for j in range(2))
    de = sum(e[i][j] * d_nominal[i][j] for i in range(2) for j in range(2))
    if de == 0:
        # Do = De = 0 (every label is the same category). Alpha is undefined.
        # A 1.0 convention is not returned; callers must not treat it as H5.
        return float("nan")
    return 1.0 - do / de


def pairwise_metrics(
    keys: list[tuple[str, int]],
    matrix: list[list[int]],
    seat_order: tuple[str, ...],
) -> dict[str, Any]:
    cols = {seat: [row[i] for row in matrix] for i, seat in enumerate(seat_order)}
    pairs: dict[str, Any] = {}
    for s1, s2 in combinations(seat_order, 2):
        a, b = cols[s1], cols[s2]
        n = len(a)
        agree = sum(x == y for x, y in zip(a, b)) / n if n else float("nan")
        pairs[f"{s1}_vs_{s2}"] = {
            "overall_pct": round(100 * agree, 2),
            "cohen_kappa": round(cohen_kappa_binary(a, b), 4),
        }
    return pairs


def _resolve_seat_path(name_or_path: str) -> Path:
    path = Path(name_or_path)
    if path.is_file():
        return path
    return GOLD / name_or_path


def _as_file_list(spec: str | list[str]) -> list[str]:
    if isinstance(spec, str):
        return [spec]
    return list(spec)


def _load_seat_rows(spec: str | list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name in _as_file_list(spec):
        rows.extend(_load_jsonl(_resolve_seat_path(name)))
    return rows


def _source_names(spec: str | list[str]) -> str | list[str]:
    names = [Path(name).name for name in _as_file_list(spec)]
    if len(names) == 1:
        return names[0]
    return names


def _alpha_block(matrix: list[list[int]], units: int) -> dict[str, Any]:
    """Nominal alpha. A constant table is undefined, not H5-pass at 1.0."""
    alpha = krippendorff_alpha_nominal_binary(matrix)
    defined = alpha == alpha  # False for NaN
    block: dict[str, Any] = {
        "scale": "nominal",
        "variable": "checkout_recommended (binary)",
        "coders": 3,
        "units": units,
        "value": None if not defined else round(alpha, 4),
        "h5_floor": 0.4,
        "h5_pass": False if not defined else bool(alpha >= 0.4),
        "alpha_method": "krippendorff",
    }
    if defined:
        return block
    positives = sum(v for row in matrix for v in row)
    block["defined"] = False
    block["undefined_reason"] = "all_not_yet" if positives == 0 else "constant_label"
    block["stdlib_de_eq_0_convention"] = 1.0
    block["note"] = (
        "Nominal alpha is undefined when every label is the same category "
        "(Do = De = 0). krippendorff.alpha raises ValueError "
        "('There has to be more than one value in the domain.'). "
        "The stdlib de==0 branch would return 1.0; that convention is recorded "
        "as stdlib_de_eq_0_convention and is not an H5 pass, not a gold unlock, "
        "and not a Jev gate."
    )
    return block


def panel_report(
    panel: str = "expansion",
    seat_files: dict[str, str | list[str]] | None = None,
) -> dict[str, Any]:
    """Build the agreement report for a named panel.

    `seat_files` overrides the panel's default JSONL names (values are gold-dir
    filenames, filesystem paths, or a list of those to concatenate). Seat order
    stays sonnet, composer, grok.
    """
    if panel not in PANELS:
        known = ", ".join(sorted(PANELS))
        raise SystemExit(f"unknown panel {panel!r}; choose from {known}")
    spec = PANELS[panel]
    files: dict[str, str | list[str]] = dict(spec["seat_files"])
    if seat_files:
        files.update(seat_files)
    seat_order = SEAT_ORDER
    seat_rows = {seat: _load_seat_rows(files[seat]) for seat in seat_order}
    keys, matrix = build_matrix(seat_rows, seat_order)
    pos = checkout_positive_counts(keys, matrix, seat_order)
    workers = sorted({k[0] for k in keys})
    worker_cps = {w: sum(1 for k in keys if k[0] == w) for w in workers}
    panel_block: dict[str, Any] = {
        "seats": list(seat_order),
        "sources": {s: _source_names(files[s]) for s in seat_order},
        "schedule": spec["schedule"],
    }
    if spec.get("pack_source"):
        panel_block["pack_source"] = spec["pack_source"]
    return {
        "generated_for": spec["generated_for"],
        "panel": panel_block,
        "n_checkpoints": len(keys),
        "workers": worker_cps,
        "earliest_checkout_recommended_by_seat": earliest_checkout_by_seat(keys, matrix, seat_order),
        "a0_unanimous_checkout": {
            "rule": "Earliest checkpoint turn c where sonnet, composer, and grok all have checkout_recommended=true at that prefix",
            "by_worker": a0_unanimous(keys, matrix),
        },
        "krippendorff_alpha": _alpha_block(matrix, len(keys)),
        "checkout_positive_counts": {**pos, "total_true_labels": sum(pos.values())},
        "pairwise_agreement": pairwise_metrics(keys, matrix, seat_order),
        "notes": list(spec["notes"]),
    }


def expansion_panel() -> dict[str, Any]:
    return panel_report("expansion")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--panel",
        choices=sorted(PANELS),
        default="expansion",
        help=(
            "Which gold panel to score (default: expansion). "
            "'thrash' is experiment (d); 'expand-e' is experiment (e); "
            "'thrash-de' pools (d) and (e)."
        ),
    )
    parser.add_argument("--sonnet-file", help="Override the sonnet seat JSONL (filename or path)")
    parser.add_argument("--composer-file", help="Override the composer seat JSONL (filename or path)")
    parser.add_argument("--grok-file", help="Override the grok seat JSONL (filename or path)")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write machine-readable agreement JSON (default: the panel's registered path)",
    )
    parser.add_argument("--print-alpha", action="store_true", help="Print nominal alpha to stdout")
    args = parser.parse_args()
    overrides = {
        seat: getattr(args, f"{seat}_file")
        for seat in SEAT_ORDER
        if getattr(args, f"{seat}_file")
    }
    report = panel_report(args.panel, overrides or None)
    out = args.out if args.out is not None else PANELS[args.panel]["out"]
    out.write_text(json.dumps(report, indent=2) + "\n")
    if args.print_alpha:
        value = report["krippendorff_alpha"]["value"]
        print("undefined" if value is None else value)


if __name__ == "__main__":
    main()
