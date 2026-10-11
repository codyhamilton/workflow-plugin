<script lang="ts">
	import { afterNavigate } from '$app/navigation';
	import { page } from '$app/state';
	import { ApiError } from '$lib/api';
	import { costLabel, label, num } from '$lib/format';
	import { getJSON } from '$lib/query';
	import { clearError, setError } from '$lib/state.svelte';
	import type { ConversationDetail, TimelineEvent } from '$lib/types';

	const ROW_H = 28; // fixed px per timeline row, so the window can be computed without measuring
	const MARGIN = 10; // rows kept above and below the viewport

	let data = $state<ConversationDetail | null>(null);
	let message = $state('');
	let scroller = $state<HTMLDivElement | null>(null);
	let scrollTop = $state(0);
	let viewportH = $state(600);

	const id = $derived(page.url.searchParams.get('id') ?? '');

	// The list the user came from: kept in memory for the session and in sessionStorage so a reload
	// keeps it. Only known site routes count; /conversation and /settings are excluded (the layout
	// hides the chrome on /conversation, and /settings is not a list).
	const ROUTE_NAMES: Record<string, string> = {
		'/': 'Overview',
		'/trends': 'Trends',
		'/usage': 'Usage',
		'/repos': 'Repos',
		'/hooks': 'Hooks',
		'/quality': 'Quality',
		'/executions': 'Executions',
		'/conversations': 'Conversations',
		'/explore': 'Explore'
	};
	const LAST_LIST_KEY = 'workflow-analytics-last-list';

	function readLastList(): { href: string; name: string } | null {
		try {
			const raw = sessionStorage.getItem(LAST_LIST_KEY);
			if (!raw) return null;
			const v = JSON.parse(raw);
			if (v && typeof v.href === 'string' && typeof v.name === 'string') return v;
		} catch {
			// sessionStorage can be unavailable (privacy mode); fall through to the default.
		}
		return null;
	}

	let lastList = $state<{ href: string; name: string } | null>(null);

	afterNavigate(({ from }) => {
		const name = from ? ROUTE_NAMES[from.url.pathname] : undefined;
		if (from && name) {
			lastList = { href: from.url.pathname + from.url.search, name };
			try {
				sessionStorage.setItem(LAST_LIST_KEY, JSON.stringify(lastList));
			} catch {
				// A failed write only loses the reload case.
			}
		} else if (!lastList) {
			lastList = readLastList();
		}
	});

	// One request for this conversation; the window and filters do not apply here.
	$effect(() => {
		const q = new URLSearchParams({ id });
		let live = true;
		data = null;
		message = '';
		getJSON<ConversationDetail>('conversation', 'analytics/conversation', q).then(
			(d) => {
				if (!live) return;
				clearError();
				data = d;
			},
			(e) => {
				if (!live) return;
				if (e instanceof ApiError && e.status === 404) message = 'No such conversation';
				else if (e instanceof ApiError && e.status === 400) message = 'Open a conversation from the list';
				else setError(e);
			}
		);
		return () => (live = false);
	});

	$effect(() => {
		if (scroller) viewportH = scroller.clientHeight || viewportH;
	});

	const events = $derived(
		[...(data?.events ?? [])].sort((a, b) => (a.ts < b.ts ? -1 : a.ts > b.ts ? 1 : 0))
	);
	const start = $derived(Math.max(0, Math.floor(scrollTop / ROW_H) - MARGIN));
	const end = $derived(Math.min(events.length, Math.ceil((scrollTop + viewportH) / ROW_H) + MARGIN));
	const windowed = $derived(events.slice(start, end).map((e, i) => ({ e, i: start + i })));

	const stamp = (v: string) => new Date(v).toLocaleString();
	const list = (a: string[]) => (a.length ? a.join(', ') : label(''));
	const tokens = (e: TimelineEvent) =>
		e.tokens
			? `in ${num(e.tokens.in)} · out ${num(e.tokens.out)} · cache r ${num(e.tokens.cache_read)} · w ${num(
					e.tokens.cache_write
				)} · reason ${num(e.tokens.reasoning)}`
			: '';
	const rowCost = (e: TimelineEvent) => {
		// Tokens in or out make this a usage event; an unpriced model carries `cost_usd: 0`, not null.
		// A row with no tokens in or out is not a usage row, so it shows no cost text at all.
		const used = (e.tokens?.in ?? 0) + (e.tokens?.out ?? 0);
		if (used > 0 && !(e.cost_usd != null && e.cost_usd > 0)) return 'unpriced';
		if (e.cost_usd != null && e.cost_usd > 0) return costLabel({ cost: e.cost_usd, unpriced: 0, calls: 1 });
		return '';
	};
