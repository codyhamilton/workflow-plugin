<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { apiGet } from '$lib/api';
	import { dateToFrom, dateToTo, mergeQuery, parseFilter, toDate, type Filter } from '$lib/filters';
	import { setError } from '$lib/state.svelte';
	import type { Facets } from '$lib/types';

	const filter = $derived(parseFilter(page.url.searchParams));
	let facets = $state<Facets | null>(null);

	// Facets follow the window only (dimension filters do not narrow them).
	$effect(() => {
		const q = new URLSearchParams();
		if (filter.from) q.set('from', filter.from);
		if (filter.to) q.set('to', filter.to);
		let live = true;
		apiGet<Facets>('analytics/facets', q).then(
			(f) => live && (facets = f),
			(e) => live && setError(e)
		);
		return () => (live = false);
	});

	// "" means "missing" in the API; filtering on it is not offered. Keep a selected value visible.
	function options(listed: string[] | undefined, selected: string[]): string[] {
		const out = (listed ?? []).filter((v) => v !== '');
		for (const s of selected) if (s !== '' && !out.includes(s)) out.push(s);
		return out;
	}

	function change(next: Filter) {
		const qs = mergeQuery(page.url.searchParams, next).toString();
		goto(`${page.url.pathname}${qs ? `?${qs}` : ''}`, { keepFocus: true, noScroll: true });
	}

	function pick(name: 'repo_id' | 'harness' | 'kind' | 'plan', e: Event) {
		const sel = e.currentTarget as HTMLSelectElement;
		const values = [...sel.selectedOptions].map((o) => o.value);
		change({ ...filter, [name]: values } as Filter);
	}

	const groups = $derived([
		{ name: 'repo_id' as const, title: 'Repo', values: options(facets?.repos, filter.repo_id), selected: filter.repo_id },
		{ name: 'harness' as const, title: 'Harness', values: options(facets?.harnesses, filter.harness), selected: filter.harness },
		{ name: 'kind' as const, title: 'Kind', values: options(facets?.kinds, filter.kind), selected: filter.kind as string[] },
		{ name: 'plan' as const, title: 'Plan', values: options(facets?.plans, filter.plan), selected: filter.plan }
	]);
</script>

<form class="filters" onsubmit={(e) => e.preventDefault()}>
	<label>
		From
		<input
			type="date"
			data-testid="filter-from"
			value={toDate(filter.from)}
			onchange={(e) => change({ ...filter, from: dateToFrom(e.currentTarget.value) })}
		/>
	</label>
	<label>
		To
		<input
			type="date"
			data-testid="filter-to"
			value={toDate(filter.to)}
			onchange={(e) => change({ ...filter, to: dateToTo(e.currentTarget.value) })}
		/>
	</label>
	{#each groups as g (g.name)}
		<label>
			{g.title}
			<select multiple size="3" data-testid="filter-{g.name}" onchange={(e) => pick(g.name, e)}>
				{#each g.values as v (v)}
					<option value={v} selected={g.selected.includes(v)}>{v}</option>
				{/each}
			</select>
		</label>
	{/each}
</form>

<style>
	.filters {
		display: flex;
		flex-wrap: wrap;
		gap: 1rem;
		align-items: flex-start;
		padding: 0.75rem 0;
		border-bottom: 1px solid #ddd;
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
