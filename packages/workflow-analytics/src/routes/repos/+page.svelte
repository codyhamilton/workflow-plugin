<script lang="ts">
	import { page } from '$app/state';
	import { apiGet } from '$lib/api';
	import Bars from '$lib/charts/Bars.svelte';
	import { filterParams, parseFilter } from '$lib/filters';
	import { clearError, setError } from '$lib/state.svelte';
	import type { Facets, Summary } from '$lib/types';

	const FIELDS = ['conversations', 'hook_events', 'artifact_versions', 'commits'] as const;
	const KINDS = ['design', 'brief', 'report'] as const;

	let rows = $state<{ repo: string; s: Summary }[] | null>(null);

	$effect(() => {
		const f = parseFilter(page.url.searchParams);
		const q = filterParams(f);
		let live = true;
		(async () => {
			// /facets ignores repo_id, so the URL's repo_id values only narrow its list.
			const facets = await apiGet<Facets>('analytics/facets', q);
			const repos = facets.repos.filter((r) => r !== '' && (f.repo_id.length === 0 || f.repo_id.includes(r)));
			return Promise.all(
				repos.map(async (repo) => {
					const p = filterParams({ ...f, repo_id: [repo] });
					return { repo, s: await apiGet<Summary>('analytics/summary', p) };
				})
			);
		})().then(
			(r) => {
				if (!live) return;
				clearError();
				rows = r;
			},
			(e) => {
				if (!live) return;
				rows = null;
				setError(e);
			}
		);
		return () => (live = false);
	});

	const chartRows = $derived(
		(rows ?? []).map((r) => ({ name: r.repo, ...Object.fromEntries(FIELDS.map((k) => [k, r.s[k]])) }))
	);
</script>

<h1>Repos</h1>
{#if rows}
	<Bars rows={chartRows} keys={[...FIELDS]} />
	<table>
		<thead>
			<tr>
				<th>repo</th>
				{#each FIELDS as f (f)}<th>{f}</th>{/each}
				{#each KINDS as k (k)}<th>{k}</th>{/each}
			</tr>
		</thead>
		<tbody>
			{#each rows as r (r.repo)}
				<tr>
					<th>{r.repo}</th>
					{#each FIELDS as f (f)}<td data-testid="repo-{r.repo}-{f}">{r.s[f]}</td>{/each}
					{#each KINDS as k (k)}<td data-testid="repo-{r.repo}-by_kind-{k}">{r.s.by_kind[k]}</td>{/each}
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
		border-bottom: 1px solid #eee;
		font-variant-numeric: tabular-nums;
	}
	th:first-child {
		text-align: left;
	}
</style>
