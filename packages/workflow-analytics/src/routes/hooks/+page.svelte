<script lang="ts">
	import BarChart from '$lib/charts/BarChart.svelte';
	import Treemap from '$lib/charts/Treemap.svelte';
	import type { BarRow, TreemapNode } from '$lib/charts/options';
	import { label } from '$lib/format';
	import { getJSON, Superseded } from '$lib/query';
	import { clearError, setError } from '$lib/state.svelte';
	import type { QueryResponse } from '$lib/types';
	import type { DimKey } from '$lib/urlstate';
	import { view } from '$lib/view.svelte';

	// Four bars, one per dimension. The 20-key cap folds the tail into `__other__`, which every
	// chart and the table mark inert.
	const BARS: { testid: string; dim: DimKey }[] = [
		{ testid: 'hooks-harness', dim: 'harness' },
		{ testid: 'hooks-repo_id', dim: 'repo_id' },
		{ testid: 'hooks-event', dim: 'event' },
		{ testid: 'hooks-tool', dim: 'tool' }
	];
	// `/query` takes at most two dims, so the design's harness → norm_event → tool tree is two
	// linked two-level treemaps: A is harness → norm_event, B is norm_event → tool.
	const TREEMAPS: { testid: string; dims: [DimKey, DimKey] }[] = [
		{ testid: 'hooks-treemap-a', dims: ['harness', 'norm_event'] },
		{ testid: 'hooks-treemap-b', dims: ['norm_event', 'tool'] }
	];

	let bars = $state<Record<string, BarRow[]>>({});
	let trees = $state<Record<string, TreemapNode[]>>({});
	let failure = $state<unknown>(null);
	// Charts mount only once every request for the current view has settled, so a chart never
	// reports ready while it is still empty (`expectSettled` would otherwise pass too early).
	let loaded = $state(false);

	function barRows(resp: QueryResponse): BarRow[] {
		return resp.rows.map((r) => ({ key: r.k[0] ?? '', label: label(r.k[0]), value: r.v }));
	}

	// Fold the two-key rows into parent → leaf nodes, keeping first-seen order.
	function treeNodes(resp: QueryResponse): TreemapNode[] {
		const nodes = new Map<string, TreemapNode>();
		const order: string[] = [];
		for (const r of resp.rows) {
			const a = r.k[0] ?? '';
			const b = r.k[1] ?? '';
			let node = nodes.get(a);
			if (!node) {
				node = { name: a, children: [] };
				nodes.set(a, node);
				order.push(a);
			}
			node.children!.push({ name: b, value: r.v });
		}
		return order.map((a) => nodes.get(a)!);
	}

	// Six `/query` calls on one view change. Facets gate the first wave so one load issues each
	// request once (the URL alone does not change under them).
	$effect(() => {
		if (!view.facets) return;
		const jobs: Promise<void>[] = [];
		for (const { testid, dim } of BARS) {
			const params = view.paramsFor('query', {
				measure: 'hook_events',
				dim,
				bucket: 'none',
				top: '20'
			});
			if (!params) continue;
			jobs.push(
				getJSON<QueryResponse>(testid, 'analytics/query', params).then(
					(resp) => {
						bars[testid] = barRows(resp);
					},
					(e) => {
						if (!(e instanceof Superseded)) failure = e;
					}
				)
			);
		}
		for (const { testid, dims } of TREEMAPS) {
			const params = view.paramsFor('query', { measure: 'hook_events', dim: dims, bucket: 'none' });
			if (!params) continue;
			jobs.push(
				getJSON<QueryResponse>(testid, 'analytics/query', params).then(
					(resp) => {
						trees[testid] = treeNodes(resp);
					},
					(e) => {
						if (!(e instanceof Superseded)) failure = e;
					}
				)
			);
		}
		let live = true;
		loaded = false;
		let remaining = jobs.length;
		if (remaining === 0) {
			loaded = true;
			return;
		}
		for (const job of jobs)
			job.finally(() => {
				if (live && --remaining === 0) loaded = true;
			});
		return () => {
			live = false;
		};
	});

	$effect(() => {
		if (failure) setError(failure);
		else clearError();
	});

	// A bar click drills one dimension. A treemap path drills every level; `/query` allows two dims
	// but `view.drill` navigates once per call, so the tail waits for the first navigation to land.
	type Step = { dim: DimKey; value: string; shift: boolean };
	let pending: Step[] = [];

	function drillPath(dims: DimKey[], path: string[], shift: boolean) {
		if (path.length === 0 || path.some((v) => v === '__other__')) return;
		view.drill(dims[0], path[0], { shift });
		pending = path.slice(1).map((value, i) => ({ dim: dims[i + 1], value, shift }));
	}

	$effect(() => {
		void view.state;
		if (pending.length > 0) {
			const [next, ...rest] = pending;
			pending = rest;
			view.drill(next.dim, next.value, { shift: next.shift });
		}
	});
</script>

<h1>Hooks</h1>
{#if loaded}
	{#each BARS as b (b.testid)}
		<h2>{b.dim}</h2>
		<BarChart
			testid={b.testid}
			rows={bars[b.testid] ?? []}
			onselect={(d) => view.drill(b.dim, d.key, { shift: d.shift })}
		/>
	{/each}
	{#each TREEMAPS as t (t.testid)}
		<h2>{t.dims[0]} → {t.dims[1]}</h2>
		<Treemap
			testid={t.testid}
			root={trees[t.testid] ?? []}
			onselect={(d) => drillPath(t.dims, d.path, d.shift)}
		/>
	{/each}
{/if}
