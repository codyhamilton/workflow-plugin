// The e2e fixture: facts posted to both e2e serves, and the hand-counted numbers every report spec
// asserts against. Specs for 2-02..2-04 read expectations from here; if a number is missing they
// compute it in their own spec from FACTS. Do not edit the counts to match a failing report: recount
// by hand from the facts below.
//
// Timestamps are whole hours on UTC days 1-5 days before "now", so the default 30-day window
// holds all of them. Day offsets are "days before today (UTC midnight)".
import { createHash } from 'node:crypto';

const DAY = 86400;
const today = Math.floor(Date.now() / 1000 / DAY) * DAY;
const at = (daysAgo: number, hour: number) => today - daysAgo * DAY + hour * 3600;
const dayStr = (daysAgo: number) => new Date(at(daysAgo, 0) * 1000).toISOString().slice(0, 10);

/** UTC day strings (YYYY-MM-DD) for the days the fixture uses, keyed by days-ago. */
export const DAYS = { d1: dayStr(1), d2: dayStr(2), d3: dayStr(3), d4: dayStr(4), d5: dayStr(5) };

export const REPOS = ['r1', 'r2'];
export const HARNESSES = ['claude', 'cursor', 'opencode'];
/** The one repo the filtered lens uses. */
export const FILTER_REPO = 'r1';

export const P_DESIGN1 = 'docs/plans/01-x/DESIGN.md';
export const P_BRIEF1 = 'docs/plans/01-x/briefs/1-01-a.md';
export const P_REPORT1 = 'docs/plans/01-x/reports/1-01-a.md';
export const P_BRIEF2 = 'docs/plans/02-y/briefs/2-01-b.md';
export const P_DESIGN2 = 'docs/plans/02-y/DESIGN.md';
export const P_BRIEF3 = 'docs/plans/01-x/briefs/1-02-c.md';
export const P_NESTED = 'docs/plans/01-x/briefs/sub/1-03-n.md'; // nested: no kind, counts as "other"

type Fact = Record<string, unknown>;
export const FACTS: Fact[] = [];
let n = 0;
function add(conv: string, harness: string, repo: string, type: string, event: string, ts: number, extra: Fact = {}) {
	n++;
	FACTS.push({ id: `f#${n}`, type, conversation_id: conv, harness, repo_id: repo, event, ts, ...extra });
}
function art(conv: string, harness: string, repo: string, event: string, ts: number, path: string, content: string, source: string) {
	const x: Fact = { path, content, content_hash: createHash('sha256').update(content).digest('hex'), source };
	if (source === 'commit') x.sha = 'abc1';
	add(conv, harness, repo, 'artifact_version', event, ts, x);
}
const tool = (name: string): Fact => ({ payload: { tool_name: name } });

// c1: claude, r1. Complete brief: commit and report.
add('c1', 'claude', 'r1', 'hook_event', 'PreToolUse', at(5, 10), tool('Bash'));
add('c1', 'claude', 'r1', 'hook_event', 'PreToolUse', at(5, 11), tool('Bash'));
add('c1', 'claude', 'r1', 'hook_event', 'Stop', at(4, 9));
art('c1', 'claude', 'r1', 'Write', at(5, 12), P_DESIGN1, '# d1\n', 'worktree');
art('c1', 'claude', 'r1', 'Write', at(4, 10), P_BRIEF1, '# b1\n', 'worktree');
add('c1', 'claude', 'r1', 'commit', 'commit', at(3, 12), { sha: 'abc1' });
art('c1', 'claude', 'r1', 'commit', at(3, 12), P_DESIGN1, '# d1\n', 'commit'); // same content as the worktree design
art('c1', 'claude', 'r1', 'Write', at(3, 13), P_REPORT1, '# rep1\n', 'worktree');
// c2: cursor, r2. Unreported brief: commit, no report.
add('c2', 'cursor', 'r2', 'hook_event', 'PostToolUse', at(2, 8), tool('Read'));
art('c2', 'cursor', 'r2', 'Write', at(2, 9), P_BRIEF2, '# b2\n', 'worktree');
art('c2', 'cursor', 'r2', 'Write', at(2, 10), P_DESIGN2, '# d2\n', 'worktree');
add('c2', 'cursor', 'r2', 'commit', 'commit', at(2, 12), { sha: 'def2' });
// c3: claude, r1. Started brief (no commit) and a nested brief path.
art('c3', 'claude', 'r1', 'Write', at(1, 9), P_BRIEF3, '# b3\n', 'worktree');
art('c3', 'claude', 'r1', 'Write', at(1, 10), P_NESTED, '# nest\n', 'worktree');
add('c3', 'claude', 'r1', 'hook_event', 'Stop', at(1, 9));
// c4: cursor, r1. One good hook event; one rejected by precheck for carrying a secret (not stored as a fact).
add('c4', 'cursor', 'r1', 'hook_event', 'PreToolUse', at(1, 8), tool('Bash'));
	add('c4', 'cursor', 'r1', 'hook_event', 'PreToolUse', at(1, 8), {
		payload: { tool_name: 'Bash', cmd: 'AKIA' + 'IOSFODNN7' + 'EXAMPLE' }
	});
