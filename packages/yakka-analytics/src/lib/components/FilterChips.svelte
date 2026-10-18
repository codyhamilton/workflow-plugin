<script lang="ts">
	import { chips } from '$lib/urlstate';
	import { view } from '$lib/view.svelte';

	const active = $derived(chips(view.state));
</script>

{#if active.length > 0}
	<ul class="chips">
		{#each active as c (`${c.mode}-${c.key}-${c.value}`)}
			<li data-testid="chip-{c.key}-{c.value}" data-mode={c.mode}>
				<span class="label">
					{c.mode === 'exclude' ? 'not ' : ''}{c.key}: {c.value}{c.key === 'conversation_id' && c.mode === 'exclude'
						? ' (not applied)'
						: ''}
				</span>
				<button
					type="button"
					data-testid="chip-remove-{c.key}-{c.value}"
					aria-label="Remove filter {c.key} {c.value}"
					onclick={() => view.removeChip(c.key, c.value)}
				>
					×
				</button>
			</li>
		{/each}
	</ul>
{/if}

<style>
	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 0.25rem 0.5rem;
		list-style: none;
		margin: 0.5rem 0 0;
		padding: 0;
	}
	li {
		display: inline-flex;
		align-items: center;
		gap: 0.25rem;
		padding: 0.1rem 0.35rem;
		border: 1px solid var(--border);
		border-radius: 999px;
		background: var(--surface);
		font-size: 0.8rem;
	}
	li[data-mode='exclude'] .label {
		font-style: italic;
	}
	button {
		border: none;
		background: none;
		color: var(--muted);
		cursor: pointer;
		line-height: 1;
	}
</style>
