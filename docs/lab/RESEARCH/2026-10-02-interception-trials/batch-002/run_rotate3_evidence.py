#!/usr/bin/env python3
"""Build the rotate-3 Soft HOLD adjudication, digest, and join artifacts.

This command is deliberately offline.  It reads the committed outcome
sidecar, prefix snapshot packs, local OpenCode metadata when available, and
TypeSafe/Luna result rows.  It never calls a model, writes a raw capture, or
computes an FP/miss scoreboard.

The blind corpus and digest bundle omit all outcome labels and window values.
The separate tail/control manifests are provenance reports and therefore may
name their reference status, but remain descriptive and Soft HOLD.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from typing import Any

BATCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BATCH.parents[4] / "tools" / "interception"))

from window_status_join import FIXED_SCHEDULE, derive_rows, index_labels, load_jsonl


LABELS_PATH = BATCH / "outcome-labels.jsonl"
PACK_DIRS = ("snapshots-dense", "snapshots-mid", "snapshots")
RESULT_PREFIXES = ("typesafe", "luna")
SOFT_HOLD = {
    "soft_standard_hold": True,
    "product_wiring": False,
    "hooks": False,
    "standard_unlock": False,
    "local_8080": False,
    "not_scoreboard": True,
    "metrics_computed": False,
}
LEAK_KEYS = {
    "near_done",
    "near_done_at_checkpoint",
    "runaway_like",
    "runaway_like_at_checkpoint",
    "ideal_steer_window",
    "ideal_steer_window_by_cp",
    "window_status",
    "termination_cause",
    "human_steer_count",
    "maps_family",
    "T_eligibility_only",
    "path",
    "worker_id",
    "project",
    "session_id",
}


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def load_packs() -> dict[str, dict[str, Any]]:
    """Select the densest available pack for each worker without leaking paths."""
    candidates: dict[str, list[tuple[int, int, Path, dict[str, Any]]]] = {}
    for priority, directory_name in enumerate(PACK_DIRS):
        directory = BATCH / directory_name
        for path in sorted(directory.glob("*.json")):
            try:
                pack = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            worker_id = pack.get("worker_id") or path.stem
            checkpoints = pack.get("checkpoints") or []
            if not worker_id or not checkpoints:
                continue
            candidates.setdefault(worker_id, []).append(
                (len(checkpoints), -priority, path, pack)
            )
    return {
        worker_id: max(rows, key=lambda row: (row[0], row[1], str(row[2])))[3]
        for worker_id, rows in candidates.items()
    }


def strip_leaks(value: Any) -> Any:
    """Remove labels, source identity, and terminal information recursively."""
    if isinstance(value, dict):
        return {
            key: strip_leaks(child)
            for key, child in value.items()
            if key not in LEAK_KEYS
        }
    if isinstance(value, list):
        return [strip_leaks(child) for child in value]
    return value


def snapshot_tail_metadata(state: dict[str, Any]) -> dict[str, Any] | None:
    tail = state.get("tail")
    if not isinstance(tail, list) or not tail:
        return None
    entries = []
    for offset, item in enumerate(tail, start=-len(tail) + 1):
        if not isinstance(item, dict):
            item = {"value": item}
        entries.append(
            {
                "relative_turn": offset,
                "tool_names": sorted(str(name) for name in item.get("tool_names", [])),
                "excerpt_present": bool(item.get("excerpt")),
                "excerpt_digest": digest(item.get("excerpt", "")),
            }
        )
    return {"entry_count": len(entries), "entries": entries}


def opencode_tail_metadata(pack: dict[str, Any], checkpoint: int) -> dict[str, Any] | None:
    """Return digest-only tail metadata from a local OpenCode SQLite session.

    The database path is never written to an artifact and part content is
    hashed rather than copied.  If the local store is unavailable, the
    positive remains explicitly gated.
    """
    source = str(pack.get("path") or "")
    marker = "#session/"
    if not source.startswith("sqlite:") or marker not in source:
        return None
    database, session_id = source[len("sqlite:") :].split(marker, 1)
    try:
        connection = sqlite3.connect(database)
        messages = list(
            connection.execute(
                "select id, data from message where session_id=? order by time_created",
                (session_id,),
            )
        )
        assistant_messages = [
            (message_id, json.loads(data))
            for message_id, data in messages
            if json.loads(data).get("role") == "assistant"
        ]
        selected = assistant_messages[:checkpoint][-8:]
        entries = []
        for index, (message_id, message_data) in enumerate(selected, start=-len(selected) + 1):
            parts = []
            for part_data, in connection.execute(
                "select data from part where message_id=? order by time_created",
                (message_id,),
            ):
                part = json.loads(part_data)
                parts.append(
                    {
                        "type": part.get("type"),
                        "tool": part.get("tool"),
                        "has_text": bool(part.get("text")),
                        "part_digest": digest(part),
                    }
                )
            entries.append(
                {
                    "relative_turn": index,
                    "part_types": [part["type"] for part in parts],
                    "tool_names": sorted(
                        str(part["tool"]) for part in parts if part.get("tool")
                    ),
                    "part_digests": [part["part_digest"] for part in parts],
                    "text_parts": sum(part["has_text"] for part in parts),
                }
            )
        connection.close()
    except (OSError, sqlite3.Error, json.JSONDecodeError):
        return None
    if len(selected) < 8:
        return None
    return {
        "entry_count": len(entries),
        "entries": entries,
        "source_kind": "local_opencode_sqlite_digest_only",
    }


def exact_key_rows(labels: dict[str, dict[str, Any]], packs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for session_id in sorted(labels):
        label = labels[session_id]
        if label.get("label_status") != "labeled":
            continue
        near = label.get("near_done_at_checkpoint") or {}
        runaway = label.get("runaway_like_at_checkpoint") or {}
        for checkpoint_key in sorted(set(near) | set(runaway), key=int):
            checkpoint = int(checkpoint_key)
            pack = packs.get(session_id)
            checkpoint_row = next(
                (
                    row
                    for row in (pack or {}).get("checkpoints", [])
                    if int(row.get("checkpoint", -1)) == checkpoint
                ),
                None,
            )
            state = (checkpoint_row or {}).get("full_state") or {}
            clean_state = strip_leaks(state)
            tail = snapshot_tail_metadata(state)
            if tail is None and pack is not None:
                tail = opencode_tail_metadata(pack, checkpoint)
            review_id = hashlib.sha256(
                f"rotate-3-review\0{session_id}\0{checkpoint}".encode()
            ).hexdigest()[:24]
            rows.append(
                {
                    "review_id": review_id,
                    "checkpoint": checkpoint,
                    "checkpoint_in_fixed_schedule": str(checkpoint) in FIXED_SCHEDULE,
                    "prefix_state": clean_state,
                    "prefix_state_digest": digest(clean_state),
                    "tail_digest_metadata": tail,
                    "tail_digest_available": tail is not None,
                    "reference_values_embedded": False,
                    "judge_fields_embedded": False,
                    "label_values_embedded": False,
                }
            )
    return rows


def adjudication_templates(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    def template(adjudicator: str) -> list[dict[str, Any]]:
        return [
            {
                "review_id": row["review_id"],
                "adjudicator": adjudicator,
                "near_done": None,
                "runaway_like": None,
                "ideal_steer_window": None,
                "confidence": None,
                "rationale": None,
                "completed": False,
            }
            for row in rows
        ]
    return template("A"), template("B")


def non_maps_controls(
    labels: dict[str, dict[str, Any]], packs: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    rows = []
    for session_id, pack in sorted(packs.items()):
        project = str(pack.get("project") or "")
        if "open-pajero-maps" in project:
            continue
        checkpoints = sorted(
            pack.get("checkpoints") or [], key=lambda row: int(row["checkpoint"])
        )
        if not checkpoints:
            continue
        checkpoint = int(checkpoints[len(checkpoints) // 2]["checkpoint"])
        label = labels.get(session_id) or {}
        is_labeled = (
            label.get("label_status") == "labeled"
            and str(checkpoint) in (label.get("near_done_at_checkpoint") or {})
            and str(checkpoint) in (label.get("runaway_like_at_checkpoint") or {})
        )
        rows.append(
            {
                "control_id": hashlib.sha256(
                    f"rotate-3-control\0{session_id}\0{checkpoint}".encode()
                ).hexdigest()[:24],
                "session_id": session_id,
                "checkpoint": checkpoint,
                "harness": pack.get("harness"),
                "project": project,
                "label_status": "labeled_reference" if is_labeled else "unlabeled_holdout",
                "rationale": (
                    "No outcome sidecar row exists for this representative non-Maps "
                    "prefix; do not infer a negative label from judge output, window "
                    "absence, final length, or lack of a fire."
                    if not is_labeled
                    else "Retain the existing exact sidecar label as a reference control; "
                    "do not pool it with the unlabeled holdout."
                ),
                "preferred_action": (
                    "Keep unlabeled until an independent adjudicator records a complete "
                    "checkpoint sheet."
                    if not is_labeled
                    else "Use only in the labeled reference stratum after independent "
                    "agreement is retained."
                ),
            }
        )
    return rows


def tail_positive_manifest(
    labels: dict[str, dict[str, Any]], packs: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    rows = []
    for session_id, label in sorted(labels.items()):
        for checkpoint_key, value in sorted(
            (label.get("runaway_like_at_checkpoint") or {}).items(), key=lambda item: int(item[0])
        ):
            if value != "yes":
                continue
            checkpoint = int(checkpoint_key)
            pack = packs.get(session_id) or {}
            state = next(
                (
                    row.get("full_state") or {}
                    for row in pack.get("checkpoints", [])
                    if int(row.get("checkpoint", -1)) == checkpoint
                ),
                {},
            )
            tail = snapshot_tail_metadata(state) or opencode_tail_metadata(pack, checkpoint)
            rows.append(
                {
                    "session_id": session_id,
                    "checkpoint": checkpoint,
                    "reference_label": "runaway_like=yes",
                    "ideal_steer_window": label.get("ideal_steer_window"),
                    "tail_digest_available": tail is not None,
                    "tail_source": (
                        "snapshot" if snapshot_tail_metadata(state) is not None
                        else "local_opencode_sqlite_digest_only" if tail is not None
                        else "unavailable"
                    ),
                    "gate_status": (
                        "evidence_recovered_not_independently_adjudicated"
                        if tail is not None
                        else "still_tail_gated"
                    ),
                    "independent_adjudication_required": True,
                    "not_a_scoreboard": True,
                }
            )
    return rows


def result_streams() -> list[Path]:
    return sorted(
        path
        for path in BATCH.glob("*/results.jsonl")
        if path.parent.name.startswith(RESULT_PREFIXES)
    )


def result_join(labels: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    joined: list[dict[str, Any]] = []
    streams = []
    excluded_streams = []
    invalid_join_key_rows = 0
    for path in result_streams():
        results = load_jsonl(path)
        valid_results = [
            result
            for result in results
            if isinstance(result.get("session_id"), str)
            and bool(result.get("session_id"))
            and isinstance(result.get("checkpoint"), int)
            and not isinstance(result.get("checkpoint"), bool)
        ]
        invalid_count = len(results) - len(valid_results)
        invalid_join_key_rows += invalid_count
        if not valid_results:
            excluded_streams.append(
                {
                    "stream": path.parent.name,
                    "result_rows": len(results),
                    "reason": "no exact session_id + checkpoint join keys",
                }
            )
            continue
        derived = derive_rows(valid_results, labels)
        for row in derived:
            row["source_result"] = str(path.relative_to(BATCH))
            joined.append(row)
        exact = sum(
            row["label_join_eligibility"] == "label_join_exact" for row in derived
        )
        unique = {(row["session_id"], row["checkpoint"]) for row in derived}
        exact_keys = {
            (row["session_id"], row["checkpoint"])
            for row in derived
            if row["label_join_eligibility"] == "label_join_exact"
        }
        streams.append(
            {
                "stream": path.parent.name,
                "result_rows": len(results),
                "joinable_result_rows": len(valid_results),
                "invalid_join_key_rows": invalid_count,
                "exact_join_rows": exact,
                "unjoined_rows": len(valid_results) - exact,
                "unique_session_checkpoints": len(unique),
                "exact_unique_session_checkpoints": len(exact_keys),
            }
        )
    eligibility = Counter(row["label_join_eligibility"] for row in joined)
    exact_keys = {
        (row["session_id"], row["checkpoint"])
        for row in joined
        if row["label_join_eligibility"] == "label_join_exact"
    }
    all_keys = {(row["session_id"], row["checkpoint"]) for row in joined}
    summary = {
        **SOFT_HOLD,
        "protocol_rev": "rotate-3-exact-key-join-v1",
        "join_key": ["session_id", "checkpoint"],
        "fixed_schedule": sorted(int(value) for value in FIXED_SCHEDULE),
        "result_streams": streams,
        "excluded_streams": excluded_streams,
        "source_rows": sum(stream["result_rows"] for stream in streams) + sum(
            stream["result_rows"] for stream in excluded_streams
        ),
        "joinable_result_rows": len(joined),
        "invalid_join_key_rows": invalid_join_key_rows,
        "exact_join_rows": eligibility["label_join_exact"],
        "unjoined_rows": len(joined) - eligibility["label_join_exact"],
        "unjoinable_total_rows": (
            len(joined)
            - eligibility["label_join_exact"]
            + invalid_join_key_rows
        ),
        "unique_session_checkpoints": len(all_keys),
        "exact_unique_session_checkpoints": len(exact_keys),
        "unjoined_unique_session_checkpoints": len(all_keys - exact_keys),
        "label_join_eligibility_rows": dict(sorted(eligibility.items())),
        "repeated_rows_are_independent_trials": False,
        "session_clustered_interpretation_required": True,
        "scoreboard_allowed": False,
    }
    return joined, summary


def main() -> int:
    labels = index_labels(load_jsonl(LABELS_PATH))
    packs = load_packs()
    corpus = exact_key_rows(labels, packs)
    blind = [
        {
            "review_id": row["review_id"],
            "checkpoint": row["checkpoint"],
            "checkpoint_in_fixed_schedule": row["checkpoint_in_fixed_schedule"],
            "prefix_state": row["prefix_state"],
            "prefix_state_digest": row["prefix_state_digest"],
            "tail_digest_metadata": row["tail_digest_metadata"],
            "tail_digest_available": row["tail_digest_available"],
            "reference_values_embedded": False,
            "judge_fields_embedded": False,
            "label_values_embedded": False,
        }
        for row in corpus
    ]
    template_a, template_b = adjudication_templates(corpus)
    controls = non_maps_controls(labels, packs)
    positives = tail_positive_manifest(labels, packs)
    joined, join_summary = result_join(labels)

    write_jsonl(BATCH / "rotate-3-independent-adjudication-corpus.jsonl", blind)
    write_jsonl(BATCH / "rotate-3-blind-digest-bundle.jsonl", blind)
    write_jsonl(BATCH / "rotate-3-adjudicator-a-template.jsonl", template_a)
    write_jsonl(BATCH / "rotate-3-adjudicator-b-template.jsonl", template_b)
    write_jsonl(BATCH / "rotate-3-result-join.jsonl", joined)
    write_json(BATCH / "rotate-3-non-maps-controls.json", {
        "protocol_rev": "rotate-3-non-maps-controls-v1",
        **SOFT_HOLD,
        "controls": controls,
        "counts": dict(Counter(row["label_status"] for row in controls)),
        "unlabeled_controls_have_rationale": all(
            row["label_status"] != "unlabeled_holdout" or bool(row["rationale"])
            for row in controls
        ),
    })
    write_json(BATCH / "rotate-3-tail-positive-manifest.json", {
        "protocol_rev": "rotate-3-tail-positive-v1",
        **SOFT_HOLD,
        "positives": positives,
        "counts": {
            "positive_keys": len(positives),
            "tail_digest_available": sum(row["tail_digest_available"] for row in positives),
            "still_tail_gated": sum(row["gate_status"] == "still_tail_gated" for row in positives),
        },
        "interpretation": (
            "A recovered digest establishes source availability only. It does not "
            "validate a label, create a hit/miss outcome, or unlock behavior."
        ),
    })
    write_json(BATCH / "rotate-3-result-join-meters.json", join_summary)
    write_json(BATCH / "rotate-3-adjudication-meters.json", {
        "protocol_rev": "rotate-3-independent-adjudication-v1",
        **SOFT_HOLD,
        "labeled_sidecar_sessions": sum(
            label.get("label_status") == "labeled" for label in labels.values()
        ),
        "blind_corpus_rows": len(blind),
        "blind_corpus_unique_review_ids": len({row["review_id"] for row in blind}),
        "adjudicator_templates": 2,
        "tail_positive_keys": len(positives),
        "tail_positive_keys_with_digest": sum(
            row["tail_digest_available"] for row in positives
        ),
        "non_maps_controls": len(controls),
        "non_maps_labeled_reference_controls": sum(
            row["label_status"] == "labeled_reference" for row in controls
        ),
        "non_maps_unlabeled_holdout_controls": sum(
            row["label_status"] == "unlabeled_holdout" for row in controls
        ),
        "independent_agreement": "not_run",
        "reference_validation": "not_complete",
        "remaining_gates": [
            "two independent completed adjudicator sheets",
            "retained agreement and adjudication-disagreement report",
            "exact-key TypeSafe/Luna join reviewed after adjudication",
            "session-clustered descriptive analysis only",
        ],
    })
    print(json.dumps({
        "blind_corpus_rows": len(blind),
        "tail_positive_keys": len(positives),
        "non_maps_controls": len(controls),
        "result_rows": join_summary["joinable_result_rows"],
        "exact_join_rows": join_summary["exact_join_rows"],
        "unjoined_rows": join_summary["unjoinable_total_rows"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
