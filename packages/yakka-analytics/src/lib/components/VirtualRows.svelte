<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		rows,
		rowHeight,
		children
	}: {
		rows: any[];
		rowHeight: number;
		children: Snippet<[any]>;
	} = $props();

	const height = 600;
	let scrollTop = $state(0);

	const start = $derived(Math.max(0, Math.floor(scrollTop / rowHeight) - 10));
	const end = $derived(Math.min(rows.length, Math.ceil((scrollTop + height) / rowHeight) + 10));
	const visible = $derived(rows.slice(start, end));

	function onscroll(e: Event) {
		scrollTop = (e.currentTarget as HTMLElement).scrollTop;
	}
</script>

<div class="virtual-scroll" data-testid="virtual-scroll" style="height:{height}px" {onscroll}>
	<div class="virtual-total" style="height:{rows.length * rowHeight}px">
		<div class="virtual-window" style="transform: translateY({start * rowHeight}px)">
			{#each visible as row, i (start + i)}
				{@render children(row)}
			{/each}
		</div>
	</div>
</div>

<style>
	.virtual-scroll {
		overflow-y: auto;
		position: relative;
	}
	.virtual-total {
		position: relative;
	}
	.virtual-window {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
	}
</style>
