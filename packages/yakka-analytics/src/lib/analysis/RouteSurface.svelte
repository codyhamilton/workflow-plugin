<script lang="ts">
	let { legacy = false, children } = $props();
</script>

<div class="route-surface" data-legacy-theme={legacy ? '' : undefined}>
	{@render children()}
</div>

<style>
	.route-surface {
		display: contents;
	}
	.route-surface[data-legacy-theme] {
		display: block;
		color: var(--text);
		background: var(--bg);
		margin: 0 calc(-1 * var(--space-4));
		padding: 0 var(--space-4) var(--space-5);
	}
</style>
