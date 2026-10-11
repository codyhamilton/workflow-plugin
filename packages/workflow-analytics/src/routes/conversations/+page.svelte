<script lang="ts">
	import { page } from '$app/state';
	import Pager from '$lib/components/Pager.svelte';
	import VirtualRows from '$lib/components/VirtualRows.svelte';
	import { getJSON, Superseded } from '$lib/query';
	import { view } from '$lib/view.svelte';
	import type { Conversations } from '$lib/types';

	const ROW_HEIGHT = 36;

	let rows = $state<Conversations['rows']>([]);
	let next = $state<string | undefined>(undefined);
	let loaded = $state(false);

	const limit = $derived(page.url.searchParams.get('limit'));
	const params = $derived(view.paramsFor('rest', limit ? { limit } : {}));

	$effect(() => {
		const p = params;
		if (!p) return;
		let live = true;
		rows = [];
		next = undefined;
		loaded = false;
		getJSON<Conversations>('conversations', 'analytics/conversations', p).then(
			(r) => {
				if (!live) return;
				loaded = true;
				rows = r.rows;
				next = r.next;
			},
			(e) => {
				if (!live || e instanceof Superseded) return;
			}
		);
		return () => (live = false);
	});

	const list = (a: string[]) => a.join(', ');
</script>

<h1>Conversations</h1>
{#if loaded}
	<div class="head">
		<span>conversation</span><span>harness</span><span>repos</span><span>first</span><span>last</span>
		<span>hook events</span><span>artifact versions</span><span>commits</span><span>kinds</span>
	</div>
	<VirtualRows {rows} rowHeight={ROW_HEIGHT}>
		{#snippet children(r)}
			<div class="row" data-testid="conv-row" style="height:{ROW_HEIGHT}px">
				<a
					class="cell"
					data-testid="conv-{r.conversation_id}-conversation_id"
					href="/conversation?id={r.conversation_id}">{r.conversation_id}</a
				>
				<button
					type="button"
					class="cell link"
					data-testid="conv-{r.conversation_id}-harness"
					onclick={(e) => view.drill('harness', r.harness, e)}>{r.harness}</button
				>
				<span class="cell" data-testid="conv-{r.conversation_id}-repos">
					{#each r.repos as repo, i}<button
							type="button"
							class="link"
							onclick={(e) => view.drill('repo_id', repo, e)}>{repo}</button>{#if i < r.repos.length - 1}, {/if}{/each}
				</span>
				<time class="cell">{r.first_ts}</time>
				<time class="cell">{r.last_ts}</time>
				<span class="cell num" data-testid="conv-{r.conversation_id}-hook_events">{r.hook_events}</span>
				<span class="cell num" data-testid="conv-{r.conversation_id}-artifact_versions">{r.artifact_versions}</span>
				<span class="cell num" data-testid="conv-{r.conversation_id}-commits">{r.commits}</span>
				<span class="cell">{list(r.kinds)}</span>
			</div>
		{/snippet}
	</VirtualRows>
	<Pager
		path="analytics/conversations"
		params={params ?? new URLSearchParams()}
		{next}
		onpage={(more, n) => {
			rows = [...rows, ...more];
			next = n;
		}}
	/>
{/if}

<style>
	.head,
	.row {
		display: grid;
		grid-template-columns: 1.4fr 0.8fr 0.8fr 1.2fr 1.2fr 0.8fr 0.9fr 0.6fr 1fr;
		align-items: center;
		gap: 0.5rem;
		padding: 0 0.75rem;
		border-bottom: 1px solid #eee;
		box-sizing: border-box;
	}
	.head {
		font-weight: 600;
	}
	.cell {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.num {
		text-align: right;
		font-variant-numeric: tabular-nums;
	}
	.link {
		background: none;
		border: 0;
		padding: 0;
		color: inherit;
		font: inherit;
		cursor: pointer;
		text-align: left;
	}
</style>
