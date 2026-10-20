<script lang="ts">
	import '$lib/analysis/tokens.css';
	import '$lib/theme.css';
	import RouteSurface from '$lib/analysis/RouteSurface.svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import {
		getThemePreference,
		initTheme,
		setThemePreference,
		type ThemePreference
	} from '$lib/charts/theme';
	import Notices from '$lib/components/Notices.svelte';
	import { ApiError, fetchMe, isCollectorMode } from '$lib/api';
	import {
		decideAfterMeFetch,
		readBearer,
		readConfiguredBase,
		shouldNavigateToProfile,
		type MeFetchResult
	} from '$lib/session-gate';
	import { beginSessionGate, finishSessionGate, sessionGate } from '$lib/session-gate.svelte';
	import { clearError, fetchError, pruneNotices, setNoticeView } from '$lib/state.svelte';

	let { children } = $props();

	const nav = [
		['/', 'Overview'],
		['/profile', 'Profile'],
		['/settings', 'Settings']
	];

	const chrome = $derived(
		page.url.pathname !== '/settings' &&
			page.url.pathname !== '/login' &&
			page.url.pathname !== '/profile' &&
			page.url.pathname !== '/device' &&
			!page.url.pathname.startsWith('/oauth/')
	);

	const collector = $derived(isCollectorMode());
	const noTenant = $derived(collector && fetchError.status === 403 && fetchError.message === 'no such tenant');

	function navHref(path: string): string {
		return path === '/settings' || path === '/profile' ? path : path + page.url.search;
	}

	const viewKey = $derived(page.url.pathname + page.url.search);
	$effect.pre(() => setNoticeView(viewKey));

	$effect(() => {
		page.url.pathname;
		page.url.search;
		clearError();
		pruneNotices();
	});

	$effect(() => {
		let live = true;
		beginSessionGate();

		void (async () => {
			let me: MeFetchResult;
			try {
				const body = await fetchMe();
				me = { kind: 'ok', body };
			} catch (e) {
				if (e instanceof ApiError) {
					me = { kind: 'http', status: e.status, message: e.message };
				} else {
					me = { kind: 'other' };
				}
			}
			if (!live) return;

			const hostname = location.hostname;
			const pathname = page.url.pathname;
			const search = page.url.search;
			const decision = decideAfterMeFetch({
				hostname,
				pathname,
				search,
				configuredBase: readConfiguredBase(),
				bearer: readBearer(),
				me
			});
			if (decision !== 'stay') {
				const ret = encodeURIComponent(decision.login);
				void goto(`/login?return=${ret}`);
			}
			finishSessionGate(me);
		})();

		return () => {
			live = false;
		};
	});

	$effect(() => {
		if (!sessionGate.ready || !sessionGate.me) return;
		if (
			shouldNavigateToProfile({
				pathname: page.url.pathname,
				me: sessionGate.me,
				fetchErrorStatus: fetchError.status,
				fetchErrorMessage: fetchError.message
			})
		) {
			void goto('/profile');
		}
	});

	let themePref = $state<ThemePreference>('system');
	$effect(() => {
		const off = initTheme();
		themePref = getThemePreference();
		return off;
	});

	function chooseTheme(pref: ThemePreference) {
		setThemePreference(pref);
		themePref = pref;
	}
</script>

<svelte:head>
	<script>
		(function () {
			var key = 'yakka-analytics-theme';
			var pref = 'system';
			try {
				var v = localStorage.getItem(key);
				if (v === 'light' || v === 'dark' || v === 'system') pref = v;
			} catch (e) {}
			var dark =
				pref === 'dark' ||
				(pref === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
			document.documentElement.dataset.theme = dark ? 'dark' : 'light';
		})();
	</script>
</svelte:head>

<header>
		<strong>Workflow analytics</strong>
		<div class="theme" role="group" aria-label="Theme">
			<button
				type="button"
				data-testid="theme-system"
				aria-pressed={themePref === 'system'}
				onclick={() => chooseTheme('system')}>System</button
			>
			<button
				type="button"
				data-testid="theme-light"
				aria-pressed={themePref === 'light'}
				onclick={() => chooseTheme('light')}>Light</button
			>
			<button
				type="button"
				data-testid="theme-dark"
				aria-pressed={themePref === 'dark'}
				onclick={() => chooseTheme('dark')}>Dark</button
			>
		</div>
		<nav>
			{#each nav as [href, text] (href)}
				<a href={navHref(href)} aria-current={page.url.pathname === href ? 'page' : undefined}>{text}</a>
			{/each}
		</nav>
	</header>

	<main>
		{#if chrome}
			<RouteSurface>
				<Notices />
				{#if fetchError.message}
					<div class="error" role="alert" data-testid="error-panel">
						<p>{fetchError.message}{fetchError.status ? ` (HTTP ${fetchError.status})` : ''}</p>
						{#if noTenant}
							<p>You do not have a tenant yet. <a href="/profile">Create one on your profile</a>.</p>
						{:else if fetchError.status === 401 || fetchError.network}
							<p>Check the connection in <a href="/settings">/settings</a>: the API base URL and the token.</p>
						{/if}
					</div>
				{/if}
				{#if sessionGate.ready}
					{@render children()}
				{/if}
			</RouteSurface>
		{:else}
			{#if fetchError.message}
				<div class="error" role="alert" data-testid="error-panel">
					<p>{fetchError.message}{fetchError.status ? ` (HTTP ${fetchError.status})` : ''}</p>
					{#if noTenant}
						<p>You do not have a tenant yet. <a href="/profile">Create one on your profile</a>.</p>
					{:else if fetchError.status === 401 || fetchError.network}
						<p>Check the connection in <a href="/settings">/settings</a>: the API base URL and the token.</p>
					{/if}
				</div>
			{/if}
			{#if sessionGate.ready}
				{@render children()}
			{/if}
		{/if}
	</main>

<style>
	:global(body) {
		margin: 0;
		overflow-x: hidden;
		font-family: system-ui, sans-serif;
		color: var(--text);
		background: var(--bg);
	}
	header {
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-3) var(--space-4);
		align-items: baseline;
		padding: var(--space-3) var(--space-4);
		background: var(--surface);
		border-bottom: 1px solid var(--border);
	}
	.theme {
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-2);
	}
	.theme button {
		font: inherit;
		color: var(--text);
		background: var(--bg);
		border: 1px solid var(--border);
		padding: var(--space-1) var(--space-2);
		cursor: pointer;
	}
	.theme button[aria-pressed='true'] {
		border-color: var(--accent);
		color: var(--accent);
		font-weight: 600;
	}
	nav {
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-2) var(--space-3);
	}
	nav a {
		color: var(--text);
		text-decoration: none;
	}
	nav a[aria-current='page'] {
		font-weight: 700;
		color: var(--accent);
	}
	main {
		padding: 0 var(--space-4) var(--space-5);
		overflow-x: hidden;
	}
	.error {
		margin: var(--space-3) 0;
		padding: var(--space-2) var(--space-3);
		border: 1px solid var(--danger);
		background: var(--surface);
		color: var(--text);
	}
	.error p {
		margin: 0.25rem 0;
	}
</style>
