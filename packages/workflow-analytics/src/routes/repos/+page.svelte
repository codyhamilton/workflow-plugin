<script lang="ts">
	import BarChart from '$lib/charts/BarChart.svelte';
	import { getJSON, Superseded } from '$lib/query';
	import { clearError, setError } from '$lib/state.svelte';
	import type { QueryResponse } from '$lib/types';
	import { view } from '$lib/view.svelte';

	const TABLE_MEASURES = ['hook_events', 'conversations', 'artifact_versions', 'commits'] as const;
	type TableMeasure = (typeof TABLE_MEASURES)[number];
	const QUERY_MEASURES = [...TABLE_MEASURES, 'cost_usd'] as const;
	type QueryMeasure = (typeof QUERY_MEASURES)[number];
	type RankMeasure = QueryMeasure;

	let tables = $state<Record<QueryMeasure, QueryResponse> | null>(null);
	let rankBy = $state<RankMeasure>('hook_events');

	$effect(() => {
		// Wait for the facets: issuing before they load makes this effect run twice (once when
		// `facets` flips from null), and superseding an in-flight request re-sends it.
		if (view.facets === null) return;
		const queries = QUERY_MEASURES.map((m) =>
			view.paramsFor('query', { measure: m, dim: 'repo_id', top: '100', bucket: 'none' })
		);
		if (queries.some((q) => q === null)) return;
		let live = true;
		Promise.all(
			QUERY_MEASURES.map((m, i) => getJSON<QueryResponse>(`repos-${m}`, 'analytics/query', queries[i]!))
		).then(
			(responses) => {
				if (!live) return;
				clearError();
				tables = Object.fromEntries(QUERY_MEASURES.map((m, i) => [m, responses[i]])) as Record<
					QueryMeasure,
					QueryResponse
				>;
			},
			(e) => {
				// A superseded call is not an error; a real failure clears the table.
				if (!live || e instanceof Superseded) return;
				tables = null;
				setError(e);
			}
		);
		return () => {
			live = false;
		};
	});

	type RepoRow = { repo: string } & Record<TableMeasure, number> & { cost_usd: number };

	function zeroRow(): Record<TableMeasure, number> & { cost_usd: number } {
		return { hook_events: 0, conversations: 0, artifact_versions: 0, commits: 0, cost_usd: 0 };
	}

	// Join measures by repo id; a repo absent from a measure counts 0 there.
	const joined = $derived.by(() => {
		if (!tables) return null;
		const byRepo = new Map<string, Record<TableMeasure, number> & { cost_usd: number }>();
		for (const m of QUERY_MEASURES)
			for (const row of tables[m].rows) {
				const repo = row.k[0] ?? '';
				const values = byRepo.get(repo) ?? zeroRow();
				values[m] = row.v;
				byRepo.set(repo, values);
			}
		return [...byRepo.entries()].map(([repo, values]) => ({ repo, ...values }) as RepoRow);
	});

	function sortRows(rows: RepoRow[], measure: RankMeasure): RepoRow[] {
		return [...rows].sort((a, b) => {
			if (a.repo === '__other__') return 1;
			if (b.repo === '__other__') return -1;
			return b[measure] - a[measure] || a.repo.localeCompare(b.repo);
		});
	}

	// Table order stays on hook_events when the chart ranking measure changes.
	const rows = $derived.by(() => (joined ? sortRows(joined, 'hook_events') : null));
	const chartRows = $derived.by(() => (joined ? sortRows(joined, rankBy) : null));
	const chartUnit = $derived(rankBy === 'cost_usd' ? 'usd' : undefined);

	// `__other__` is the folded tail of the top-100 ranking; it is not a filter value.
	function pick(repo: string, shift: boolean) {
		if (repo === '__other__') return;
		view.drill('repo_id', repo, { shift });
	}
</script>

<h1>Repos</h1>
{#if rows && chartRows}
	<label>
		Rank by
		<select data-testid="repos-rank" bind:value={rankBy}>
			{#each QUERY_MEASURES as m (m)}<option value={m}>{m}</option>{/each}
		</select>
	</label>
	<BarChart
		testid="repos-chart"
		rows={chartRows.map((r) => ({ key: r.repo, label: r.repo, value: r[rankBy] }))}
		unit={chartUnit}
		onselect={(d) => pick(d.key, d.shift)}
	/>
	<table>
		<thead>
			<tr>
				<th>repo</th>
				{#each TABLE_MEASURES as f (f)}<th>{f}</th>{/each}
			</tr>
		</thead>
		<tbody>
			{#each rows as r (r.repo)}
				<tr data-testid="repo-row-{r.repo}" onclick={(ev) => pick(r.repo, ev.shiftKey)}>
					<th>{r.repo}</th>
					{#each TABLE_MEASURES as f (f)}<td data-testid="repo-{r.repo}-{f}">{r[f]}</td>{/each}
				</tr>
			{/each}
		</tbody>
	</table>
{/if}

<style>
	label {
		display: block;
		margin-bottom: 0.5rem;
		font-size: 0.9rem;
	}
	select {
		margin-left: 0.35rem;
	}
	table {
		margin-top: 1rem;
		border-collapse: collapse;
	}
	th,
	td {
		padding: 0.2rem 0.75rem;
		text-align: right;
		border-bottom: 1px solid var(--border);
		font-variant-numeric: tabular-nums;
	}
	th:first-child {
		text-align: left;
	}
	tr {
		cursor: pointer;
	}
</style>
