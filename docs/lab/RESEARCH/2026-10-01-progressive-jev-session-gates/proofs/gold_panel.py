"""Gold-label aggregation for progressive Jev session gates.

CHM (Coding Harness Manager) writes multi-model verdict JSON under
``validated/gold/``. This module reads that shape and computes TERMS §7
rule A0. It does not invent a checkout when ``checkout_recommended`` is null.

On ``p0-checkout-verdicts-20261001.jsonl``, only ``signed: true`` rows vote.
Those are the Sonnet reviewer finals. Unsigned ``role: draft`` Flash rows are
a review trail, not a seat. ``grok-4.7-high`` and ``composer`` stay empty
until a later signed pack fills them. Primary ``gold_exit`` stays null until
three seats have voted.

Canonical verdict object::

    {
      "worker_id": "92a48e004519",
      "checkpoint_turn": 105,
      "model": "grok-4.7-high",
      "checkout_recommended": true,
      "rationale": "...",
      "first_checkout_turn_guess": 105
    }

Also accepted: a JSON list of those objects, JSONL, ``{"verdicts": [...]}``
or ``{"labels": [...]}`` (parent ``worker_id`` / ``checkpoint_turn`` fill
gaps), and a per-worker ``{"models": {model: {"checkpoints": [...]}}}`` file.
TERMS rows with ``answer: not_yet|checkout`` and ``judge`` map onto the same
object. A null ``checkout_recommended`` is pending. It is not ``not_yet``.

Primary ``gold_exit`` requires three judges at every turn the walk uses
(TERMS §7, TUNING-PLAN stage 3). With two judges the earliest unanimous
turn is stored as ``gold_exit_unanimous_min2`` and ``panel`` is
``underpowered``. Confidence stays not high either way.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

H5_ALPHA_FLOOR = 0.40
PRIMARY_MIN_JUDGES = 3
DIAGNOSTIC_MIN_JUDGES = 2

ALPHA_METHOD_NOTE = (
    "Krippendorff nominal alpha on {not_yet, checkout}. "
    "A unit is one (worker_id, checkpoint_turn). "
    "Null checkout_recommended is missing data, not not_yet. "
    "For each unit with m>=2 assignments, coincidence o_ck adds "
    "n_c*(n_c-1)/(m-1) on the diagonal and n_c*n_k/(m-1) off it. "
    "Nominal delta^2 is 0 when the categories match and 1 otherwise. "
    "alpha = 1 - D_o/D_e. D_e = 0 (one category only) leaves alpha null. "
    "Ordinal alpha is the same ratio with "
    "delta^2(c,k) = (sum of marginal counts from c through k, minus (n_c+n_k)/2)^2 "
    "(Krippendorff, 2011, Computing Krippendorff's Alpha-Reliability). "
    "Use ordinal alpha for ordered 0-3 pattern scores. "
    "CHM verdicts are boolean checkout_recommended, so the H5 number is nominal "
    "and alpha_ordinal stays null until a verdict carries an ordered score."
)

SKIP_FILE_NAMES = {
    "summary.json",
    "export.json",
    "readme.md",
    "score-ubuntu-raw-dry-run.json",
}
# Seats CHM can still fill. Matching is substring on the model id.
PANEL_SEATS = (
    ("claude-sonnet", ("claude-sonnet", "sonnet")),
    ("grok-4.7-high", ("grok-4.7",)),
    ("composer", ("composer",)),
)
CHECKOUT_ANSWERS = {"checkout"}
NOT_YET_ANSWERS = {"not_yet", "continue", "inconclusive"}


def _read_json_docs(path: Path) -> list[Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        docs: list[Any] = []
        for line in text.splitlines():
            if line.strip():
                docs.append(json.loads(line))
        return docs
    if not text.strip():
        return []
    return [json.loads(text)]


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value == int(value):
        return int(value)
    return None


def _checkout_bit(raw: dict[str, Any]) -> tuple[bool | None, str | None]:
    """Return (checkout or None if pending, invalid_reason)."""
    if raw.get("invalid_reason"):
        return None, str(raw["invalid_reason"])
    if "checkout_recommended" in raw:
        bit = raw.get("checkout_recommended")
        if bit is None:
            return None, None
        if isinstance(bit, bool):
            if bit and isinstance(raw.get("patterns"), list) and len(raw["patterns"]) == 0:
                return None, "checkout_without_pattern"
            return bit, None
        return None, "checkout_recommended_not_bool"
    if "answer" in raw:
        answer = raw.get("answer")
        if answer is None:
            return None, None
        if not isinstance(answer, str):
            return None, "answer_not_string"
        token = answer.strip().lower()
        if token in CHECKOUT_ANSWERS:
            if isinstance(raw.get("patterns"), list) and len(raw["patterns"]) == 0:
                return None, "checkout_without_pattern"
            return True, None
        if token in NOT_YET_ANSWERS:
            return False, None
        return None, "answer_not_binary"
    return None, None


def normalize_label(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Map one object onto the canonical verdict. Bundles return None."""
    if "brief_anchor" in raw and "checkout_recommended" not in raw and "answer" not in raw:
        return None
    worker = raw.get("worker_id")
    turn = _as_int(raw.get("checkpoint_turn", raw.get("turn")))
    if not isinstance(worker, str) or not worker or turn is None:
        return None
    model = raw.get("model", raw.get("judge", raw.get("judge_model_id")))
    if model is not None and not isinstance(model, str):
        model = str(model)
    if isinstance(model, str):
        model = model.strip() or None
    bit, invalid = _checkout_bit(raw)
    guess = _as_int(raw.get("first_checkout_turn_guess", raw.get("first_checkout_guess")))
    rationale = raw.get("rationale")
    if rationale is None:
        rationale = ""
    if not isinstance(rationale, str):
        rationale = str(rationale)
    T = _as_int(raw.get("T"))
    signed = raw.get("signed") if isinstance(raw.get("signed"), bool) else None
    role = raw.get("role") if isinstance(raw.get("role"), str) else None
    return {
        "worker_id": worker,
        "checkpoint_turn": turn,
        "model": model,
        "checkout_recommended": bit,
        "rationale": rationale,
        "first_checkout_turn_guess": guess,
        "T": T,
        "signed": signed,
        "role": role,
        "invalid_reason": invalid,
        "pending": bit is None and invalid is None,
    }


