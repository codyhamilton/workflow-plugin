<script lang="ts">
	import { page } from '$app/state';
	import {
		store,
		type SavedView,
		reportFromPathname,
		chartParamsFromQuery,
		viewHref
	} from '$lib/views';

	// A reactive copy of the store, refreshed on every save/delete (and on a cross-tab storage event).
	let saved = $state<SavedView[]>(store.listViews());
	$effect(() => store.subscribe(() => (saved = store.listViews())));

	let name = $state('');
	let open = $state(false);
	let error = $state('');

	const report = $derived(reportFromPathname(page.url.pathname));

	function save() {
		const trimmed = name.trim();
		if (!trimmed || !report) return;
		try {
			const params = chartParamsFromQuery(report, page.url.searchParams);
			store.saveView(trimmed, report, params);
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
		disabled={!report}
		onkeydown={(e) => e.key === 'Enter' && save()}
	/>
	<button type="button" data-testid="saveview-save" disabled={!report} onclick={save}>Save view</button>
	<button
		type="button"
		data-testid="saveview-menu-toggle"
		aria-expanded={open}
		onclick={() => (open = !open)}
	>
		Saved views
	</button>
	{#if !report}
		<p class="saveview-hint" data-testid="saveview-not-storable">Save is available on report pages only.</p>
	{/if}
	{#if open}
		<ul class="list">
			{#each saved as v (v.id)}
				<li>
					<a data-testid="saveview-item" href={viewHref(v)}>{v.name}</a>
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
	.saveview-hint,
	.saveview-error {
		flex-basis: 100%;
		margin: 0;
		color: var(--muted);
		font-size: 0.85rem;
	}
</style>
