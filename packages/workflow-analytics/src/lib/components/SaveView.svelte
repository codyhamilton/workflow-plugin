<script lang="ts">
	import { page } from '$app/state';
	import { store, type SavedView } from '$lib/views';

	// A reactive copy of the store, refreshed on every save/delete (and on a cross-tab storage event).
	let saved = $state<SavedView[]>(store.listViews());
	$effect(() => store.subscribe(() => (saved = store.listViews())));

	let name = $state('');
	let open = $state(false);
	let error = $state('');

	// The current page as a stored URL: pathname plus query, never the embed flag.
	const url = $derived.by(() => {
		const q = new URLSearchParams(page.url.searchParams);
		q.delete('embed');
		const qs = q.toString();
		return page.url.pathname + (qs ? `?${qs}` : '');
	});

	function save() {
		const trimmed = name.trim();
		if (!trimmed) return;
		try {
			store.saveView(trimmed, url);
			name = '';
			error = '';
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
	}
</script>

<div class="saveview">
	<input
		type="text"
		data-testid="saveview-name"
		placeholder="View name"
		bind:value={name}
		onkeydown={(e) => e.key === 'Enter' && save()}
	/>
	<button type="button" data-testid="saveview-save" onclick={save}>Save view</button>
	<button
		type="button"
		data-testid="saveview-menu-toggle"
		aria-expanded={open}
		onclick={() => (open = !open)}
	>
		Saved views
	</button>
	{#if open}
		<ul class="list">
			{#each saved as v (v.id)}
				<li>
					<a data-testid="saveview-item" href={v.url}>{v.name}</a>
					<button
						type="button"
						data-testid="saveview-delete"
						aria-label={`Delete ${v.name}`}
						onclick={() => store.deleteView(v.id)}
					>
						&times;
					</button>
				</li>
			{/each}
		</ul>
	{/if}
	{#if error}<p class="saveview-error" role="alert">{error}</p>{/if}
</div>

<style>
	.saveview {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		align-items: center;
		margin: 0.5rem 0;
	}
	.list {
		flex-basis: 100%;
		margin: 0;
		padding-left: 1rem;
	}
	.list li {
		display: flex;
		gap: 0.5rem;
		align-items: baseline;
	}
	.saveview-error {
		flex-basis: 100%;
		margin: 0;
		color: var(--muted);
		font-size: 0.85rem;
	}
</style>
