<script lang="ts">
	import { untrack } from 'svelte';
	import Heatmap from '$lib/charts/Heatmap.svelte';
	import Sparkline from '$lib/charts/Sparkline.svelte';
	import type { HeatCell, TimePoint } from '$lib/charts/options';
	import { pickBucket } from '$lib/buckets';
	import { costLabel } from '$lib/format';
	import { resolveWindow } from '$lib/params';
	import { getJSON, Superseded } from '$lib/query';
	import { clearError, setError } from '$lib/state.svelte';
	import type { QueryResponse, Summary } from '$lib/types';
	import { view } from '$lib/view.svelte';

	const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
	const HOURS = Array.from({ length: 24 }, (_, h) => String(h).padStart(2, '0'));

	// Tile id used in the spark testid, and the /query measure that feeds it.
	const SPARKS = [
		['conversations', 'conversations'],
		['hook_events', 'hook_events'],
		['artifact_versions', 'artifact_versions'],
		['distinct_content', 'distinct_content'],
		['commits', 'commits'],
		['model_calls', 'model_calls'],
		['tokens_in', 'tokens_in'],
		['cost_usd', 'cost_usd'],
		['unpriced_calls', 'unpriced_calls']
	] as const;

	let summary = $state<Summary | null>(null);
	let sparks = $state<Record<string, TimePoint[]>>({});
	let heat = $state<HeatCell[]>([]);

	$effect(() => {
		const state = view.state; // tracks the URL
		const needsFacets = Object.keys(state.exclude).length > 0;
		const ready = needsFacets ? view.facets !== null : true; // tracks facets only when needed
		if (!ready) return;

		let live = true;
		const fail = (e: unknown) => {
			if (!live || e instanceof Superseded) return;
			setError(e);
		};

		const rest = untrack(() => view.paramsFor('rest'));
		if (rest) {
			getJSON<Summary>('overview-summary', 'analytics/summary', rest).then((s) => {
				if (!live) return;
				clearError();
				summary = s;
			}, fail);
		}

		const win = resolveWindow(state, new Date(), view.tz, 'query');
		const bucket = win.all
			? 'month'
			: win.from && win.to
				? (pickBucket(win.from, win.to, view.tz, ['hour', 'day', 'week', 'month']) ?? 'day')
				: 'day';

		for (const [id, measure] of SPARKS) {
			const p = untrack(() => view.paramsFor('query', { measure, bucket }));
			if (!p) continue;
			getJSON<QueryResponse>(`overview-spark-${id}`, 'analytics/query', p).then((r) => {
				if (!live) return;
				clearError();
				sparks = {
					...sparks,
					[id]: r.rows.filter((x) => x.t).map((x) => ({ t: x.t as string, v: x.v }))
				};
			}, fail);
		}

		const hp = untrack(() =>
			view.paramsFor('query', { measure: 'hook_events', dim: ['weekday', 'hour_of_day'], bucket: 'none' })
		);
		if (hp) {
			getJSON<QueryResponse>('overview-heatmap', 'analytics/query', hp).then((r) => {
				if (!live) return;
				clearError();
				heat = r.rows.map((x) => ({ x: Number(x.k[1]), y: Number(x.k[0]), v: x.v }));
			}, fail);
		}

		return () => {
			live = false;
		};
	});
</script>

<h1>Overview</h1>
{#if summary}
	<section class="tiles" data-testid="overview-summary">
		<div class="tile">
			<span class="n" data-testid="summary-conversations">{summary.conversations}</span>
			<span class="name">conversations</span>
			<Sparkline testid="overview-spark-conversations" points={sparks.conversations ?? []} />
		</div>
		<div class="tile">
			<span class="n" data-testid="summary-hook_events">{summary.hook_events}</span>
			<span class="name">hook events</span>
			<Sparkline testid="overview-spark-hook_events" points={sparks.hook_events ?? []} />
		</div>
		<div class="tile">
			<span class="n" data-testid="summary-artifact_versions">{summary.artifact_versions}</span>
			<span class="name">artifact versions</span>
			<Sparkline testid="overview-spark-artifact_versions" points={sparks.artifact_versions ?? []} />
		</div>
		<div class="tile">
			<span class="n" data-testid="summary-distinct_content">{summary.distinct_content}</span>
			<span class="name">distinct content</span>
			<Sparkline testid="overview-spark-distinct_content" points={sparks.distinct_content ?? []} />
		</div>
		<div class="tile">
			<span class="n" data-testid="summary-commits">{summary.commits}</span>
			<span class="name">commits</span>
			<Sparkline testid="overview-spark-commits" points={sparks.commits ?? []} />
		</div>
		<div class="tile">
			<span class="n" data-testid="summary-model_calls">{summary.model_calls}</span>
			<span class="name">model calls</span>
			<Sparkline testid="overview-spark-model_calls" points={sparks.model_calls ?? []} />
		</div>
		<div class="tile">
			<span class="n" data-testid="summary-tokens">{summary.tokens_in + summary.tokens_out}</span>
			<span class="name">tokens</span>
			<span class="sub">cache read <span data-testid="summary-tokens_cache_read">{summary.tokens_cache_read}</span></span>
			<Sparkline testid="overview-spark-tokens_in" points={sparks.tokens_in ?? []} />
		</div>
		<div class="tile">
			<span class="n" data-testid="summary-cost_usd"
				>{costLabel({ cost: summary.cost_usd, unpriced: summary.unpriced_calls, calls: summary.model_calls })}</span
			>
			<span class="name">cost</span>
			<Sparkline testid="overview-spark-cost_usd" points={sparks.cost_usd ?? []} />
		</div>
		<div class="tile">
			<span class="n" data-testid="summary-unpriced_calls">{summary.unpriced_calls}</span>
			<span class="name">unpriced calls</span>
			<Sparkline testid="overview-spark-unpriced_calls" points={sparks.unpriced_calls ?? []} />
		</div>
	</section>
{/if}

<section class="heat">
	<h2>Activity by hour and weekday</h2>
	<Heatmap testid="overview-heatmap" cells={heat} xLabels={HOURS} yLabels={WEEKDAYS} />
</section>

<style>
	.tiles {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(9rem, 1fr));
		gap: 0.75rem;
	}
	.tile {
		min-width: 0;
		padding: 0.5rem 0.75rem;
		border: 1px solid #ddd;
		border-radius: 4px;
		display: flex;
		flex-direction: column;
		gap: 0.15rem;
	}
	.n {
		font-size: 1.6rem;
		font-variant-numeric: tabular-nums;
	}
	.name {
		font-size: 0.8rem;
		color: #555;
	}
	.sub {
		font-size: 0.75rem;
		color: #777;
	}
	.heat {
		margin-top: 1.5rem;
	}
</style>
