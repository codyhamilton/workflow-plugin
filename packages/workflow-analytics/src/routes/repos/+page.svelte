<script lang="ts">
	import BarChart from '$lib/charts/BarChart.svelte';
	import { getJSON, Superseded } from '$lib/query';
	import { clearError, setError } from '$lib/state.svelte';
	import type { QueryResponse } from '$lib/types';
	import { view } from '$lib/view.svelte';

	// One request per column measure. The repo count never changes this number.
	const MEASURES = ['hook_events', 'conversations', 'artifact_versions', 'commits'] as const;
	type Measure = (typeof MEASURES)[number];

	let tables = $state<Record<Measure, QueryResponse> | null>(null);

	$effect(() => {
		// Wait for the facets: issuing before they load makes this effect run twice (once when
		// `facets` flips from null), and superseding an in-flight request re-sends it.
		if (view.facets === null) return;
		const queries = MEASURES.map((m) =>
			view.paramsFor('query', { measure: m, dim: 'repo_id', top: '100', bucket: 'none' })
		);
		if (queries.some((q) => q === null)) return;
		let live = true;
		Promise.all(
			MEASURES.map((m, i) => getJSON<QueryResponse>(`repos-${m}`, 'analytics/query', queries[i]!))
		).then(
			(responses) => {
				if (!live) return;
				clearError();
				tables = Object.fromEntries(MEASURES.map((m, i) => [m, responses[i]])) as Record<
					Measure,
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

	// Join the four measures by repo id; a repo absent from a measure counts 0 there.
	const rows = $derived.by(() => {
		if (!tables) return null;
		const byRepo = new Map<string, Record<Measure, number>>();
		for (const m of MEASURES)
			for (const row of tables[m].rows) {
				const repo = row.k[0] ?? '';
				const values =
					byRepo.get(repo) ??
					({ hook_events: 0, conversations: 0, artifact_versions: 0, commits: 0 } as Record<Measure, number>);
				values[m] = row.v;
				byRepo.set(repo, values);
			}
		return [...byRepo.entries()]
			.map(([repo, values]) => ({ repo, ...values }))
			.sort((a, b) => {
				if (a.repo === '__other__') return 1;
				if (b.repo === '__other__') return -1;
				return b.hook_events - a.hook_events || a.repo.localeCompare(b.repo);
			});
	});

	// `__other__` is the folded tail of the top-100 ranking; it is not a filter value.
	function pick(repo: string, shift: boolean) {
		if (repo === '__other__') return;
		view.drill('repo_id', repo, { shift });
	}
</script>

<h1>Repos</h1>
{#if rows}
	<BarChart
		testid="repos-chart"
		rows={rows.map((r) => ({ key: r.repo, label: r.repo, value: r.hook_events }))}
		onselect={(d) => pick(d.key, d.shift)}
	/>
	<table>
		<thead>
			<tr>
				<th>repo</th>
				{#each MEASURES as f (f)}<th>{f}</th>{/each}
			</tr>
		</thead>
		<tbody>
			{#each rows as r (r.repo)}
				<tr data-testid="repo-row-{r.repo}" onclick={(ev) => pick(r.repo, ev.shiftKey)}>
					<th>{r.repo}</th>
					{#each MEASURES as f (f)}<td data-testid="repo-{r.repo}-{f}">{r[f]}</td>{/each}
				</tr>
			{/each}
		</tbody>
	</table>
{/if}

<style>
	table {
		margin-top: 1rem;
		border-collapse: collapse;
	}
	th,
	td {
		padding: 0.2rem 0.75rem;
		text-align: right;
		border-bottom: 1px solid var(--border, #eee);
		font-variant-numeric: tabular-nums;
	}
	th:first-child {
		text-align: left;
	}
	tr {
		cursor: pointer;
	}
</style>
