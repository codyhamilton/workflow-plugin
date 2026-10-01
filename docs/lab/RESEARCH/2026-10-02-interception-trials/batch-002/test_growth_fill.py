#!/usr/bin/env python3
"""Offline checks for growth_fill + sweep gating. Run: python3 test_growth_fill.py"""
import importlib.util, json, os, sys, tempfile, unittest
from pathlib import Path

BATCH = Path(__file__).resolve().parent
os.environ.setdefault('WF_REPO', str(BATCH.parents[4]))

def _load(name, fname):
    spec = importlib.util.spec_from_file_location(name, BATCH / fname)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m); return m

gf = _load('growth_fill', 'growth_fill.py')

TAIL = [
    {'turn': 1, 'excerpt': '', 'tool_names': ['Bash']},
    {'turn': 2, 'excerpt': '', 'tool_names': ['Bash']},
    {'turn': 3, 'excerpt': 'Tests failed with an error; retrying.', 'tool_names': []},
    {'turn': 4, 'excerpt': '', 'tool_names': ['Edit']},
    {'turn': 5, 'excerpt': 'Committed and pushed.', 'tool_names': []},
]
FULL = {'checkpoint_turn': 5, 'tail': TAIL, 'delta_since_prior': {},
        'cumulative': {'tool_histogram': {'Bash': 3, 'Edit': 1}, 'reread_paths': ['a'],
                       'compaction_event_count': 2}}

class Fill(unittest.TestCase):
    def test_derived_fields_nonempty(self):
        d = gf.derive_growth_fields(FULL)
        for f in ('markers', 'phase_hints', 'recent'):
            self.assertTrue(d[f], f)
        m = d['markers']
        self.assertEqual((m['tail_turns'], m['silent_tool_turns'], m['max_same_tool_run']), (5, 3, 2))
        self.assertGreaterEqual(m['error_terms'], 2)
        self.assertEqual(d['phase_hints']['tail_dominant_class'], 'exec')
        self.assertTrue(d['phase_hints']['closing_language'])
        self.assertEqual([r['turn'] for r in d['recent']], [2, 3, 4, 5])

    def test_gate_without_tail(self):
        lite = {'checkpoint_turn': 45, 'cumulative': {'api_turns': 45}}
        self.assertIsNone(gf.derive_growth_fields(lite))
        for mode in gf.GROWTH_FIELD:
            self.assertIsNone(gf.fill_growth_fields(lite, mode))

    def test_native_field_wins(self):
        full = {**FULL, 'markers': {'x': 1}}
        self.assertEqual(gf.fill_growth_fields(full, 'markers_focus')['markers'], {'x': 1})

    def test_no_leak_keys(self):
        blob = json.dumps(gf.derive_growth_fields(FULL))
        for k in ('progress', 'session_length', 'norm_length', 'schedule'):
            self.assertNotIn(k, blob)

    def test_real_corpus_coverage(self):
        rep = gf.coverage_report(BATCH)
        self.assertGreater(rep['n_eligible'], 0)
        self.assertEqual(rep['n_eligible'] + rep['n_gated_no_tail'], rep['n_sessions'])
        for f, n in rep['nonempty_after_fill'].items():
            self.assertEqual(n, rep['n_eligible'], f)

class Sweep(unittest.TestCase):
    def test_cells_filled_and_gated(self):
        sw = _load('sweep_under_test', 'run_typesafe_scenario_corpus_sweep.py')
        cells, packs, _sc, gated = sw.build_cells()
        growth = [c for c in cells if c['state_selection'] in gf.GROWTH_FIELD]
        self.assertTrue(growth)
        for c in growth:
            f = gf.GROWTH_FIELD[c['state_selection']]
            self.assertTrue(c['state'].get(f), (c['scenario_id'], c['session_id']))
            self.assertEqual(c['state_fill'], gf.FILL_VERSION)
            self.assertEqual(c['harness'], 'claude-code')
        self.assertTrue(gated)
        self.assertEqual(len({c['cell_id'] for c in cells}), len(cells))

if __name__ == '__main__':
    unittest.main()
