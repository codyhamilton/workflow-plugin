<script lang="ts">
	import { page } from '$app/state';
	import { untrack } from 'svelte';
	import { bucketStarts, instantKey } from '$lib/charts/score-series';
	import SankeyChart from '$lib/charts/SankeyChart.svelte';
	import type { SankeyLink, SankeyNode } from '$lib/charts/sankey';
	import TimeChart from '$lib/charts/TimeChart.svelte';
	import type { TimeSeries } from '$lib/charts/options';
	import Pager from '$lib/components/Pager.svelte';
	import { bucketCount, pickBucket, type Bucket } from '$lib/buckets';
	import { label } from '$lib/format';
	import { resolveWindow } from '$lib/params';
	import { getJSON } from '$lib/query';
	import { clearError, setError } from '$lib/state.svelte';
	import type { Executions, Shape } from '$lib/types';
	import { view } from '$lib/view.svelte';

	const SHAPES: Shape[] = ['complete', 'unreported', 'started'];
	const ORDER: Bucket[] = ['day', 'week', 'month'];
	const CAP = 400;

	const NODES: SankeyNode[] = [
		{ name: 'design', label: 'design' },
		{ name: 'brief', label: 'brief' },
		{ name: 'commit', label: 'commit' },
		{ name: 'report', label: 'report' },
		{ name: 'nocommit', label: 'no commit' },
		{ name: 'noreport', label: 'no report' }
	];
	interface LinkDef {
		source: string;
		target: string;
		label: string;
		shapes: Shape[];
		value: (c: Executions['counts']) => number;
	}
	const LINKS: LinkDef[] = [
		{ source: 'design', target: 'brief', label: 'design → brief', shapes: [], value: (c) => c.complete + c.unreported + c.started },
		{ source: 'brief', target: 'commit', label: 'brief → commit', shapes: ['complete', 'unreported'], value: (c) => c.complete + c.unreported },
		{ source: 'brief', target: 'nocommit', label: 'brief → no commit', shapes: ['started'], value: (c) => c.started },
		{ source: 'commit', target: 'report', label: 'commit → report', shapes: ['complete'], value: (c) => c.complete },
		{ source: 'commit', target: 'noreport', label: 'commit → no report', shapes: ['unreported'], value: (c) => c.unreported }
	];

	let counts = $state<Executions['counts'] | null>(null);
	let rows = $state<Executions['rows']>([]);
	let next = $state<string | undefined>(undefined);
	let execSeries = $state<Executions['series']>(undefined);
	let respBucket = $state<Executions['bucket']>(undefined);

	const selected = $derived((page.url.searchParams.get('shape') ?? '').split(',').filter(Boolean) as Shape[]);
	const empty = $derived(counts !== null && counts.complete + counts.unreported + counts.started === 0);
	const linkData = $derived.by((): SankeyLink[] => {
		const c = counts;
		return c ? LINKS.map((l) => ({ source: l.source, target: l.target, value: l.value(c) })) : [];
	});

	const window = $derived.by(() => {
		const w = resolveWindow(view.state, new Date(), view.tz, 'rest');
		return w.from && w.to ? { from: w.from, to: w.to } : null;
	});

	const offered = $derived.by(() =>
		window ? ORDER.filter((b) => bucketCount(b, window.from, window.to, view.tz) <= CAP) : ORDER
	);

	const bucket = $derived.by(() => {
		if (!window) return 'day' as Bucket;
		const want = page.url.searchParams.get('bucket') as Bucket | null;
		if (want && offered.includes(want)) return want;
		return pickBucket(window.from, window.to, view.tz, ORDER) ?? offered[0] ?? 'month';
	});

	const chartSeries = $derived.by((): TimeSeries[] => {
		if (!execSeries?.length || !window) return [];
		const b = (respBucket ?? bucket) as Bucket;
		const starts = bucketStarts(view.tz, b, window.from, window.to);
		return execSeries.map((s) => {
			const byT = new Map(s.points.map((p) => [p.t, p.n]));
			const byStart = new Map<number, number>();
			for (const p of s.points) {
				const e = Date.parse(p.t);
				if (!Number.isNaN(e)) byStart.set(e, p.n);
			}
			return {
				name: s.key,
				points: starts.map((e) => {
					const t = instantKey(view.tz, new Date(e));
					const v = byStart.get(e) ?? byT.get(t) ?? 0;
					return { t, v };
				})
			};
		});
	});

	function sameSet(a: readonly string[], b: readonly string[]) {
		return a.length === b.length && a.every((x) => b.includes(x));
	}
	function applyShapes(shapes: Shape[]) {
		if (shapes.length === 0 || sameSet(selected, shapes)) view.setParam('shape', null);
		else view.setParam('shape', shapes.join(','));
	}
	function onLinkClick(l: SankeyLink) {
		const def = LINKS.find((d) => d.source === l.source && d.target === l.target);
		if (def) applyShapes(def.shapes);
	}
	function setBucket(v: string) {
		view.setParam('bucket', v);
	}

	const params = $derived.by(() => {
		const limit = page.url.searchParams.get('limit');
		const extra: Record<string, string | string[]> = { bucket };
		if (selected.length) extra.shape = [...selected];
		if (limit) extra.limit = limit;
		return view.paramsFor('rest', extra);
	});

	const queryKey = $derived(params ? params.toString() : null);

	$effect(() => {
		const key = queryKey;
		if (!key) return;
		const q = untrack(() => params);
		if (!q) return;
		let live = true;
		rows = [];
		next = undefined;
		execSeries = undefined;
		respBucket = undefined;
		getJSON<Executions>('executions', 'analytics/executions', q).then(
			(r) => {
				if (!live) return;
				clearError();
				counts = r.counts;
				rows = r.rows;
				next = r.next;
				execSeries = r.series;
				respBucket = r.bucket;
			},
			(e) => {
				if (!live) return;
				counts = null;
				execSeries = undefined;
				respBucket = undefined;
				setError(e);
			}
		);
		return () => (live = false);
	});
