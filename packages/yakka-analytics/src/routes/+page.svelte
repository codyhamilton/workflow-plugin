<script lang="ts">
	import { aggregate, type TrendResult } from '$lib/aggregate';
	import { TrendChart, type TrendFrameData } from '$lib/analysis/chart-frame';
	import { isCollectorMode } from '$lib/api';
	import { tenantNameFromMe } from '$lib/session-gate';
	import { sessionGate } from '$lib/session-gate.svelte';
	import { Superseded } from '$lib/query';
	import { clearError, setError } from '$lib/state.svelte';

	const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;

	const sessionTenant = $derived(isCollectorMode() ? tenantNameFromMe(sessionGate.me) : null);
	const sessionReady = $derived(sessionGate.ready);

	let hookEvents = $state<TrendFrameData | null>(null);
	let costUsd = $state<TrendFrameData | null>(null);

	function trendFrame(measure: string, result: TrendResult): TrendFrameData {
		return {
			measure,
			bucket: 'day',
			series: (result.series ?? []).map((s) => ({ name: s.key, points: s.points }))
		};
	}

	$effect(() => {
		if (!sessionReady) return;

		let live = true;
		const fail = (e: unknown) => {
			if (!live || e instanceof Superseded) return;
			setError(e);
		};

		const tenant = sessionTenant;
		const base = tenant ? { tenant, window: { tz } } : { window: { tz } };

		(async () => {
			const now = new Date();
			try {
				const hook = await aggregate(
					{
						...base,
						ask: { ask: 'trend', measure: 'hook_events', bucket: 'day' }
					},
					{ now }
				);
				if (!live) return;
				clearError();
				hookEvents = trendFrame('hook_events', hook as TrendResult);

				const cost = await aggregate(
					{
						...base,
						ask: { ask: 'trend', measure: 'cost_usd', bucket: 'day' }
					},
					{ now }
				);
				if (!live) return;
				clearError();
				costUsd = trendFrame('cost_usd', cost as TrendResult);
			} catch (e) {
				fail(e);
			}
		})();

		return () => {
			live = false;
		};
	});
</script>

<h1>Overview</h1>

{#if hookEvents}
	<section class="trend">
		<span class="label">{hookEvents.measure}</span>
		<TrendChart data={hookEvents} testid="landing-trend-hook_events" />
	</section>
{/if}
{#if costUsd}
	<section class="trend">
		<span class="label">{costUsd.measure}</span>
		<TrendChart data={costUsd} testid="landing-trend-cost_usd" />
	</section>
{/if}

<style>
	.trend {
		margin-top: 1rem;
	}
	.label {
		display: block;
		font-size: 0.85rem;
		color: var(--muted);
		margin-bottom: 0.35rem;
	}
</style>
