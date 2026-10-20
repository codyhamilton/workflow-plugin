import type { DistributionBin } from '$lib/types';

/** Pointer modifiers surfaced for phase-5 exclude (shift-click) wiring. */
export interface ChartPointerModifiers {
	shiftKey: boolean;
	altKey: boolean;
	metaKey: boolean;
	ctrlKey: boolean;
}

export interface ChartHoverDetail {
	seriesName?: string;
	category?: string;
	value?: number | string | null;
	raw?: unknown;
}

export interface ChartBrushEndDetail {
	/** Selected time range from a time-axis brush, when present. */
	from?: string;
	to?: string;
	raw?: unknown;
}

/**
 * Drill intent from a clickable mark. Only emitted when the mark is drillable for `dim`
 * (`__other__`, empty key, `hour_of_day`, and `weekday` are never drill targets).
 */
export interface ChartDrillDetail {
	dim: string;
	value: string;
	modifiers: ChartPointerModifiers;
	raw?: unknown;
}

export type TrendBucket = 'hour' | 'day' | 'week' | 'month';

export interface TrendPoint {
	t: string;
	v: number;
}

export interface TrendSeries {
	name: string;
	points: TrendPoint[];
}

/** Frame-level trend input (boundary `ask: trend` slice stub). */
export interface TrendFrameData {
	measure: string;
	bucket: TrendBucket;
	series: TrendSeries[];
	/** When set, breakdown series keys are drillable on this filter dim. */
	breakdownDim?: string;
}

export interface BreakdownRow {
	key: string;
	label?: string;
	value: number;
}

/** Frame-level breakdown input (boundary `ask: breakdown` slice stub). */
export interface BreakdownFrameData {
	measure: string;
	dim: string;
	rows: BreakdownRow[];
}

export type DistributionMeasure =
	| 'cost_usd'
	| 'tokens_in'
	| 'tokens_out'
	| 'tokens_cache_read'
	| 'tokens_cache_write'
	| 'tokens_reasoning';

/** Frame-level distribution input (boundary `ask: distribution` slice stub). */
export interface DistributionFrameData {
	measure: DistributionMeasure;
	bins: DistributionBin[];
	/** Optional breakdown dim for drill on grouped distribution (e.g. `model`). */
	drillDim?: string;
}

export interface QualityScorePoint {
	t: string;
	n?: number;
	p25?: number;
	median?: number;
	p75?: number;
}

/** Frame-level quality input (boundary `ask: quality` slice stub). */
export interface QualityFrameData {
	kind: 'design' | 'brief' | 'report';
	bucket: 'day' | 'week' | 'month';
	points: QualityScorePoint[];
	baselineMedian?: number;
	from: Date;
	to: Date;
	tz: string;
}

export type ChartFrameKind = 'trend' | 'breakdown' | 'distribution' | 'quality';

export interface ChartFrameCallbacks {
	onhover?: (detail: ChartHoverDetail) => void;
	/** Time-axis brush end — window change intent for trend / quality series. */
	onbrushend?: (detail: ChartBrushEndDetail) => void;
	/** Drill on a filter dim value when the mark is drillable. */
	ondrill?: (detail: ChartDrillDetail) => void;
}

export interface ChartFrameCommonProps extends ChartFrameCallbacks {
	height?: number;
	testid?: string;
}
