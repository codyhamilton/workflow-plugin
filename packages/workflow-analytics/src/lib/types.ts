// Response shapes of the /v1 read routes (DESIGN.md "Analytics reads"; baselines from serve/reads.go).
import type { Kind } from './filters';

export interface Facets {
	repos: string[];
	harnesses: string[];
	kinds: Kind[];
	plans: string[];
	events: string[];
	models: string[];
	norm_events: string[];
	tools: { name: string; n: number }[];
	checks: { kind: Kind; name: string }[];
}

export interface Summary {
	from: string;
	to: string;
	conversations: number;
	hook_events: number;
	artifact_versions: number;
	distinct_content: number;
	by_kind: { design: number; brief: number; report: number; other: number };
	by_source: { worktree: number; commit: number };
	commits: number;
	rejections: { precheck: number; screen: number };
	screens: { pass: number; unscreened: number };
	model_calls: number;
	unpriced_calls: number;
	cost_usd: number;
	tokens_in: number;
	tokens_out: number;
	tokens_cache_read: number;
	tokens_cache_write: number;
	tokens_reasoning: number;
}

export type Metric = 'hook_events' | 'artifact_versions' | 'commits' | 'conversations' | 'rejections';

export interface Series {
	bucket: 'day' | 'week';
	series: { key: string; points: { t: string; n: number }[] }[];
}

export interface ScoreRow {
	name: string;
	n: number;
	min: number;
	p25: number;
	median: number;
	p75: number;
	max: number;
}
export interface Scores {
	kind: Kind;
	checks: ScoreRow[];
}

export interface Baselines {
	kind: Kind;
	checks: Record<string, { n: number; p25: number; median: number; p75: number }>;
}

export interface ScoreSeriesPoint {
	t: string;
	n: number;
	p25: number;
	median: number;
	p75: number;
}

export interface ScoreSeriesCheck {
	name: string;
	points: ScoreSeriesPoint[];
}

export interface ScoreSeries {
	kind: Kind;
	bucket: 'day' | 'week' | 'month';
	checks: ScoreSeriesCheck[];
}

export type Shape = 'complete' | 'unreported' | 'started';
export interface Executions {
	counts: Record<Shape, number>;
	rows: { repo_id: string; plan: string; conversation_id: string; brief_path: string; harness: string; shape: Shape; ts: string }[];
	next?: string;
	bucket?: 'day' | 'week' | 'month';
	series?: { key: Shape; points: { t: string; n: number }[] }[];
}

export interface Conversations {
	rows: {
		conversation_id: string;
		harness: string;
		repos: string[];
		first_ts: string;
		last_ts: string;
		hook_events: number;
		artifact_versions: number;
		commits: number;
		kinds: Kind[];
	}[];
	next?: string;
}

export interface Explore {
	rows: Record<string, string | number>[];
	truncated: boolean;
}

// Shapes added by the plan 12 read routes (/query, /schema, /conversation, /summary, /facets).
export interface QueryRow {
	t?: string;
	k: string[];
	v: number;
}

export interface QueryResponse {
	measure: string;
	bucket: string;
	dims: string[];
	rows: QueryRow[];
	ignored_filters?: string[];
	partial?: boolean;
	truncated?: boolean;
}

export interface Schema {
	measures: { name: string; unit: string; dims: string[] }[];
	buckets: string[];
}

export interface TimelineEvent {
	ts: string;
	type: string;
	norm_event: string;
	event: string;
	tool: string;
	model: string;
	path: string;
	kind: string;
	source: string;
	sha: string;
	tokens?: { in: number; out: number; cache_read: number; cache_write: number; reasoning: number };
	cost_usd?: number;
}

export interface Totals {
	model_calls: number;
	tokens_in: number;
	tokens_out: number;
	tokens_cache_read: number;
	tokens_cache_write: number;
	tokens_reasoning: number;
	cost_usd: number;
	unpriced_calls: number;
}

export interface ConversationDetail {
	conversation_id: string;
	harness: string;
	repos: string[];
	models: string[];
	first_ts: string;
	last_ts: string;
	totals: Totals;
	events: TimelineEvent[];
	truncated?: boolean;
}

export interface DistributionBin {
	lo: number;
	hi?: number;
	n: number;
}

export interface DistributionRow {
	k: string;
	n: number;
	unpriced: number;
	min: number;
	p25: number;
	median: number;
	p75: number;
	p95: number;
	max: number;
	bins: DistributionBin[];
}

export interface DistributionResponse {
	measure: string;
	grain: string;
	dim?: string;
	rows: DistributionRow[];
	truncated?: boolean;
	ignored_filters?: string[];
}
