<script lang="ts">
	import type { AggregateRequest, ConversationResult, ConversationsResult } from '$lib/aggregate';
	import { costLabel, label, num } from '$lib/format';
	import type { TimelineEvent, Totals } from '$lib/types';
	import { requestToUrlState } from '../request-mutate';
	import { resolveWindow } from '$lib/params';

	let {
		request,
		primary,
		commit,
		tz
	}: {
		request: AggregateRequest;
		primary: ConversationsResult | ConversationResult | null;
		commit: (next: AggregateRequest, replace?: boolean) => void;
		tz: string;
	} = $props();

	const list = $derived(primary?.ask === 'conversations' ? primary.rows : []);
	const detail = $derived(primary?.ask === 'conversation' ? primary.detail : null);

	const eventWindow = $derived.by(() => {
		const state = requestToUrlState(request);
		if (state.range === 'all') return null;
		const w = resolveWindow(state, new Date(), tz, 'rest');
		if (w.from === undefined || w.to === undefined) return null;
		return { from: w.from.getTime(), to: w.to.getTime() };
	});

	const events = $derived(
		detail ? [...detail.events].sort((a, b) => (a.ts < b.ts ? -1 : a.ts > b.ts ? 1 : 0)) : []
	);

	function rowCost(r: ConversationsResult['rows'][number]): string {
		return costLabel({
			cost: r.cost_usd,
			unpriced: r.unpriced_calls,
			calls: r.model_calls
		});
	}

	function openConversation(id: string) {
		commit({ ...request, ask: { ask: 'conversation', id } });
	}

	function backToList() {
		commit({ ...request, ask: { ask: 'conversations' } });
	}

	function inWindow(ts: string): boolean {
		const w = eventWindow;
		if (!w) return true;
		const t = new Date(ts).getTime();
		return t >= w.from && t <= w.to;
	}

	const stamp = (v: string) => new Date(v).toLocaleString();

	const WINDOW_TOTAL_KEYS = [
		'model_calls',
		'tokens_in',
		'tokens_out',
		'tokens_cache_read',
		'tokens_cache_write',
		'tokens_reasoning',
		'unpriced_calls',
		'cost_usd'
	] as const satisfies readonly (keyof Totals)[];

	const windowTotal = (t: Totals, k: keyof Totals) => {
		if (k === 'cost_usd')
			return costLabel({ cost: t.cost_usd, unpriced: t.unpriced_calls, calls: t.model_calls });
		return num(t[k]);
	};

	function rowEventCost(e: TimelineEvent): string {
		const used = (e.tokens?.in ?? 0) + (e.tokens?.out ?? 0);
		if (used > 0 && !(e.cost_usd != null && e.cost_usd > 0)) return 'unpriced';
		if (e.cost_usd != null && e.cost_usd > 0) return costLabel({ cost: e.cost_usd, unpriced: 0, calls: 1 });
		return '';
	}
</script>

<div class="conv-tool" data-testid="investigation-conversations-tool">
	{#if detail}
		<button type="button" data-testid="investigation-conv-back" onclick={backToList}>← Conversations</button>
		<h2>{label(detail.conversation_id)}</h2>
		<div class="totals">
			<div class="tile">
				<span class="n" data-testid="investigation-conv-total-model_calls">{num(detail.totals.model_calls)}</span>
				<span class="name">model calls</span>
			</div>
			<div class="tile">
				<span class="n" data-testid="investigation-conv-total-cost"
					>{costLabel({
						cost: detail.totals.cost_usd,
						unpriced: detail.totals.unpriced_calls,
						calls: detail.totals.model_calls
					})}</span
				>
				<span class="name">cost</span>
			</div>
		</div>
		{#if detail.window_totals}
			<div class="totals" data-testid="investigation-conv-window-totals">
				{#each WINDOW_TOTAL_KEYS as k (k)}
					<div class="tile">
						<span class="n" data-testid="investigation-conv-window-{k}">{windowTotal(detail.window_totals!, k)}</span>
						<span class="name">{k.replace(/_/g, ' ')}</span>
					</div>
				{/each}
			</div>
		{/if}
		<div class="timeline">
			{#each events as e (e.ts + (e.event ?? '') + (e.norm_event ?? ''))}
				<div
					class="row"
					class:out={eventWindow && !inWindow(e.ts)}
					data-testid="investigation-timeline-row"
				>
					<time datetime={e.ts}>{stamp(e.ts)}</time>
					{#if eventWindow && !inWindow(e.ts)}
						<span class="badge" data-testid="investigation-timeline-out">out of window</span>
					{:else if eventWindow}
						<span class="badge in" data-testid="investigation-timeline-in">in window</span>
					{/if}
					<span>{e.norm_event || e.event || label('')}</span>
					{#if rowEventCost(e)}<span>{rowEventCost(e)}</span>{/if}
				</div>
			{/each}
		</div>
	{:else}
		<div class="head">
			<span>conversation</span><span>model</span><span>cost</span>
		</div>
		{#each list as r (r.conversation_id)}
			<div class="list-row" data-testid="investigation-conv-row">
				<button
					type="button"
					class="link"
					data-testid="investigation-conv-{r.conversation_id}-id"
					onclick={() => openConversation(r.conversation_id)}>{r.conversation_id}</button
				>
				<span data-testid="investigation-conv-{r.conversation_id}-model">{label(r.model)}</span>
				<span data-testid="investigation-conv-{r.conversation_id}-cost">{rowCost(r)}</span>
			</div>
		{/each}
	{/if}
</div>

<style>
	.head,
	.list-row {
		display: grid;
		grid-template-columns: 1fr 2fr 1fr;
		gap: 0.5rem;
		padding: 0.25rem 0;
		border-bottom: 1px solid var(--border);
	}
	.link {
		text-align: left;
		background: none;
		border: none;
		padding: 0;
		color: inherit;
		cursor: pointer;
		text-decoration: underline;
	}
	.totals {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		margin: 0.5rem 0;
	}
	.tile {
		border: 1px solid var(--border);
		padding: 0.35rem 0.5rem;
		border-radius: 4px;
	}
	.timeline .row {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		padding: 0.2rem 0;
		border-bottom: 1px solid var(--border);
		font-size: 0.85rem;
	}
	.row.out {
		opacity: 0.65;
	}
	.badge.in {
		color: var(--accent, inherit);
	}
</style>
