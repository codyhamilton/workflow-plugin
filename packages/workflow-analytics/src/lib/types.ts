// Response shapes of the /v1 read routes (DESIGN.md "Analytics reads"; baselines from serve/reads.go).
import type { Kind } from './filters';

export interface Facets {
	repos: string[];
	harnesses: string[];
	kinds: Kind[];
	plans: string[];
	events: string[];
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

export type Shape = 'complete' | 'unreported' | 'started';
export interface Executions {
	counts: Record<Shape, number>;
	rows: { repo_id: string; plan: string; conversation_id: string; brief_path: string; harness: string; shape: Shape; ts: string }[];
	next?: string;
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
