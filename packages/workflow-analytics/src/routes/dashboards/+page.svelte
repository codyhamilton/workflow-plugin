<script lang="ts">
	import { page } from '$app/state';
	import { view } from '$lib/view.svelte';
	import { ImportError, store, type Dashboard, type SavedView } from '$lib/views';

	// Each tile is a full page in an iframe, so past this the dashboard gets slow. The cap is a
	// page-level guard: the store happily holds more.
	const MAX_TILES = 12;

	let dashboards = $state<Dashboard[]>(store.listDashboards());
	let views = $state<SavedView[]>(store.listViews());
	let name = $state('');
	let addId = $state('');
	let importText = $state('');
	let importError = $state('');

	$effect(() =>
		store.subscribe(() => {
			dashboards = store.listDashboards();
			views = store.listViews();
		})
	);

	const selectedId = $derived(page.url.searchParams.get('d'));
	const selected = $derived(dashboards.find((d) => d.id === selectedId) ?? null);
	const atCap = $derived(!!selected && selected.viewIds.length >= MAX_TILES);

	// One entry per tile, in dashboard order. `index` is the store's index for move/remove.
	const tiles = $derived(
		(selected?.viewIds ?? []).map((id, index) => {
			const v = views.find((x) => x.id === id);
			return { id, index, name: v?.name ?? '', src: v ? tileSrc(v) : '' };
		})
	);

	/** A saved view's url is site-relative (5-01); frame it with `embed=1` so the shell is hidden. */
	function tileSrc(v: SavedView): string {
		if (typeof location === 'undefined') return '';
		const url = new URL(v.url, location.origin);
		if (url.origin !== location.origin) return '';
		return `${v.url}${v.url.includes('?') ? '&' : '?'}embed=1`;
	}

	function select(id: string | null) {
		view.setParam('d', id);
	}

	function create(e: Event) {
		e.preventDefault();
		const trimmed = name.trim();
		if (!trimmed) return;
		const d = store.createDashboard(trimmed);
		name = '';
		select(d.id);
	}

	function remove() {
		if (!selected) return;
		store.deleteDashboard(selected.id);
		select(null);
	}

	function add() {
		if (!selected || !addId || atCap) return;
		store.addToDashboard(selected.id, addId);
	}

	function move(index: number, delta: number) {
		if (!selected) return;
		store.moveInDashboard(selected.id, index, index + delta);
	}

	function drop(index: number) {
		if (!selected) return;
		store.removeFromDashboard(selected.id, index);
	}

	function exportJson() {
		if (!selected) return;
		const blob = new Blob([store.exportDashboard(selected.id)], { type: 'application/json' });
		const href = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = href;
		a.download = `${selected.name}.json`;
		document.body.append(a);
		a.click();
		a.remove();
		setTimeout(() => URL.revokeObjectURL(href), 0);
	}

	function importJson(text: string) {
		importError = '';
		try {
			const d = store.importDashboard(text);
			importText = '';
			select(d.id);
		} catch (e) {
			importError =
				e instanceof ImportError || e instanceof Error ? (e as Error).message : String(e);
		}
	}

	async function importFile(e: Event) {
		const input = e.currentTarget as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;
		try {
			importJson(await file.text());
		} finally {
			input.value = '';
		}
	}
</script>

<h1>Dashboards</h1>
<p>
	A dashboard is an ordered grid of saved views. Each tile frames the view's own url with
	<code>embed=1</code>, so it shows every kind of view without any per-view code.
</p>

