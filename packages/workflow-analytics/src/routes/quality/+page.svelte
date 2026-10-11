<script lang="ts">
	import { KINDS, type Kind } from '$lib/filters';
	import { scoresParams } from '$lib/params';
	import { getJSON, Superseded } from '$lib/query';
	import { clearError, setError } from '$lib/state.svelte';
	import type { Baselines, Scores } from '$lib/types';
	import { view } from '$lib/view.svelte';

	const W = ['n', 'min', 'p25', 'median', 'p75', 'max'] as const;
	const B = ['n', 'p25', 'median', 'p75'] as const;

	let scores = $state<Scores | null>(null);
	let baselines = $state<Baselines | null>(null);

	// The first valid kind in the URL, default design.
	const include = $derived(view.state.include);
	const kind = $derived<Kind>((include.kind?.[0] as Kind | undefined) ?? 'design');

	$effect(() => {
		const base = view.paramsFor('rest');
		const k = kind;
		if (!base) {
			scores = null;
			baselines = null;
			return;
		}
		let live = true;
		// Both reads are GETs; the baseline is all-time, so only `kind` is sent to it.
		Promise.all([
			getJSON<Scores>('quality-scores', 'analytics/scores', scoresParams(base, k)),
			getJSON<Baselines>('quality-baselines', 'baselines', new URLSearchParams({ kind: k }))
		]).then(
			([s, b]) => {
				if (!live) return;
				clearError();
				scores = s;
				baselines = b;
			},
			(e) => {
				if (!live || e instanceof Superseded) return;
				scores = null;
				baselines = null;
				setError(e);
			}
		);
		return () => {
			live = false;
		};
	});
</script>

<h1>Quality</h1>
<p class="kinds">
	Kind:
	{#each KINDS as k (k)}
		<button type="button" aria-pressed={k === kind} data-testid="quality-kind-{k}" onclick={() => view.setInclude('kind', [k])}
			>{k}</button
		>
	{/each}
</p>
{#if (include.kind?.length ?? 0) > 1}
	<p data-testid="quality-kind-note">The URL names several kinds; showing {kind}.</p>
{/if}
{#if scores}
	<table>
		<thead>
			<tr>
				<th rowspan="2">check</th>
				<th colspan={W.length}>window</th>
				<th colspan={B.length}>all-time baseline</th>
			</tr>
			<tr>
				{#each W as f (f)}<th>{f}</th>{/each}
				{#each B as f (f)}<th class="b">{f}</th>{/each}
			</tr>
		</thead>
		<tbody>
			{#each scores.checks as c (c.name)}
				{@const b = baselines?.checks?.[c.name]}
				<tr data-testid="q-row">
					<th>{c.name}</th>
					{#each W as f (f)}<td data-testid="q-{c.name}-w-{f}">{c[f]}</td>{/each}
					{#each B as f (f)}<td class="b" data-testid="q-{c.name}-b-{f}">{b ? b[f] : ''}</td>{/each}
				</tr>
			{/each}
		</tbody>
	</table>
{/if}

<style>
	button[aria-pressed='true'] {
		font-weight: bold;
	}
	table {
		margin-top: 1rem;
		border-collapse: collapse;
	}
	th,
	td {
		padding: 0.2rem 0.75rem;
		text-align: right;
		border-bottom: 1px solid #eee;
		font-variant-numeric: tabular-nums;
	}
	th:first-child {
		text-align: left;
	}
	.b {
		background: #f6f6fa;
	}
</style>
