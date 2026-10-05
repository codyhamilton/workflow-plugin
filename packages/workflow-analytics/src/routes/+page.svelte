<script lang="ts">
	import { page } from '$app/state';
	import { apiGet } from '$lib/api';
	import { filterParams, parseFilter } from '$lib/filters';
	import { clearError, setError } from '$lib/state.svelte';
	import type { Summary } from '$lib/types';

	let summary = $state<Summary | null>(null);

	// Refetch whenever the page query changes; a stale response never overwrites a newer one.
	$effect(() => {
		const q = filterParams(parseFilter(page.url.searchParams));
		let live = true;
		apiGet<Summary>('analytics/summary', q).then(
			(s) => {
				if (!live) return;
				clearError();
				summary = s;
			},
			(e) => {
				if (!live) return;
				summary = null;
				setError(e);
			}
		);
		return () => (live = false);
	});

	// One tile per scalar; nested keys joined with "-" for the test id (summary-by_kind-brief).
	const tiles = $derived.by(() => {
		if (!summary) return [];
		const s = summary;
		const group = (title: string, field: string, o: Record<string, number>) => ({
			title,
			items: Object.entries(o).map(([k, v]) => ({ id: `${field}-${k}`, name: k, value: v }))
		});
		return [
			{
				title: 'Volume',
				items: [
					{ id: 'conversations', name: 'conversations', value: s.conversations },
					{ id: 'hook_events', name: 'hook events', value: s.hook_events },
					{ id: 'artifact_versions', name: 'artifact versions', value: s.artifact_versions },
					{ id: 'distinct_content', name: 'distinct content', value: s.distinct_content },
					{ id: 'commits', name: 'commits', value: s.commits }
				]
			},
			group('Artifacts by kind', 'by_kind', s.by_kind),
			group('Artifacts by source', 'by_source', s.by_source),
			group('Rejections', 'rejections', s.rejections),
			group('Screens', 'screens', s.screens)
		];
	});
</script>

<h1>Overview</h1>
{#if summary}
	<p class="window" data-testid="summary-window">
		<time>{summary.from}</time> to <time>{summary.to}</time>
	</p>
	{#each tiles as g (g.title)}
		<h2>{g.title}</h2>
		<div class="tiles">
			{#each g.items as t (t.id)}
				<div class="tile">
					<span class="n" data-testid="summary-{t.id}">{t.value}</span>
					<span class="name">{t.name}</span>
				</div>
			{/each}
		</div>
	{/each}
{/if}

<style>
	.tiles {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem;
	}
	.tile {
		min-width: 7rem;
		padding: 0.5rem 0.75rem;
		border: 1px solid #ddd;
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
		color: #555;
	}
	.window {
		color: #555;
	}
</style>