// c5: opencode, r1. Three usage calls: two priced Sonnet calls on different days and one unpriced
// local call. The ingest normaliser stores the model as providerID/modelID.
add('c5', 'opencode', 'r1', 'hook_event', 'transcript.assistant_message', at(4, 7), {
	payload: {
		hook_event_name: 'transcript.assistant_message',
		message_id: 'msg_c5_1',
		modelID: 'claude-sonnet-5-5',
		providerID: 'anthropic',
		cost: 0.0123,
		tokens: { cache: { read: 3000, write: 400 }, input: 1000, output: 200, reasoning: 50 }
	}
});
add('c5', 'opencode', 'r1', 'hook_event', 'transcript.assistant_message', at(2, 7), {
	payload: {
		hook_event_name: 'transcript.assistant_message',
		message_id: 'msg_c5_2',
		modelID: 'qwen3-coder:30b-a3b-q4_K_M',
		providerID: 'ollama-maxctx',
		tokens: { cache: { read: 0, write: 0 }, input: 500, output: 100, reasoning: 0 }
	}
});
add('c5', 'opencode', 'r1', 'hook_event', 'transcript.assistant_message', at(1, 7), {
	payload: {
		hook_event_name: 'transcript.assistant_message',
		message_id: 'msg_c5_3',
		modelID: 'claude-sonnet-5-5',
		providerID: 'anthropic',
		cost: 0.01,
		tokens: { cache: { read: 100, write: 50 }, input: 2000, output: 300, reasoning: 10 }
	}
});
// c1: claude, r1. One assistant usage message with a distinct id (Opus priced from pricing_table.json).
add('c1', 'claude', 'r1', 'hook_event', 'transcript.assistant_message', at(5, 13), {
	payload: {
		hook_event_name: 'transcript.assistant_message',
		message_id: 'msg_c1_usage_1',
		model: 'claude-opus-5-5',
		usage: { input_tokens: 2, output_tokens: 5505, cache_read_input_tokens: 96297, cache_creation_input_tokens: 922 }
	}
});

/** Summary expectations, all hand-counted from the facts above. */
export const SUMMARY_ALL = {
	conversations: 5,
	hook_events: 10,
	artifact_versions: 8,
	distinct_content: 7, // d1 worktree and d1 commit share a hash
	commits: 2,
	'by_kind-design': 3,
	'by_kind-brief': 3,
	'by_kind-report': 1,
	'by_kind-other': 1,
	'by_source-worktree': 7,
	'by_source-commit': 1,
	'rejections-precheck': 1,
	'rejections-screen': 0,
	'screens-pass': 0, // no scorer in the e2e serves: every verdict is "unscreened"
	'screens-unscreened': 7
};
/** Summary with repo_id=r1 (c1, c3, c4). Rejections carry no repo_id, so they drop out of any repo filter. */
export const SUMMARY_R1 = {
	conversations: 4,
	hook_events: 9,
	artifact_versions: 6,
	distinct_content: 5,
	commits: 1,
	'by_kind-design': 2,
	'by_kind-brief': 2,
	'by_kind-report': 1,
	'by_kind-other': 1,
	'by_source-worktree': 5,
	'by_source-commit': 1,
	'rejections-precheck': 0,
	'rejections-screen': 0,
	'screens-pass': 0,
	'screens-unscreened': 5
};