</script>

<a data-testid="back-to-conversations" href={lastList?.href ?? '/conversations'}
	>← Back to {lastList?.name ?? 'Conversations'}</a
>

{#if message}
	<p data-testid="conversation-message">{message}</p>
{:else if data}
	<h1>{label(data.conversation_id)}</h1>
	<div class="meta">
		<span><b>harness</b> {label(data.harness)}</span>
		<span><b>repos</b> {list(data.repos)}</span>
		<span><b>models</b> {list(data.models)}</span>
		<span><b>first</b> <time datetime={data.first_ts}>{stamp(data.first_ts)}</time></span>
		<span><b>last</b> <time datetime={data.last_ts}>{stamp(data.last_ts)}</time></span>
	</div>

	<div class="totals">
		<div class="tile"><span class="n" data-testid="conv-total-model_calls">{num(data.totals.model_calls)}</span><span class="name">model calls</span></div>
		<div class="tile"><span class="n" data-testid="conv-total-tokens_in">{num(data.totals.tokens_in)}</span><span class="name">tokens in</span></div>
		<div class="tile"><span class="n" data-testid="conv-total-tokens_out">{num(data.totals.tokens_out)}</span><span class="name">tokens out</span></div>
		<div class="tile"><span class="n" data-testid="conv-total-tokens_cache_read">{num(data.totals.tokens_cache_read)}</span><span class="name">cache read</span></div>
		<div class="tile"><span class="n" data-testid="conv-total-tokens_cache_write">{num(data.totals.tokens_cache_write)}</span><span class="name">cache write</span></div>
		<div class="tile"><span class="n" data-testid="conv-total-tokens_reasoning">{num(data.totals.tokens_reasoning)}</span><span class="name">reasoning</span></div>
		<div class="tile"><span class="n" data-testid="conv-total-unpriced_calls">{num(data.totals.unpriced_calls)}</span><span class="name">unpriced calls</span></div>
		<div class="tile"><span class="n" data-testid="conv-total-cost">{costLabel({ cost: data.totals.cost_usd, unpriced: data.totals.unpriced_calls, calls: data.totals.model_calls })}</span><span class="name">cost</span></div>
	</div>

	{#if data.truncated}
		<p data-testid="timeline-truncated">showing the first 5,000 events</p>
	{/if}

	<div
		class="timeline"
		bind:this={scroller}
		onscroll={(e) => (scrollTop = (e.currentTarget as HTMLDivElement).scrollTop)}
	>
		<div class="spacer" style="height:{events.length * ROW_H}px">
			{#each windowed as { e, i } (i)}
				<div class="row" data-testid="timeline-row" style="top:{i * ROW_H}px; height:{ROW_H}px">
					<time class="t" datetime={e.ts}>{stamp(e.ts)}</time>
					<span class="ev">{e.norm_event || e.event || label('')}</span>
					<span class="dim">{label(e.tool)}</span>
					<span class="dim">{label(e.model)}</span>
					<span class="dim path">{label(e.path)}</span>
					{#if tokens(e)}<span class="dim">{tokens(e)}</span>{/if}
					{#if rowCost(e)}<span class="dim">{rowCost(e)}</span>{/if}
				</div>
			{/each}
		</div>
	</div>
{/if}

<style>
	.meta {
		display: flex;
		flex-wrap: wrap;
		gap: 0.25rem 1.25rem;
		margin: 0.5rem 0 1rem;
	}
	.totals {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem;
	}
	.tile {
		min-width: 6rem;
		padding: 0.5rem 0.75rem;
		border: 1px solid var(--border, #ddd);
		border-radius: 4px;
		display: flex;
		flex-direction: column;
	}
	.n {
		font-size: 1.4rem;
		font-variant-numeric: tabular-nums;
	}
	.name {
		font-size: 0.8rem;
		color: #555;
	}
	.timeline {
		height: 600px;
		margin-top: 1rem;
		overflow-y: auto;
		border: 1px solid var(--border, #eee);
	}
	.row {
		position: absolute;
		left: 0;
		right: 0;
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 0 0.5rem;
		box-sizing: border-box;
		white-space: nowrap;
		border-bottom: 1px solid #f2f2f2;
	}
	.t {
		flex: 0 0 11rem;
		font-variant-numeric: tabular-nums;
		color: #555;
	}
	.ev {
		flex: 0 0 14rem;
	}
	.dim {
		color: #555;
	}
	.path {
		max-width: 20rem;
		overflow: hidden;
		text-overflow: ellipsis;
	}
</style>
