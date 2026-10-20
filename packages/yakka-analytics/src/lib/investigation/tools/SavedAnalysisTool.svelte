<script lang="ts">
	import type { AggregateRequest } from '$lib/aggregate';
	import { list, remove, save, type SavedAnalysis } from '$lib/saved-analysis';

	let {
		request,
		onOpen
	}: {
		request: AggregateRequest;
		onOpen: (spec: AggregateRequest) => void;
	} = $props();

	let name = $state('');
	let items = $state<SavedAnalysis[]>(list());

	function refresh() {
		items = list();
	}

	function doSave() {
		const trimmed = name.trim();
		if (!trimmed) return;
		save(trimmed, request);
		name = '';
		refresh();
	}

	function openItem(item: SavedAnalysis) {
		onOpen(item.spec);
	}

	function doRemove(id: string) {
		remove(id);
		refresh();
	}
</script>

<div class="saved-tool" data-testid="investigation-saved-tool">
	<label>
		Name
		<input data-testid="investigation-saved-name" bind:value={name} />
	</label>
	<button type="button" data-testid="investigation-saved-save" onclick={doSave}>Save current</button>

	<ul class="list">
		{#each items as item (item.id)}
			<li>
				<button type="button" data-testid="investigation-saved-open-{item.name}" onclick={() => openItem(item)}
					>{item.name}</button
				>
				<button type="button" class="remove" onclick={() => doRemove(item.id)}>Remove</button>
			</li>
		{/each}
	</ul>
</div>

<style>
	label {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		margin-bottom: 0.5rem;
	}
	.list {
		list-style: none;
		padding: 0;
		margin: 1rem 0 0;
	}
	li {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		margin-bottom: 0.35rem;
	}
	.remove {
		font-size: 0.85rem;
	}
</style>