/** Whole-window usage measures: 4 calls, 3 priced (2 Sonnet reported + 1 Opus table-priced), 1 unpriced. */
export const USAGE_ALL = {
	model_calls: 4,
	unpriced_calls: 1,
	tokens_in: 3502, // 1000 + 500 + 2000 + 2
	tokens_out: 6105, // 200 + 100 + 300 + 5505
	tokens_cache_read: 99397, // 3000 + 0 + 100 + 96297
	tokens_cache_write: 1372, // 400 + 0 + 50 + 922
	tokens_reasoning: 60, // 50 + 0 + 10 + 0
	cost_usd: 0.156277 // 0.0123 + 0.0100 Sonnet reported + 0.133977 Opus from table
};
/** Per-model usage, keyed by the derived model name the ingest normaliser stores. */
export const USAGE_BY_MODEL = {
	'anthropic/claude-sonnet-5-5': { calls: 2, unpriced: 0, cost_usd: 0.0223 },
	'ollama-maxctx/qwen3-coder:30b-a3b-q4_K_M': { calls: 1, unpriced: 1, cost_usd: 0 },
	'claude-opus-5-5': { calls: 1, unpriced: 0, cost_usd: 0.133977 }
};
/** The `/conversation?id=c5` totals: c5's three OpenCode calls. */
export const USAGE_C5 = {
	model_calls: 3,
	tokens_in: 3500, // 1000 + 500 + 2000
	tokens_out: 600, // 200 + 100 + 300
	tokens_cache_read: 3100, // 3000 + 0 + 100
	tokens_cache_write: 450, // 400 + 0 + 50
	tokens_reasoning: 60, // 50 + 0 + 10
	cost_usd: 0.0223, // 0.0123 + 0.0100
	unpriced_calls: 1
};

/** Hook events (whole window): 10 in total. The empty tool key is the Stop and usage events (no tool_name). */
export const HOOKS_BY_REPO = { r1: 9, r2: 1 };
export const HOOKS_BY_HARNESS = { claude: 5, cursor: 2, opencode: 3 };
export const HOOKS_BY_EVENT = { PreToolUse: 3, Stop: 2, PostToolUse: 1, 'transcript.assistant_message': 4 };
export const HOOKS_BY_TOOL = { Bash: 3, Read: 1, '': 6 };
/** series metric=hook_events bucket=day group=none: key "all". */
export const HOOK_EVENTS_BY_DAY: Record<string, number> = {
	[DAYS.d5]: 3,
	[DAYS.d4]: 2,
	[DAYS.d2]: 2,
	[DAYS.d1]: 3
};

/** /executions, ts descending. ts is the earliest in-window brief ts, as epoch seconds. */
export const EXECUTION_COUNTS = { complete: 1, unreported: 1, started: 1 };
export const EXECUTION_ROWS = [
	{ repo_id: 'r1', plan: '01-x', conversation_id: 'c3', brief_path: P_BRIEF3, harness: 'claude', shape: 'started', ts: at(1, 9) },
	{ repo_id: 'r2', plan: '02-y', conversation_id: 'c2', brief_path: P_BRIEF2, harness: 'cursor', shape: 'unreported', ts: at(2, 9) },
	{ repo_id: 'r1', plan: '01-x', conversation_id: 'c1', brief_path: P_BRIEF1, harness: 'claude', shape: 'complete', ts: at(4, 10) }
];

/** /conversations, last_ts descending. */
export const CONVERSATION_ROWS = [
	{ conversation_id: 'c3', harness: 'claude', repos: ['r1'], first_ts: at(1, 9), last_ts: at(1, 10), hook_events: 1, artifact_versions: 2, commits: 0, kinds: ['brief'] },
	{ conversation_id: 'c4', harness: 'cursor', repos: ['r1'], first_ts: at(1, 8), last_ts: at(1, 8), hook_events: 1, artifact_versions: 0, commits: 0, kinds: [] },
	{ conversation_id: 'c5', harness: 'opencode', repos: ['r1'], first_ts: at(4, 7), last_ts: at(1, 7), hook_events: 3, artifact_versions: 0, commits: 0, kinds: [] },
	{ conversation_id: 'c2', harness: 'cursor', repos: ['r2'], first_ts: at(2, 8), last_ts: at(2, 12), hook_events: 1, artifact_versions: 2, commits: 1, kinds: ['brief', 'design'] },
	{ conversation_id: 'c1', harness: 'claude', repos: ['r1'], first_ts: at(5, 10), last_ts: at(3, 13), hook_events: 4, artifact_versions: 4, commits: 1, kinds: ['brief', 'design', 'report'] }
];
