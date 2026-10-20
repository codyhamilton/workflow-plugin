<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import {
		aggregate,
		type AggregateAsk,
		type AggregateRequest,
		type AggregateResult,
		type BreakdownResult,
		type TrendResult
	} from '$lib/aggregate';
	import {
		BreakdownChart,
		isDrillableMark,
		TrendChart,
		type BreakdownFrameData,
		type TrendFrameData
	} from '$lib/analysis/chart-frame';
	import { isCollectorMode } from '$lib/api';
	import { PRESETS } from '$lib/presets';
	import { tenantNameFromMe } from '$lib/session-gate';
	import { sessionGate } from '$lib/session-gate.svelte';
	import { Superseded } from '$lib/query';
	import { clearError, setError } from '$lib/state.svelte';
	import type { PresetId } from '$lib/urlstate';
	import { explorationDims, isDimKey } from './dims';
	import { breakdownFrame, ignoredFilters, trendFrame } from './frames';
	import {
		applyDrillToRequest,
		applyWindowState,
		requestToUrlState
	} from './request-mutate';
	import {
		investigationRequestToSearch,
		parseInvestigationRequest
	} from './request-url';

	const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
	const sessionTenant = $derived(isCollectorMode() ? tenantNameFromMe(sessionGate.me) : null);
	const sessionReady = $derived(sessionGate.ready);

	let primary = $state<AggregateResult | null>(null);
	let companionCost = $state<TrendFrameData | null>(null);
	let chartKeys = $state<string[]>([]);

	const queryString = $derived(page.url.search);

	const request = $derived.by(() => {
		try {
			const params = new URLSearchParams(queryString.replace(/^\?/, ''));
			const parsed = parseInvestigationRequest(params, new Date());
			return sessionTenant ? { ...parsed, tenant: sessionTenant } : parsed;
		} catch (e) {
			setError(e);
			return null;
		}
	});

	const urlState = $derived(request ? requestToUrlState(request, new Date()) : null);

	const ignored = $derived(ignoredFilters(primary));

	function commit(next: AggregateRequest, replace = false) {
		const qs = investigationRequestToSearch(next, new Date()).toString();
		const suffix = qs ? `?${qs}` : '';
		const target = `/${suffix}`;
		if (target === `${page.url.pathname}${page.url.search}`) return;
		goto(target, { replaceState: replace, noScroll: true, keepFocus: true });
	}

	function setPreset(id: PresetId) {
		if (!request) return;
		commit(applyWindowState(request, { range: id }, new Date()));
	}

	function onBrushEnd(detail: { from?: string; to?: string }) {
		if (!request || !detail.from || !detail.to) return;
		commit(
			applyWindowState(
				request,
				{ range: 'custom', from: detail.from, to: detail.to },
				new Date()
			)
		);
	}

	function onDrill(detail: { dim: string; value: string; modifiers: { shiftKey: boolean } }) {
		if (!request || !isDrillableMark(detail.dim, detail.value) || !isDimKey(detail.dim)) return;
		commit(
			applyDrillToRequest(request, detail.dim, detail.value, detail.modifiers.shiftKey, new Date())
		);
	}

	function dimSelectValue(ask: AggregateAsk): string {
		if (ask.ask === 'breakdown') return `breakdown:${ask.dim}`;
		if (ask.ask === 'trend' && ask.dim) return `trend:${ask.dim}`;
		if (ask.ask === 'trend') return 'trend';
		return ask.ask;
	}

	function onDimChange(raw: string) {
		if (!request) return;
		const measure =
			request.ask.ask === 'trend' || request.ask.ask === 'breakdown'
				? request.ask.measure
				: 'hook_events';
		let ask: AggregateAsk;
		if (raw === 'trend') {
			ask = { ask: 'trend', measure, bucket: 'day' };
		} else if (raw.startsWith('breakdown:')) {
			const dim = raw.slice('breakdown:'.length);
			if (!isDimKey(dim)) return;
			ask = { ask: 'breakdown', measure, dim };
		} else if (raw.startsWith('trend:')) {
			const dim = raw.slice('trend:'.length);
			if (!isDimKey(dim)) return;
			ask = { ask: 'trend', measure, bucket: 'day', dim };
		} else if (raw === 'executions') {
			ask = { ask: 'executions', bucket: 'day' };
		} else return;
		commit({ ...request, ask });
	}

	const trendData = $derived.by((): TrendFrameData | null => {
		if (!primary || primary.ask !== 'trend') return null;
		const ask = request?.ask;
		if (!ask || ask.ask !== 'trend') return null;
		return trendFrame(ask.measure, ask.bucket, primary as TrendResult, ask.dim);
	});

	const breakdownData = $derived.by((): BreakdownFrameData | null => {
		if (!primary || primary.ask !== 'breakdown') return null;
		const ask = request?.ask;
		if (!ask || ask.ask !== 'breakdown') return null;
		return breakdownFrame(ask.measure, ask.dim, primary as BreakdownResult);
	});

	$effect(() => {
		if (!breakdownData) {
			chartKeys = [];
			return;
		}
		chartKeys = breakdownData.rows.map((r) => r.key);
	});

	$effect(() => {
		if (!sessionReady || !request) return;
		let live = true;
		const fail = (e: unknown) => {
			if (!live || e instanceof Superseded) return;
			setError(e);
		};
		const req = request;
		const wantCompanionCost =
			req.ask.ask === 'trend' &&
			req.ask.measure === 'hook_events' &&
			req.ask.bucket === 'day' &&
			!req.ask.dim;

		(async () => {
			const now = new Date();
			try {
				const result = await aggregate(req, { now });
				if (!live) return;
				clearError();
				primary = result;
				if (wantCompanionCost) {
					const cost = await aggregate(
						{
							...req,
							ask: { ask: 'trend', measure: 'cost_usd', bucket: 'day' }
						},
						{ now }
					);
					if (!live) return;
					companionCost = trendFrame('cost_usd', 'day', cost as TrendResult);
				} else {
					companionCost = null;
				}
			} catch (e) {
				fail(e);
			}
		})();

		return () => {
			live = false;
		};
	});

	const dimOptions = $derived(
		primary ? explorationDims(primary.controls) : (['harness', 'model', 'conversation_id'] as const)
	);
