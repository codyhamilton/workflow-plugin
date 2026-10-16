<script lang="ts">
	import { dateToFrom, dateToTo } from '$lib/filters';
	import { PRESETS, presetWindow } from '$lib/presets';
	import type { DimKey } from '$lib/urlstate';
	import { view } from '$lib/view.svelte';

	const MULTIS: DimKey[] = ['repo_id', 'harness', 'kind', 'plan', 'model'];
	const LABELS: Record<string, string> = {
		repo_id: 'Repo',
		harness: 'Harness',
		kind: 'Kind',
		plan: 'Plan',
		model: 'Model'
	};

	// The window the date inputs display: the custom range, or the preset expanded at `now`.
	const win = $derived.by(() => {
		const s = view.state;
		if (s.range === 'custom') {
			return { from: s.from?.slice(0, 10) ?? '', to: s.to?.slice(0, 10) ?? '' };
		}
		const w = presetWindow(s.range, new Date(), view.tz);
		return {
			from: w ? w.from.toISOString().slice(0, 10) : '',
			to: w ? w.to.toISOString().slice(0, 10) : ''
		};
	});

	// "" means "missing" in the API; do not offer it, but keep a selected value visible.
	function options(key: DimKey): string[] {
		const selected = view.state.include[key] ?? [];
		const listed = (view.facets?.[key] ?? []).filter((v) => v !== '');
		return [...new Set([...listed, ...selected.filter((v) => v !== '')])];
	}

	function keepFrom(v: string): Date {
		const s = view.state;
		if (s.range === 'custom' && s.from) return new Date(s.from);
		const w = presetWindow(s.range, new Date(), view.tz);
		return w ? w.from : new Date(dateToFrom(v)!);
	}
	function keepTo(v: string): Date {
		const s = view.state;
		if (s.range === 'custom' && s.to) return new Date(s.to);
		const w = presetWindow(s.range, new Date(), view.tz);
		return w ? w.to : new Date(dateToTo(v)!);
	}

	function onFrom(e: Event) {
		const v = (e.currentTarget as HTMLInputElement).value;
		if (!v) return;
		view.setWindow(new Date(dateToFrom(v)!), keepTo(v));
	}
	function onTo(e: Event) {
		const v = (e.currentTarget as HTMLInputElement).value;
		if (!v) return;
		view.setWindow(keepFrom(v), new Date(dateToTo(v)!));
	}

	function onSelect(key: DimKey, e: Event) {
		const sel = Array.from((e.currentTarget as HTMLSelectElement).selectedOptions, (o) => o.value);
		const cur = view.state.include[key] ?? [];
		for (const v of sel) if (!cur.includes(v)) view.drill(key, v);
		for (const v of cur) if (!sel.includes(v)) view.removeChip(key, v);
	}
</script>

<form class="filters" onsubmit={(e) => e.preventDefault()}>
	<div class="presets" role="group" aria-label="Date range">
		{#each PRESETS as p (p.id)}
			<button
				type="button"
				data-testid="preset-{p.id}"
				aria-pressed={view.state.range === p.id}
				onclick={() => view.setPreset(p.id)}
			>
				{p.label}
			</button>
		{/each}
	</div>
	<label>
		From
		<input type="date" data-testid="filter-from" value={win.from} onchange={onFrom} />
	</label>
	<label>
		To
		<input type="date" data-testid="filter-to" value={win.to} onchange={onTo} />
	</label>
	{#each MULTIS as key (key)}
		<label>
			{LABELS[key]}
			<select multiple size="3" data-testid="filter-{key}" onchange={(e) => onSelect(key, e)}>
				{#each options(key) as v (v)}
					<option value={v} selected={(view.state.include[key] ?? []).includes(v)}>{v}</option>
				{/each}
			</select>
		</label>
	{/each}
</form>

<style>
	.filters {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem 1rem;
		align-items: flex-end;
		padding: 0.75rem 0;
		border-bottom: 1px solid var(--border);
	}
	.presets {
		display: flex;
		flex-wrap: wrap;
		gap: 0.25rem;
	}
	.presets button[aria-pressed='true'] {
		background: var(--accent);
		color: var(--bg);
		border-color: var(--accent);
	}
	label {
		display: flex;
		flex-direction: column;
		font-size: 0.8rem;
		gap: 0.25rem;
	}
	select {
		min-width: 9rem;
	}
</style>
