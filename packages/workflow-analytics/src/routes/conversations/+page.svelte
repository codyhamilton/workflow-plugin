<script lang="ts">
	import { page } from '$app/state';
	import { apiGet } from '$lib/api';
	import Pager from '$lib/components/Pager.svelte';
	import { filterParams, parseFilter } from '$lib/filters';
	import { label } from '$lib/format';
	import { clearError, setError } from '$lib/state.svelte';
	import type { Conversations } from '$lib/types';

	let rows = $state<Conversations['rows']>([]);
	let next = $state<string | undefined>(undefined);
	let loaded = $state(false);

	// First-page query: the shared filter plus an optional `limit` passed through to the API.
	const params = $derived.by(() => {
		const q = filterParams(parseFilter(page.url.searchParams));
		const l = page.url.searchParams.get('limit');
		if (l) q.set('limit', l);
		return q;
	});

	$effect(() => {
		const q = params;
		let live = true;
		rows = [];
		next = undefined;
		apiGet<Conversations>('analytics/conversations', q).then(
			(r) => {
				if (!live) return;
				clearError();
				loaded = true;
				rows = r.rows;
				next = r.next;
			},
			(e) => {
				if (!live) return;
				loaded = false;
				setError(e);
			}
		);
		return () => (live = false);
	});

	const list = (a: string[]) => (a.length ? a.join(', ') : label(''));
</script>

<h1>Conversations</h1>
{#if loaded}
	<table>
		<thead>
			<tr>
				<th>conversation</th><th>harness</th><th>repos</th><th>first</th><th>last</th>
				<th>hook events</th><th>artifact versions</th><th>commits</th><th>kinds</th>
			</tr>
		</thead>
		<tbody>
			{#each rows as r, i (i)}
				<tr data-testid="conv-row">
					<td>{label(r.conversation_id)}</td>
					<td>{label(r.harness)}</td>
					<td>{list(r.repos)}</td>
					<td><time>{r.first_ts}</time></td>
					<td><time>{r.last_ts}</time></td>
					<td class="num" data-testid="conv-{r.conversation_id}-hook_events">{r.hook_events}</td>
					<td class="num" data-testid="conv-{r.conversation_id}-artifact_versions">{r.artifact_versions}</td>
					<td class="num" data-testid="conv-{r.conversation_id}-commits">{r.commits}</td>
					<td>{list(r.kinds)}</td>
				</tr>
			{/each}
		</tbody>
	</table>
	<Pager
		path="analytics/conversations"
		{params}
		{next}
		onpage={(more, n) => {
			rows = [...rows, ...more];
			next = n;
		}}
	/>
{/if}

<style>
	table {
		margin-top: 1rem;
		border-collapse: collapse;
	}
	th,
	td {
		padding: 0.2rem 0.75rem;
		text-align: left;
		border-bottom: 1px solid #eee;
	}
	.num {
		text-align: right;
		font-variant-numeric: tabular-nums;
	}
</style>
