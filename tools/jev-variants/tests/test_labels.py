import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import labels


def c(name, **i):
    return {"name": name, "input": i, "output": None}


class TestLabels(unittest.TestCase):
    def test_detectors(self):
        d = labels.detectors([c("Read", file_path="a.py"), c("Grep", pattern="x")])
        self.assertTrue(d["investigating-before-editing"])
        self.assertFalse(d["writing-main-implementation"])
        d = labels.detectors([c("Edit", file_path="docs/x.md")])
        self.assertTrue(d["docs-only-recordkeeping"])
        self.assertFalse(d["writing-main-implementation"])
        d = labels.detectors([c("Edit", file_path="src/a.py")])
        self.assertTrue(d["writing-main-implementation"])
        d = labels.detectors([c("Bash", command="python -m pytest -q")])
        self.assertTrue(d["last-test-run-green"])

    def test_auc(self):
        self.assertEqual(labels.auc([0.9], [0.1]), 1.0)
        self.assertIsNone(labels.auc([], [0.1]))

    def test_window_is_prefix(self):
        ev = [{"kind": "tool_batch", "turn": t, "calls": [c("Read", file_path=str(t))]} for t in (1, 2, 3)]
        self.assertEqual(len(labels.window_calls(ev, 2, 5)), 2)


if __name__ == "__main__":
    unittest.main()
