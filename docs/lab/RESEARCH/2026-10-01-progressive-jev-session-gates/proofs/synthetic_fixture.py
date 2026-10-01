"""Tiny Claude-shaped JSONL so proofs run without the maps corpus."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def synthetic_rows(turns: int = 90) -> list[dict[str, Any]]:
    """``turns`` unique assistant ids, plus one duplicate id and one compaction row.

    Turn 75's visible text contains a fake secret so redaction can be asserted.
    Every 5th turn reads ``src/repeat.py``.
    """
    secret = "api_key=supersecretvalue1234567890"
    rows: list[dict[str, Any]] = [
        {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Implement the session gate harness. {secret}",
                    }
                ],
            },
        }
    ]
    for number in range(1, turns + 1):
        content: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": secret if number == 75 else f"turn {number} working on the brief",
            }
        ]
        if number % 5 == 0:
            content.append(
                {
                    "type": "tool_use",
                    "name": "Read",
                    "id": f"tool-read-{number}",
                    "input": {"file_path": "src/repeat.py"},
                }
            )
            content.append(
                {
                    "type": "tool_use",
                    "name": "Bash",
                    "id": f"tool-bash-{number}",
                    "input": {"command": "pytest"},
                }
            )
        if number == 10:
            content.append(
                {
                    "type": "tool_use",
                    "name": "Read",
                    "id": "tool-read-once",
                    "input": {"file_path": "src/once.py"},
                }
            )
        rows.append(
            {
                "type": "assistant",
                "message": {
                    "id": f"msg-{number:03d}",
                    "role": "assistant",
                    "content": content,
                    "usage": {
                        "input_tokens": 100 * number,
                        "cache_read_input_tokens": 0,
                        "cache_creation_input_tokens": 0,
                    },
                },
            }
        )
        if number == 1:
            rows.append(
                {
                    "type": "assistant",
                    "message": {
                        "id": "msg-001",
                        "role": "assistant",
                        "content": [{"type": "text", "text": " continued"}],
                        "usage": {
                            "input_tokens": 100,
                            "cache_read_input_tokens": 0,
                            "cache_creation_input_tokens": 0,
                        },
                    },
                }
            )
        if number == 40:
            rows.append(
                {
                    "type": "system",
                    "subtype": "compact_boundary",
                    "content": "Conversation compacted",
                }
            )
    return rows


def write_synthetic(path: Path, turns: int = 90) -> None:
    lines = [json.dumps(row, ensure_ascii=False) for row in synthetic_rows(turns)]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    destination = Path(__file__).resolve().parent / "fixtures" / "synthetic_worker_90.jsonl"
    write_synthetic(destination)
    print(destination)