def is_voting_label(label: dict[str, Any]) -> bool:
    """Signed Sonnet finals vote. Unsigned Flash drafts do not.

    Rows with no ``signed`` flag and no ``role`` still vote, so a later
    Grok or Composer pack can use the flat verdict shape.
    """
    if label.get("signed") is True:
        return True
    if label.get("signed") is False or label.get("role") == "draft":
        return False
    return True


def seat_for_model(model: str) -> str | None:
    text = model.lower()
    for seat, aliases in PANEL_SEATS:
        if any(alias in text for alias in aliases):
            return seat
    return None


def _merge(parent: dict[str, Any], child: dict[str, Any]) -> dict[str, Any]:
    merged = dict(parent)
    merged.update(child)
    return merged


def explode_document(doc: Any) -> list[dict[str, Any]]:
    """Flatten one JSON document into canonical verdicts."""
    if isinstance(doc, list):
        rows: list[dict[str, Any]] = []
        for item in doc:
            rows.extend(explode_document(item))
        return rows
    if not isinstance(doc, dict):
        return []
    for key in ("verdicts", "labels"):
        nested = doc.get(key)
        if isinstance(nested, list):
            parent = {
                field: doc[field]
                for field in (
                    "worker_id",
                    "checkpoint_turn",
                    "turn",
                    "model",
                    "T",
                    "first_checkout_turn_guess",
                )
                if field in doc
            }
            rows = []
            for item in nested:
                if isinstance(item, dict):
                    rows.extend(explode_document(_merge(parent, item)))
            return rows
    models = doc.get("models")
    if isinstance(models, dict):
        rows = []
        for model_name, payload in models.items():
            model = model_name if isinstance(model_name, str) else str(model_name)
            if isinstance(payload, list):
                for item in payload:
                    if isinstance(item, dict):
                        rows.extend(
                            explode_document(
                                _merge(
                                    {"worker_id": doc.get("worker_id"), "T": doc.get("T"), "model": model},
                                    item,
                                )
                            )
                        )
                continue
            if not isinstance(payload, dict):
                continue
            guess = payload.get("first_checkout_turn_guess")
            series = None
            for key in ("checkpoints", "labels", "verdicts"):
                if isinstance(payload.get(key), list):
                    series = payload[key]
                    break
            if series is None:
                rows.extend(
                    explode_document(
                        _merge(
                            {"worker_id": doc.get("worker_id"), "T": doc.get("T"), "model": model},
                            payload,
                        )
                    )
                )
                continue
            for item in series:
                if not isinstance(item, dict):
                    continue
                child = _merge(
                    {
                        "worker_id": doc.get("worker_id"),
                        "T": doc.get("T"),
                        "model": model,
                        "first_checkout_turn_guess": guess,
                    },
                    item,
                )
                rows.extend(explode_document(child))
        return rows
    label = normalize_label(doc)
    if label is None:
        return []
    return [label]


