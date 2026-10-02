"""Cursor turn counts come from message rows, not tool blocks or usage estimates."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.types import SessionRef
from parsers.cursor import CursorParser
from stats import compute_stats


def _write_rows(path: Path, rows: list[dict | str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as out:
        for row in rows:
            out.write((row if isinstance(row, str) else json.dumps(row)) + "\n")


def _row(role: str, *items: dict) -> dict:
    return {"role": role, "message": {"content": list(items)}}


class CursorTurnTests(unittest.TestCase):
    def test_parent_and_subagent_turns_are_message_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            session_dir = Path(tmp) / "session-id"
            parent = session_dir / "session-id.jsonl"
            _write_rows(parent, [
                _row("user", {"type": "text", "text": "<user_query>Build it</user_query>"}),
                _row("assistant", {"type": "text", "text": "Working"},
                     {"type": "tool_use", "name": "Read", "input": {}},
                     {"type": "tool_use", "name": "Shell", "input": {}}),
                {"type": "status", "status": "running"},
                _row("assistant", {"type": "text", "text": "Done"}),
                "{incomplete",
            ])
            _write_rows(session_dir / "subagents" / "child.jsonl", [
                _row("user", {"type": "text", "text": "Subtask"}),
                _row("assistant", {"type": "tool_use", "name": "Read", "input": {}}),
                _row("assistant", {"type": "text", "text": "Finished"}),
            ])

            data = CursorParser().extract(SessionRef("cursor", "session-id", None, str(parent))).to_dict()
            session = data["session"]
            self.assertEqual((session["parent_assistant_turns"], session["parent_user_turns"]), (2, 1))
            self.assertEqual((session["subagent_assistant_turns"], session["subagent_user_turns"]), (2, 1))
            self.assertEqual((session["assistant_turns"], session["user_turns"]), (4, 2))
            self.assertEqual(session["parent_tool_turns"], 2)
            self.assertEqual(data["subagents"][0]["total_tool_turns"], 1)
            self.assertIsNone(session["api_calls"])
            stats = compute_stats(data)
            self.assertEqual(stats["parent_assistant_turns"], 2)
            self.assertEqual(stats["assistant_turns"], 4)
            self.assertIsNone(stats["subagent_api_calls"])

    def test_same_session_id_in_different_paths_is_counted_per_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            counts = []
            for folder, n in (("a", 1), ("b", 3)):
                parent = Path(tmp) / folder / "same-id" / "same-id.jsonl"
                _write_rows(parent, [_row("assistant", {"type": "text", "text": "x"}) for _ in range(n)])
                data = CursorParser().extract(SessionRef("cursor", "same-id", None, str(parent))).to_dict()
                counts.append(data["session"]["parent_assistant_turns"])
            self.assertEqual(counts, [1, 3])


if __name__ == "__main__":
    unittest.main()