</script>

<div class="investigation" data-testid="investigation-shell">
	<h1>Analysis</h1>
	<p class="tools-hint">Usage, quality, conversations, and saved views — coming soon.</p>

	{#if urlState}
		<div class="presets" role="group" aria-label="Date range">
			{#each PRESETS as p (p.id)}
				<button
					type="button"
					data-testid="preset-{p.id}"
					aria-pressed={urlState.range === p.id}
					onclick={() => setPreset(p.id)}
				>
					{p.label}
				</button>
			{/each}
		</div>
	{/if}

	{#if request}
		<label class="dim">
			View
			<select
				data-testid="investigation-dim"
				value={dimSelectValue(request.ask)}
				onchange={(e) => onDimChange((e.currentTarget as HTMLSelectElement).value)}
			>
				<option value="trend">Time series</option>
				{#each dimOptions as dim (dim)}
					<option value="breakdown:{dim}">Breakdown: {dim}</option>
					<option value="trend:{dim}">Trend by {dim}</option>
				{/each}
				<option value="executions">Executions over time</option>
			</select>
		</label>
	{/if}

	{#each ignored as name (name)}
		<p class="notice" data-testid="notice-ignored">
			<code>{name}</code> does not apply to this measure and was ignored
		</p>
	{/each}

	{#if trendData}
		<section class="chart">
			<TrendChart
				data={trendData}
				testid="investigation-trend-hook_events"
				onbrushend={onBrushEnd}
				ondrill={onDrill}
			/>
		</section>
	{/if}

	{#if breakdownData}
		<section class="chart">
			<BreakdownChart data={breakdownData} testid="investigation-chart" ondrill={onDrill} />
			{#if chartKeys.length}
				<ol data-testid="investigation-chart-keys" class="keys">
					{#each chartKeys as key (key)}<li>{key}</li>{/each}
				</ol>
			{/if}
		</section>
	{/if}

	{#if companionCost}
		<section class="chart">
			<span class="label">{companionCost.measure}</span>
			<TrendChart data={companionCost} testid="investigation-trend-cost_usd" />
		</section>
	{/if}
</div>

<style>
	.tools-hint {
		color: var(--muted);
		font-size: 0.9rem;
	}
	.presets {
		display: flex;
		flex-wrap: wrap;
		gap: 0.35rem;
		margin: 0.75rem 0;
	}
	.dim {
		display: block;
		margin-bottom: 0.75rem;
	}
	.chart {
		margin-top: 1rem;
	}
	.label {
		display: block;
		font-size: 0.85rem;
		color: var(--muted);
		margin-bottom: 0.35rem;
	}
	.notice {
		margin: var(--space-2) 0 0;
		padding: var(--space-1) var(--space-2);
		border: 1px solid var(--danger);
		background: var(--surface);
		font-size: 0.85rem;
	}
	.keys {
		position: absolute;
		width: 1px;
		height: 1px;
		overflow: hidden;
		clip: rect(0, 0, 0, 0);
	}
</style>
