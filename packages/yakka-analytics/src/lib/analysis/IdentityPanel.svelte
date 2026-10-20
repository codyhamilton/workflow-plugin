<script lang="ts">
	let { children } = $props();
</script>

<div class="identity-panel">
	{@render children()}
</div>

<style>
	.identity-panel {
		max-width: 40rem;
	}
	.identity-panel :global(h1) {
		margin: 0 0 var(--space-3);
		font-size: 1.5rem;
		font-weight: 700;
		color: var(--text);
	}
	.identity-panel :global(p) {
		margin: 0.75rem 0;
		color: var(--text);
	}
	.identity-panel :global(a) {
		color: var(--accent);
	}
</style>