<section class="dashboards">
	<h2>Your dashboards</h2>
	{#if dashboards.length === 0}
		<p class="muted">No dashboards yet.</p>
	{:else}
		<ul class="list">
			{#each dashboards as d (d.id)}
				<li>
					<button
						type="button"
						class="item"
						data-testid="dash-item"
						aria-pressed={d.id === selectedId}
						onclick={() => select(d.id)}
					>
						{d.name}
					</button>
				</li>
			{/each}
		</ul>
	{/if}
	<form class="create" onsubmit={create}>
		<label>
			New dashboard
			<input
				data-testid="dash-name"
				bind:value={name}
				placeholder="Dashboard name"
				autocomplete="off"
			/>
		</label>
		<button type="submit" data-testid="dash-create">Create</button>
	</form>
</section>

{#if selected}
	<section class="work">
		<div class="bar">
			<h2>{selected.name}</h2>
			<button type="button" data-testid="dash-delete" onclick={remove}>Delete</button>
			<button type="button" data-testid="dash-export" onclick={exportJson}>Export</button>
		</div>

		<div class="adders">
			<label>
				Add view
				<select data-testid="dash-add-select" bind:value={addId}>
					<option value="">Choose a saved view</option>
					{#each views as v (v.id)}
						<option value={v.id}>{v.name}</option>
					{/each}
				</select>
			</label>
			<button type="button" data-testid="dash-add" disabled={!addId || atCap} onclick={add}>
				Add
			</button>
		</div>

		{#if atCap}
			<p class="notice" role="status">Each tile is a full page; more than {MAX_TILES} is slow.</p>
		{/if}

		{#if tiles.length === 0}
			<p class="muted">No tiles yet. Save a view, then add it here.</p>
		{/if}
		<div class="grid">
			{#each tiles as t (`${t.id}-${t.index}`)}
				<div class="tile" data-testid="dash-tile">
					<div class="tile-bar">
						<span class="tile-name">{t.name || 'Saved view'}</span>
						<button
							type="button"
							data-testid="dash-tile-up"
							aria-label={`Move ${t.name} up`}
							disabled={t.index === 0}
							onclick={() => move(t.index, -1)}>↑</button
						>
						<button
							type="button"
							data-testid="dash-tile-down"
							aria-label={`Move ${t.name} down`}
							disabled={t.index === tiles.length - 1}
							onclick={() => move(t.index, 1)}>↓</button
						>
						<button
							type="button"
							data-testid="dash-tile-remove"
							aria-label={`Remove ${t.name}`}
							onclick={() => drop(t.index)}>×</button
						>
					</div>
					{#if t.src}
						<iframe class="frame" src={t.src} loading="lazy" title={t.name}></iframe>
					{:else}
						<p class="muted frame-empty">This view's url is missing or points off-site.</p>
					{/if}
				</div>
			{/each}
		</div>
	</section>
{/if}

<section class="import">
	<h2>Import a dashboard</h2>
	<label>
		Dashboard JSON file
		<input
			type="file"
			accept="application/json"
			data-testid="dash-import-file"
			onchange={importFile}
		/>
	</label>
	<label>
		Or paste dashboard JSON
		<textarea data-testid="dash-import-text" bind:value={importText} rows="4"></textarea>
	</label>
	<button type="button" data-testid="dash-import" onclick={() => importJson(importText)}>
		Import
	</button>
	{#if importError}
		<p class="error" role="alert" data-testid="dash-import-error">{importError}</p>
	{/if}
</section>

<style>
	h2 {
		font-size: 1.05rem;
		margin: 1rem 0 0.5rem;
	}
	.muted {
		color: var(--muted);
	}
	.dashboards .list {
		list-style: none;
		margin: 0 0 0.75rem;
		padding: 0;
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
	}
	.item {
		border: 1px solid var(--border);
		background: var(--surface);
		border-radius: 0.375rem;
		padding: 0.35rem 0.7rem;
		cursor: pointer;
	}
	.item[aria-pressed='true'] {
		border-color: var(--accent);
		color: var(--accent);
	}
	.create,
	.adders,
	.import {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem;
		align-items: flex-end;
	}
	.import {
		flex-direction: column;
		align-items: stretch;
		max-width: 32rem;
	}
	label {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}
	.bar {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}
	.bar h2 {
		margin: 0;
	}
	.notice {
		color: var(--muted);
		font-size: 0.85rem;
		margin: 0.5rem 0 0;
	}
	.grid {
		display: grid;
		grid-template-columns: 1fr;
		gap: 1rem;
		margin-top: 0.75rem;
	}
	@media (min-width: 1024px) {
		.grid {
			grid-template-columns: 1fr 1fr;
		}
	}
	.tile {
		display: flex;
		flex-direction: column;
		height: 360px;
		border: 1px solid var(--border);
		border-radius: 0.375rem;
		overflow: hidden;
		background: var(--surface);
	}
	.tile-bar {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		padding: 0.25rem 0.5rem;
		border-bottom: 1px solid var(--border);
	}
	.tile-name {
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		font-size: 0.9rem;
	}
	.tile-bar button {
		padding: 0.1rem 0.4rem;
	}
	.frame {
		flex: 1;
		width: 100%;
		border: 0;
	}
	.frame-empty {
		margin: 1rem;
	}
	.error {
		color: var(--danger);
		margin: 0;
	}
</style>