</script>

<h1>Executions</h1>
{#if counts && params}
	<div class="tiles">
		{#each SHAPES as s (s)}
			<div class="tile">
				<span class="n" data-testid="exec-count-{s}">{counts[s]}</span>
				<span class="name">{s}</span>
			</div>
		{/each}
	</div>
	<div class="controls">
		<label>bucket
			<select data-testid="exec-bucket" value={bucket} onchange={(e) => setBucket(e.currentTarget.value)}>
				{#each offered as b (b)}<option value={b}>{b}</option>{/each}
			</select>
		</label>
	</div>
	{#if chartSeries.length}
		<TimeChart
			testid="exec-shape-series"
			series={chartSeries}
			bucket={(respBucket ?? bucket) as 'day' | 'week' | 'month'}
			stacked={true}
			area={true}
			onbrush={({ from, to }) => view.setWindow(from, to)}
		/>
	{/if}
	{#if empty}
		<p data-testid="exec-empty">No executions in this window</p>
	{:else}
		<SankeyChart testid="exec-sankey" nodes={NODES} links={linkData} onlink={onLinkClick} />
		<div class="links">
			{#each LINKS as l (l.source + '-' + l.target)}
				<button
					type="button"
					data-testid={`exec-link-${l.source}-${l.target}`}
					aria-pressed={l.shapes.length > 0 && sameSet(selected, l.shapes)}
					onclick={() => applyShapes(l.shapes)}
				>{l.label}</button>
			{/each}
		</div>
	{/if}
	<table>
		<thead>
			<tr><th>repo</th><th>plan</th><th>conversation</th><th>brief</th><th>harness</th><th>shape</th><th>ts</th></tr>
		</thead>
		<tbody>
			{#each rows as r, i (i)}
				<tr data-testid="exec-row">
					<td>
						<button
							type="button"
							data-testid="exec-repo"
							onclick={(ev) => view.drill('repo_id', r.repo_id, { shift: ev.shiftKey })}
						>
							{label(r.repo_id)}
						</button>
					</td>
					<td>
						<button
							type="button"
							data-testid="exec-plan"
							onclick={(ev) => view.drill('plan', r.plan, { shift: ev.shiftKey })}
						>
							{label(r.plan)}
						</button>
					</td>
					<td>
						<a data-testid="exec-conversation" href={`/conversation?id=${encodeURIComponent(r.conversation_id)}`}>
							{label(r.conversation_id)}
						</a>
					</td>
					<td>{label(r.brief_path)}</td>
					<td>
						<button
							type="button"
							data-testid="exec-harness"
							onclick={(ev) => view.drill('harness', r.harness, { shift: ev.shiftKey })}
						>
							{label(r.harness)}
						</button>
					</td>
					<td>{r.shape}</td>
					<td><time>{r.ts}</time></td>
				</tr>
			{/each}
		</tbody>
	</table>
	<Pager
		path="analytics/executions"
		{params}
		{next}
		onpage={(more, n) => {
			rows = [...rows, ...more];
			next = n;
		}}
	/>
{/if}

<style>
	.tiles {
		display: flex;
		gap: 0.75rem;
	}
	.tile {
		min-width: 7rem;
		padding: 0.5rem 0.75rem;
		border: 1px solid var(--border);
		border-radius: 4px;
		display: flex;
		flex-direction: column;
	}
	.n {
		font-size: 1.6rem;
		font-variant-numeric: tabular-nums;
	}
	.name {
		font-size: 0.8rem;
		color: var(--muted);
	}
	.controls {
		display: flex;
		gap: 1rem;
		margin: 0.75rem 0;
	}
	.links {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		margin-top: 0.5rem;
	}
	table {
		margin-top: 1rem;
		border-collapse: collapse;
	}
	th,
	td {
		padding: 0.2rem 0.75rem;
		text-align: left;
		border-bottom: 1px solid var(--border);
	}
	td button {
		border: none;
		background: none;
		padding: 0;
		font: inherit;
		color: var(--accent);
		cursor: pointer;
		text-decoration: underline;
	}
</style>
