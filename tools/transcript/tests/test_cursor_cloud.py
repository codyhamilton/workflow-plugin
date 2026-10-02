"""Cloud-run cache metadata must never be mistaken for a transcript."""

from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from parsers.cursor_cloud import CursorCloudParser


class CursorCloudTests(unittest.TestCase):
    def test_discovery_and_extraction_keep_turns_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / "state.vscdb")
            conn = sqlite3.connect(db)
            conn.execute("CREATE TABLE ItemTable (key TEXT, value BLOB)")
            conn.execute("INSERT INTO ItemTable VALUES (?, ?)", (
                "cloudAgentRepository.agents.account",
                json.dumps([
                    {"bcId": "bc-11111111-1111-1111-1111-111111111111", "createdAt": 1_700_000_000_000,
                     "updatedAt": 1_700_000_010_000, "workspaceRootPath": "/workspace", "name": "build"},
                    {"bcId": "bc-22222222-2222-2222-2222-222222222222", "createdAt": 1_700_000_020_000,
                     "workspaceRootPath": "/other", "name": "review"},
                ]),
            ))
            conn.commit()
            conn.close()

            parser = CursorCloudParser(db)
            self.assertEqual(len(parser.discover_all()), 2)
            self.assertEqual(len(parser.discover("/workspace")), 1)
            self.assertEqual(len(parser.discover_all(match="review")), 1)
            self.assertEqual(len(parser.discover_all(min_subagents=1)), 0)
            ref = parser.resolve("bc-111", None)
            session = parser.extract(ref).session
            self.assertFalse(session["transcript_available"])
            self.assertIsNone(session["parent_assistant_turns"])
            self.assertIsNone(session["assistant_turns"])
            self.assertIsNone(session["user_turns"])
            self.assertEqual(session["wall_seconds"], 10)
            with self.assertRaisesRegex(ValueError, "unavailable"):
                parser.search(ref, "test")


BC_FULL = "bc-33333333-3333-3333-3333-333333333333"
BC_HDR_ONLY = "bc-44444444-4444-4444-4444-444444444444"
BC_INDEXED = "bc-55555555-5555-5555-5555-555555555555"
BC_NONE = "bc-66666666-6666-6666-6666-666666666666"


def _make_dbs(tmp: str) -> tuple[str, str]:
    db = str(Path(tmp) / "state.vscdb")
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE ItemTable (key TEXT, value BLOB)")
    conn.execute("CREATE TABLE cursorDiskKV (key TEXT UNIQUE ON CONFLICT REPLACE, value BLOB)")
    conn.execute("INSERT INTO ItemTable VALUES (?, ?)", (
        "cloudAgentRepository.agents.account",
        json.dumps([{"bcId": b, "createdAt": 1_700_000_000_000} for b in (BC_FULL, BC_HDR_ONLY, BC_INDEXED, BC_NONE)]),
    ))
    # Local composer linked to a cloud run, with all bubbles present.
    hdr = lambda i, t: {"bubbleId": f"b{i}", "type": t}
    conn.execute("INSERT INTO cursorDiskKV VALUES (?, ?)", ("composerData:local-1", json.dumps({
        "createdFromBackgroundAgent": {"bcId": BC_FULL, "shouldStreamMessages": True},
        "fullConversationHeadersOnly": [hdr(0, 1), hdr(1, 2), hdr(2, 2)],
    })))
    bubbles = [
        {"bubbleId": "b0", "type": 1, "text": "synthetic prompt needle"},
        {"bubbleId": "b1", "type": 2, "toolFormerData": {"name": "read_file_v2", "rawArgs": "{}"}},
        {"bubbleId": "b2", "type": 2, "text": "synthetic answer"},
    ]
    for i, b in enumerate(bubbles):
        conn.execute("INSERT INTO cursorDiskKV VALUES (?, ?)", (f"bubbleId:local-1:b{i}", json.dumps(b)))
    # Run-keyed composer with headers but no bubble bodies (evicted).
    conn.execute("INSERT INTO cursorDiskKV VALUES (?, ?)", (f"composerData:{BC_HDR_ONLY}", json.dumps({
        "fullConversationHeadersOnly": [hdr(0, 1), hdr(1, 2)],
    })))
    conn.execute("INSERT INTO cursorDiskKV VALUES (?, ?)", (f"bubbleId:{BC_HDR_ONLY}:b0", None))
    conn.commit()
    conn.close()

    sdb = str(Path(tmp) / "conversation-search.db")
    conn = sqlite3.connect(sdb)
    conn.execute("CREATE TABLE conversations (fts_rowid INTEGER PRIMARY KEY, source TEXT, id TEXT)")
    conn.execute("CREATE VIRTUAL TABLE conversation_fts USING fts5(title, body, branches)")
    conn.execute("INSERT INTO conversation_fts(rowid, title, body, branches) VALUES (1, 't', ?, '')",
                 ("user:\nhello needle\n\nassistant:\nreply one\n\nassistant:\nreply two\n",))
    conn.execute("INSERT INTO conversations VALUES (1, 'cloud-cache', ?)", (BC_INDEXED,))
    conn.commit()
    conn.close()
    return db, sdb


class CursorCloudBodyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.parser = CursorCloudParser(*_make_dbs(self.tmp.name))

    def _session(self, bc: str) -> dict:
        return self.parser.extract(self.parser.resolve(bc, None)).session

    def test_complete_bubbles_give_exact_turns_and_tool_calls(self) -> None:
        s = self._session(BC_FULL)
        self.assertTrue(s["transcript_available"])
        self.assertTrue(s["transcript_complete"])
        self.assertEqual((s["parent_user_turns"], s["parent_assistant_turns"], s["parent_tool_turns"]), (1, 2, 1))
        hits = self.parser.search(self.parser.resolve(BC_FULL, None), "needle")
        self.assertEqual([(h.role, h.msg_idx) for h in hits], [("user", 0)])

    def test_headers_without_bodies_stay_unknown(self) -> None:
        s = self._session(BC_HDR_ONLY)
        self.assertFalse(s["transcript_available"])
        self.assertEqual((s["bubble_headers"], s["bubbles_present"]), (2, 0))
        self.assertIsNone(s["parent_assistant_turns"])
        self.assertIsNone(s["observed_assistant_turns"])

    def test_indexed_text_is_partial_lower_bound(self) -> None:
        s = self._session(BC_INDEXED)
        self.assertTrue(s["transcript_available"])
        self.assertFalse(s["transcript_complete"])
        self.assertEqual((s["observed_user_turns"], s["observed_assistant_turns"]), (1, 2))
        self.assertIsNone(s["parent_assistant_turns"])
        self.assertEqual(len(self.parser.search(self.parser.resolve(BC_INDEXED, None), "needle")), 1)

    def test_run_without_any_body(self) -> None:
        s = self._session(BC_NONE)
        self.assertFalse(s["transcript_available"])
        self.assertIsNone(s["parent_assistant_turns"])
        with self.assertRaisesRegex(ValueError, "unavailable"):
            self.parser.search(self.parser.resolve(BC_NONE, None), "x")


if __name__ == "__main__":
    unittest.main()
