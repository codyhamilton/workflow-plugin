<script lang="ts">
	// One row per data row; a row whose `selectable` is false is drawn but inert
	// (the `__other__` bucket). A click fires the same select event as the chart mark.
	let {
		testid,
		columns,
		rows,
		onrow
	}: {
		testid: string;
		columns: string[];
		rows: { cells: (string | number)[]; selectable?: boolean }[];
		onrow?: (index: number, shift: boolean) => void;
	} = $props();
</script>

<table class="data-table" data-testid={testid}>
	<thead>
		<tr>
			{#each columns as c}<th>{c}</th>{/each}
		</tr>
	</thead>
	<tbody>
		{#each rows as row, i}
			<tr
				class:inert={row.selectable === false}
				style:cursor={row.selectable === false ? 'default' : 'pointer'}
				onclick={(e) => {
					if (row.selectable === false) return;
					onrow?.(i, e.shiftKey);
				}}
				onkeydown={(e) => {
					if (row.selectable === false) return;
					if (e.key === 'Enter' || e.key === ' ') {
						e.preventDefault();
						onrow?.(i, e.shiftKey);
					}
				}}
				tabindex={row.selectable === false ? -1 : 0}
			>
				{#each row.cells as cell}<td>{cell}</td>{/each}
			</tr>
		{/each}
	</tbody>
</table>

<style>
	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.85rem;
	}
	th,
	td {
		text-align: left;
		padding: 0.35rem 0.6rem;
		border-bottom: 1px solid var(--border, #d1d5db);
		color: var(--text, #1a1a1a);
	}
	th {
		color: var(--muted, #6b7280);
		font-weight: 600;
	}
	tr.inert {
		color: var(--muted, #6b7280);
	}
</style>
