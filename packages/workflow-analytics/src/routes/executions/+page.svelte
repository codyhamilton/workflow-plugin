<script lang="ts">
	import { page } from '$app/state';
	import { untrack } from 'svelte';
	import SankeyChart from '$lib/charts/SankeyChart.svelte';
	import type { SankeyLink, SankeyNode } from '$lib/charts/sankey';
	import Pager from '$lib/components/Pager.svelte';
	import { label } from '$lib/format';
	import { getJSON } from '$lib/query';
	import { clearError, setError } from '$lib/state.svelte';
	import type { Executions, Shape } from '$lib/types';
	import { view } from '$lib/view.svelte';

	const SHAPES: Shape[] = ['complete', 'unreported', 'started'];

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

	const selected = $derived((page.url.searchParams.get('shape') ?? '').split(',').filter(Boolean) as Shape[]);
	const empty = $derived(counts !== null && counts.complete + counts.unreported + counts.started === 0);
	const linkData = $derived.by((): SankeyLink[] => {
		const c = counts;
		return c ? LINKS.map((l) => ({ source: l.source, target: l.target, value: l.value(c) })) : [];
	});
	const filteredRows = $derived(selected.length > 0 ? rows.filter((r) => selected.includes(r.shape)) : rows);

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

	// First-page query: the shared view params plus an optional `limit` passed through to the API.
	// `paramsFor` returns null while facets are pending or when an exclude matches nothing.
	const params = $derived.by(() => {
		const limit = page.url.searchParams.get('limit');
		return view.paramsFor('rest', limit ? { limit } : undefined);
	});

	// The fetch is keyed on the API query string only: a `shape` selection (or a late facet response
	// that recomputes `params` to the same query) does not change the key, so the effect does not
	// re-run and its in-flight request is not cancelled. `params` is read untracked inside the effect.
	const queryKey = $derived(params ? params.toString() : null);

	$effect(() => {
		const key = queryKey;
		if (!key) return;
		const q = untrack(() => params);
		if (!q) return;
		let live = true;
		rows = [];
		next = undefined;
		getJSON<Executions>('executions', 'analytics/executions', q).then(
			(r) => {
				if (!live) return;
				clearError();
				counts = r.counts;
				rows = r.rows;
				next = r.next;
			},
			(e) => {
				if (!live) return;
				counts = null;
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
			{#each filteredRows as r, i (i)}
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
