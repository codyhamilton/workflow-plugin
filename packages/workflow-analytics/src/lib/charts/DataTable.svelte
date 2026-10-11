<script lang="ts">
	import { costLabel } from '$lib/format';

	// One row per data row; a row whose `selectable` is false is drawn but inert
	// (the `__other__` bucket). A click fires the same select event as the chart mark.
	// Numeric cells are formatted by the chart `unit`; the exact number is kept in `data-value`.
	let {
		testid,
		columns,
		rows,
		unit,
		onrow
	}: {
		testid: string;
		columns: string[];
		rows: { cells: (string | number)[]; selectable?: boolean }[];
		unit?: string;
		onrow?: (index: number, shift: boolean) => void;
	} = $props();

	function cellText(cell: string | number): string {
		if (typeof cell !== 'number') return cell;
		if (unit === 'usd') return costLabel({ cost: cell, unpriced: cell === 0 ? 1 : 0 });
		if (unit === 'tokens' || unit === 'count') return cell.toLocaleString('en-US');
		return String(cell);
	}
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
				{#each row.cells as cell}
					<td data-value={typeof cell === 'number' ? cell : undefined}>{cellText(cell)}</td>
				{/each}
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