def iter_label_paths(root: Path, *, include_pending: bool) -> list[Path]:
    if root.is_file():
        return [root]
    found: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in {".json", ".jsonl"}:
            continue
        lowered = path.name.lower()
        if lowered in SKIP_FILE_NAMES or lowered.startswith("score") or "summary" in lowered:
            continue
        if path.name.endswith(".bundle.json"):
            continue
        rel_parts = path.relative_to(root).parts
        if not include_pending and "pending" in rel_parts:
            continue
        found.append(path)
    return found


def load_labels(root: Path, *, include_pending: bool = False) -> list[dict[str, Any]]:
    labels: list[dict[str, Any]] = []
    for path in iter_label_paths(root, include_pending=include_pending):
        for doc in _read_json_docs(path):
            for label in explode_document(doc):
                label["source"] = str(path)
                labels.append(label)
    return labels


def _majority_threshold(n: int) -> int:
    """More than half, the TERMS §7 A1 examples (2 of 3, 3 of 4)."""
    return (n // 2) + 1


def _round_up_to_grid(value: float, grid: list[int]) -> int | None:
    for turn in grid:
        if turn >= value:
            return turn
    return None


def _median_up(values: list[int], grid: list[int]) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        raw: float = float(ordered[mid])
    else:
        raw = (ordered[mid - 1] + ordered[mid]) / 2
    return _round_up_to_grid(raw, grid)


def krippendorff_alpha(
    units: list[list[Any]],
    *,
    level: str = "nominal",
) -> float | None:
    """Nominal or ordinal Krippendorff alpha. None when the ratio is undefined.

    ``units`` is a list of coder assignments. None entries are missing.
    A unit with fewer than two assignments contributes nothing.
    """
    if level not in {"nominal", "ordinal"}:
        raise ValueError(f"level must be nominal or ordinal, got {level!r}")
    prepared: list[list[Any]] = []
    for unit in units:
        values = [value for value in unit if value is not None]
        if len(values) >= 2:
            prepared.append(values)
    if not prepared:
        return None
    categories = sorted({value for unit in prepared for value in unit}, key=lambda item: (str(type(item)), item))
    if level == "ordinal":
        for value in categories:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return None
        categories = sorted(categories)
    index = {category: pos for pos, category in enumerate(categories)}
    size = len(categories)
    coincidence = [[0.0 for _ in range(size)] for _ in range(size)]
    for unit in prepared:
        counts = [0 for _ in range(size)]
        for value in unit:
            counts[index[value]] += 1
        m = len(unit)
        for c in range(size):
            for k in range(size):
                if counts[c] == 0 or counts[k] == 0:
                    continue
                if c == k:
                    coincidence[c][k] += counts[c] * (counts[c] - 1) / (m - 1)
                else:
                    coincidence[c][k] += counts[c] * counts[k] / (m - 1)
    n = sum(sum(row) for row in coincidence)
    if n <= 1:
        return None
    marginals = [sum(coincidence[c][k] for k in range(size)) for c in range(size)]

    def delta(c: int, k: int) -> float:
        if c == k:
            return 0.0
        if level == "nominal":
            return 1.0
        lo, hi = (c, k) if c < k else (k, c)
        span = sum(marginals[g] for g in range(lo, hi + 1)) - (marginals[c] + marginals[k]) / 2
        return span * span

    observed = 0.0
    expected = 0.0
    for c in range(size):
        for k in range(size):
            distance = delta(c, k)
            observed += coincidence[c][k] * distance
            expected += marginals[c] * marginals[k] * distance
    observed /= n
    expected /= n * (n - 1)
    if expected == 0:
        return None
    return 1.0 - (observed / expected)


def cohen_kappa(pairs: list[tuple[Any, Any]]) -> dict[str, Any] | None:
    if not pairs:
        return None
    n = len(pairs)
    po = sum(1 for left, right in pairs if left == right) / n
    labels = {label for pair in pairs for label in pair}
    pe = 0.0
    for label in labels:
        p1 = sum(1 for left, _right in pairs if left == label) / n
        p2 = sum(1 for _left, right in pairs if right == label) / n
        pe += p1 * p2
    kappa = None if pe == 1 else (po - pe) / (1 - pe)
    return {"n": n, "raw_agreement": po, "kappa": kappa}


def _dedupe(labels: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Last filled verdict wins for a (worker, turn, model) key. Templates stay."""
    chosen: dict[tuple[str, int, str], dict[str, Any]] = {}
    duplicates = 0
    pending: list[dict[str, Any]] = []
    for label in labels:
        model = label.get("model")
        if not model:
            pending.append(label)
            continue
        key = (label["worker_id"], label["checkpoint_turn"], model)
        if key in chosen:
            duplicates += 1
        chosen[key] = label
    return list(chosen.values()) + pending, duplicates


def _draft_review(drafts: list[dict[str, Any]], voting: list[dict[str, Any]]) -> dict[str, Any]:
    """Count Flash checkout rows that a signed reviewer changed to not_yet."""
    finals: dict[tuple[str, int], dict[str, Any]] = {}
    for label in voting:
        if label.get("signed") is not True or label.get("pending") or label.get("invalid_reason"):
            continue
        finals[(label["worker_id"], label["checkpoint_turn"])] = label
    n_draft_checkout = 0
    n_corrected = 0
    n_agree_not_yet = 0
    n_agree_checkout = 0
    n_draft = 0
    for label in drafts:
        if label.get("pending") or label.get("invalid_reason") or not label.get("model"):
            continue
        n_draft += 1
        final = finals.get((label["worker_id"], label["checkpoint_turn"]))
        if label["checkout_recommended"]:
            n_draft_checkout += 1
        if final is None:
            continue
        if label["checkout_recommended"] and not final["checkout_recommended"]:
            n_corrected += 1
        elif label["checkout_recommended"] and final["checkout_recommended"]:
            n_agree_checkout += 1
        elif not label["checkout_recommended"] and not final["checkout_recommended"]:
            n_agree_not_yet += 1
    return {
        "voting": False,
        "n_draft_rows": n_draft,
        "n_draft_checkout": n_draft_checkout,
        "n_corrected_to_not_yet": n_corrected,
        "n_agree_not_yet": n_agree_not_yet,
        "n_agree_checkout": n_agree_checkout,
        "note": (
            "Unsigned role=draft rows are not votes. "
            "a0_if_drafts_voted is what earliest-unanimous would have been if they voted. "
            "It is not gold_exit."
        ),
    }


def aggregate_labels(
    labels: list[dict[str, Any]],
    *,
    primary_min_judges: int = PRIMARY_MIN_JUDGES,
    diagnostic_min_judges: int = DIAGNOSTIC_MIN_JUDGES,
) -> dict[str, Any]:
    """Earliest-unanimous gold plus agreement. Null recommendations stay pending.

    Unsigned drafts are excluded from the vote. They are counted in
    ``draft_review`` so a Flash checkout that Sonnet corrected stays visible
    without becoming a gold exit.
    """
    prepared: list[dict[str, Any]] = []
    for label in labels:
        if not isinstance(label, dict):
            continue
        norm = normalize_label(label)
        if norm is not None:
            prepared.append(norm)
    usable, n_duplicates = _dedupe(prepared)
    voting = [label for label in usable if is_voting_label(label)]
    drafts = [label for label in usable if not is_voting_label(label)]
    by_worker: dict[str, list[dict[str, Any]]] = {}
    for label in voting:
        by_worker.setdefault(label["worker_id"], []).append(label)
    drafts_by_worker: dict[str, list[dict[str, Any]]] = {}
    for label in drafts:
        drafts_by_worker.setdefault(label["worker_id"], []).append(label)

    worker_rows: list[dict[str, Any]] = []
    alpha_units: list[list[str | None]] = []
    pairwise: dict[str, list[tuple[str, str]]] = {}
    n_filled = 0
    n_pending = 0
    n_invalid = 0

    for worker_id in sorted(by_worker):
        group = by_worker[worker_id]
        filled = [
            label
            for label in group
            if label.get("model") and label.get("invalid_reason") is None and not label.get("pending")
        ]
        invalid = [label for label in group if label.get("invalid_reason")]
        pending = [label for label in group if label.get("pending") or not label.get("model")]
        n_filled += len(filled)
        n_pending += len(pending)
        n_invalid += len(invalid)
        turns = sorted({label["checkpoint_turn"] for label in filled})
        judges = sorted({label["model"] for label in filled if label.get("model")})
        T_values = [label["T"] for label in group if isinstance(label.get("T"), int)]
        T = max(T_values) if T_values else None
        votes: dict[int, dict[str, bool]] = {}
        for label in filled:
            votes.setdefault(label["checkpoint_turn"], {})[label["model"]] = bool(label["checkout_recommended"])

        def earliest(min_judges: int, *, unanimous: bool) -> int | None:
            for turn in turns:
                ballot = votes.get(turn, {})
                if len(ballot) < min_judges:
                    continue
                n_yes = sum(1 for bit in ballot.values() if bit)
                if unanimous and n_yes == len(ballot):
                    return turn
                if not unanimous and n_yes >= _majority_threshold(len(ballot)):
                    return turn
            return None

        judge_first: dict[str, int | None] = {}
        for judge in judges:
            first = None
            for turn in turns:
                ballot = votes.get(turn, {})
                if judge in ballot and ballot[judge]:
                    first = turn
                    break
            judge_first[judge] = first
        finite = [turn for turn in judge_first.values() if turn is not None]
        never = [judge for judge, turn in judge_first.items() if turn is None]
        guesses: dict[str, list[int | None]] = {}
        for label in filled:
            guesses.setdefault(label["model"], [])
            if label["first_checkout_turn_guess"] not in guesses[label["model"]]:
                guesses[label["model"]].append(label["first_checkout_turn_guess"])
        guess_report = {}
        for judge, values in guesses.items():
            distinct = [value for value in values if value is not None]
            guess_report[judge] = {
                "values": values,
                "conflict": len(set(distinct)) > 1,
            }

        panel_powered = len(judges) >= primary_min_judges and bool(turns)
        # Primary walk skips turns below three returned labels (TUNING-PLAN).
        gold_exit = earliest(primary_min_judges, unanimous=True) if panel_powered else None
        if not judges:
            panel = "pending"
        elif panel_powered:
            panel = "powered"
        else:
            panel = "underpowered"
        draft_votes: dict[int, dict[str, bool]] = {}
        for label in drafts_by_worker.get(worker_id, []):
            if label.get("model") and label.get("invalid_reason") is None and not label.get("pending"):
                draft_votes.setdefault(label["checkpoint_turn"], {})[label["model"]] = bool(
                    label["checkout_recommended"]
                )
        combined: dict[int, dict[str, bool]] = {}
        for turn in sorted(set(votes) | set(draft_votes)):
            combined[turn] = {**draft_votes.get(turn, {}), **votes.get(turn, {})}

        def earliest_combined(min_judges: int) -> int | None:
            for turn in sorted(combined):
                ballot = combined[turn]
                if len(ballot) < min_judges:
                    continue
                if all(ballot.values()):
                    return turn
            return None

        # Observation only. Unsigned drafts still do not set gold_exit.
        a0_if_drafts_voted = earliest_combined(diagnostic_min_judges)

        if panel == "powered":
            gold_status = "established"
        elif panel == "underpowered":
            gold_status = "underpowered"
        else:
            gold_status = "pending"

        turn_rows = []
        for turn in turns:
            ballot = votes.get(turn, {})
            turn_rows.append(
                {
                    "checkpoint_turn": turn,
                    "n": len(ballot),
                    "n_checkout": sum(1 for bit in ballot.values() if bit),
                    "unanimous_checkout": bool(ballot) and all(ballot.values()),
                    "votes": ballot,
                }
            )
            if len(ballot) >= 2:
                coder_values: list[str | None] = [
                    "checkout" if ballot[judge] else "not_yet" for judge in judges if judge in ballot
                ]
                alpha_units.append(coder_values)
                ordered_judges = [judge for judge in judges if judge in ballot]
                for i, left in enumerate(ordered_judges):
                    for right in ordered_judges[i + 1 :]:
                        key = f"{left}|{right}"
                        pairwise.setdefault(key, []).append(
                            ("checkout" if ballot[left] else "not_yet", "checkout" if ballot[right] else "not_yet")
                        )

        spread = (max(finite) - min(finite)) if len(finite) >= 2 else None
        a2 = None
        if panel_powered and len(finite) * 2 >= len(judges):
            a2 = _median_up(finite, turns)
        worker_rows.append(
            {
                "worker_id": worker_id,
                "T": T,
                "panel": panel,
                "gold_status": gold_status,
                "primary": gold_status == "established",
                "n_judges": len(judges),
                "judges": judges,
                "gold_exit": gold_exit,
                "gold_exit_rule": "A0",
                "A0": gold_exit,
                "A1": earliest(primary_min_judges, unanimous=False) if panel_powered else None,
                "A2": a2,
                "A3": "inapplicable",
                "A3_reason": "Dawid–Skene is inapplicable below 30 workers (Dawid and Skene, 1979).",
                "gold_exit_unanimous_min2": earliest(diagnostic_min_judges, unanimous=True),
                "a0_if_drafts_voted": a0_if_drafts_voted,
                "judge_first_checkout": judge_first,
                "never_checkout": never,
                "spread": spread,
                "first_checkout_turn_guess": guess_report,
                "turns": turn_rows,
            }
        )

    alpha = krippendorff_alpha(alpha_units, level="nominal") if alpha_units else None
    kappa = {
        pair: cohen_kappa(pairs)
        for pair, pairs in sorted(pairwise.items())
    }
    considered = n_filled + n_invalid
    invalid_rate = (n_invalid / considered) if considered else None
    any_powered = any(row["panel"] == "powered" for row in worker_rows)
    any_underpowered = any(row["panel"] == "underpowered" for row in worker_rows)
    if any_powered and alpha is not None:
        h5_pass = alpha >= H5_ALPHA_FLOOR
        h5 = "pass" if h5_pass else "below_floor"
    elif any_underpowered:
        h5_pass = None
        h5 = "underpowered"
    else:
        h5_pass = None
        h5 = "not_run"
    if not worker_rows or all(row["gold_status"] == "pending" for row in worker_rows):
        status = "pending"
    elif any_powered and h5 == "pass":
        status = "diagnostic"
    else:
        status = "diagnostic"
    n_prefixes = len(alpha_units)
    n_judges_min = min((len(unit) for unit in alpha_units), default=0)
    filled_voting = [
        label
        for label in voting
        if label.get("model") and label.get("invalid_reason") is None and not label.get("pending")
    ]
    seat_models: dict[str, list[str]] = {seat: [] for seat, _aliases in PANEL_SEATS}
    for label in filled_voting:
        seat = seat_for_model(label["model"])
        if seat and label["model"] not in seat_models[seat]:
            seat_models[seat].append(label["model"])
    seats = []
    for seat, _aliases in PANEL_SEATS:
        models = seat_models[seat]
        seats.append(
            {
                "seat": seat,
                "status": "filled" if models else "pending",
                "voting": bool(models),
                "models": models,
            }
        )
    draft_pairs = _draft_review(drafts, voting)
    return {
        "status": status,
        "confidence": "not-high",
        "gold_rule": "A0",
        "primary_min_judges": primary_min_judges,
        "diagnostic_min_judges": diagnostic_min_judges,
        "alpha": alpha,
        "alpha_method": "krippendorff_nominal",
        "alpha_method_note": ALPHA_METHOD_NOTE,
        "alpha_ordinal": None,
        "alpha_ordinal_note": (
            "Ordinal Krippendorff alpha is implemented as krippendorff_alpha(..., level='ordinal') "
            "and applies to ordered scores. Boolean checkout_recommended has no ordinal scale, "
            "so this field stays null on CHM verdicts."
        ),
        "n_prefixes": n_prefixes,
        "n_judges_min": n_judges_min,
        "n_labels_filled": n_filled,
        "n_labels_pending": n_pending,
        "n_labels_invalid": n_invalid,
        "n_labels_draft": draft_pairs["n_draft_rows"],
        "seats": seats,
        "draft_review": draft_pairs,
        "n_duplicate_keys": n_duplicates,
        "invalid_label_rate": invalid_rate,
        "pairwise_kappa": kappa,
        "h5_pass": h5_pass,
        "h5": h5,
        "h5_floor": H5_ALPHA_FLOOR,
        "note": (
            "Voting rows are signed=true. On the 2026-10-01 JSONL that is the Sonnet "
            "reviewer_final seat. Unsigned Flash drafts do not vote. "
            "grok-4.7-high and composer are pending seats. "
            "gold_exit stays null until three seats have voted at the turn; "
            "a null gold_exit on this file is an incomplete panel, not a decision to run to T. "
            "a0_if_drafts_voted is not gold_exit. Confidence is not high."
        ),
        "workers": worker_rows,
    }


def load_metrics_T(paths: list[Path]) -> dict[str, dict[str, Any]]:
    """worker_id -> {T, interval} from replay metrics JSON or the ubuntu-raw SUMMARY."""
    found: dict[str, dict[str, Any]] = {}

    def take(worker_id: str, payload: dict[str, Any]) -> None:
        T = _as_int(payload.get("T"))
        schedule = payload.get("schedule") if isinstance(payload.get("schedule"), dict) else {}
        interval = _as_int(schedule.get("interval")) if schedule else _as_int(payload.get("interval"))
        if isinstance(payload.get("schedule"), str) and ":" in payload["schedule"]:
            interval = _as_int(payload["schedule"].split(":")[1])
        slot = found.setdefault(worker_id, {})
        if T is not None:
            slot["T"] = T
        if interval is not None:
            slot["interval"] = interval

    for path in paths:
        doc = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(doc, dict):
            continue
        workers = doc.get("workers")
        if isinstance(workers, list):
            for row in workers:
                if isinstance(row, dict) and isinstance(row.get("worker_id"), str):
                    take(row["worker_id"], row)
        elif isinstance(workers, dict):
            for worker_id, row in workers.items():
                if isinstance(row, dict):
                    take(str(worker_id), row)
        elif isinstance(doc.get("worker_id"), str):
            take(doc["worker_id"], doc)
    return found


def load_replay_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.suffix == ".jsonl":
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    item = json.loads(line)
                    if isinstance(item, dict):
                        rows.append(item)
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(doc, list):
            rows.extend(item for item in doc if isinstance(item, dict))
        elif isinstance(doc, dict) and isinstance(doc.get("rows"), list):
            rows.extend(item for item in doc["rows"] if isinstance(item, dict))
    return rows


def score_replay(
    rows: list[dict[str, Any]],
    gold_summary: dict[str, Any],
    *,
    metrics: dict[str, dict[str, Any]] | None = None,
    interval_default: int = 15,
) -> dict[str, Any]:
    """Compare replay ``fires`` rows to primary ``gold_exit``.

    Pending and underpowered gold leave overshoot / false_early / false_late null.
    ``max_allowed_turns`` still follows the replay: gate exit, otherwise ``T``.
    """
    from session_checkout import gate_exit_from_rows, outcome_vs_gold

    metrics = metrics or {}
    by_worker: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        worker = row.get("worker_id")
        if isinstance(worker, str):
            by_worker.setdefault(worker, []).append(row)
    gold_by_id = {
        row["worker_id"]: row
        for row in gold_summary.get("workers", [])
        if isinstance(row, dict) and isinstance(row.get("worker_id"), str)
    }
    worker_ids = sorted(set(by_worker) | set(metrics) | set(gold_by_id))
    scored_rows: list[dict[str, Any]] = []
    for worker_id in worker_ids:
        replay_rows = by_worker.get(worker_id, [])
        meta = metrics.get(worker_id, {})
        gold = gold_by_id.get(worker_id, {})
        T = meta.get("T")
        if T is None:
            T = gold.get("T")
        interval = meta.get("interval") or interval_default
        fires_known = all("fires" in row for row in replay_rows) if replay_rows else True
        gate = gate_exit_from_rows(replay_rows) if fires_known else None
        gold_status = gold.get("gold_status", "absent")
        primary = bool(gold.get("primary"))
        gold_exit = gold.get("gold_exit") if primary else None
        record: dict[str, Any] = {
            "worker_id": worker_id,
            "T": T,
            "gate_exit": gate if fires_known else None,
            "fires_known": fires_known,
            "gold_status": gold_status,
            "gold_exit": gold_exit,
            "diagnostic_gold_exit_min2": gold.get("gold_exit_unanimous_min2"),
            "interval": interval,
            "scored": False,
            "overshoot": None,
            "false_early": None,
            "false_late": None,
            "on_time": None,
            "within_one_interval": None,
            "max_allowed_turns": None,
        }
        if isinstance(T, int):
            record["max_allowed_turns"] = gate if gate is not None else T
        if not fires_known:
            record["reason"] = "replay rows lack fires; gate_exit was not inferred"
        elif gold_status != "established" or not primary or "gold_exit" not in gold:
            record["reason"] = (
                "primary gold_exit is unset "
                f"(gold_status={gold_status}). Comparison fields stay null."
            )
        else:
            outcome = outcome_vs_gold(T=T if isinstance(T, int) else 0, gate_exit=gate, gold_exit=gold_exit)
            if not isinstance(T, int):
                outcome["max_allowed_turns"] = None
                record["reason"] = "T is unknown, so max_allowed_turns is null. Pass --metrics."
            record.update(outcome)
            if outcome["overshoot"] is not None:
                record["within_one_interval"] = abs(outcome["overshoot"]) <= interval
            else:
                record["within_one_interval"] = False
            record["scored"] = True
            record["reason"] = None
        scored_rows.append(record)
    any_scored = any(row["scored"] for row in scored_rows)
    return {
        "status": "diagnostic" if any_scored else "blocked_no_gold",
        "confidence": "not-high",
        "note": (
            "Scores use primary gold_exit only (A0, three judges). "
            "Pending labels and the two-judge diagnostic exit are not substituted. "
            "Dry-run replays have fires false, so max_allowed_turns stays T. "
            "That is fail-open with no Jev answer. It is not a gold exit. "
            "Confidence is not high."
        ),
        "workers": scored_rows,
    }
