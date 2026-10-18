<script lang="ts">
	import { page } from '$app/state';
	import {
		ApiError,
		createTenant,
		fetchMe,
		deviceAuthorizeAction,
		isCollectorMode,
		isValidLoopbackRedirectUri,
		oauthLoginPath,
		type MeResponse
	} from '$lib/api';

	const deviceState = $derived(page.url.searchParams.get('state') ?? '');
	const redirectUri = $derived(page.url.searchParams.get('redirect_uri') ?? '');
	const oauthReturn = $derived(page.url.pathname + page.url.search);
	const loginHref = $derived(oauthLoginPath(page.url.hostname, oauthReturn));
	const authorizeAction = $derived(deviceAuthorizeAction(page.url.hostname));

	const paramsOk = $derived(
		deviceState !== '' && redirectUri !== '' && isValidLoopbackRedirectUri(redirectUri)
	);

	let me = $state<MeResponse | null>(null);
	let loading = $state(true);
	let needsSignIn = $state(false);

	let tenantName = $state('');
	let selectedTenant = $state('');
	let grantScope = $state<'' | 'read' | 'read_write'>('');
	let expiresLocal = $state('');

	let tenantStatus = $state('');

	function parseFutureExpiry(local: string): string | null {
		if (!local.trim()) return null;
		const d = new Date(local);
		if (Number.isNaN(d.getTime())) return null;
		const iso = d.toISOString();
		if (d.getTime() <= Date.now()) return null;
		return iso;
	}

	const expiresAt = $derived(parseFutureExpiry(expiresLocal));

	const canSubmit = $derived(
		paramsOk &&
			me !== null &&
			selectedTenant !== '' &&
			grantScope !== '' &&
			expiresAt !== null
	);

	async function reload() {
		loading = true;
		needsSignIn = false;
		try {
			me = await fetchMe();
		} catch (e) {
			me = null;
			if (e instanceof ApiError && e.status === 401) {
				needsSignIn = true;
			}
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		if (!isCollectorMode()) {
			loading = false;
			return;
		}
		void reload();
	});

	async function submitTenant(e: Event) {
		e.preventDefault();
		tenantStatus = '';
		try {
			const { name } = await createTenant(tenantName.trim());
			tenantStatus = `Created tenant ${name}.`;
			tenantName = '';
			await reload();
			selectedTenant = name;
		} catch (err) {
			tenantStatus = err instanceof ApiError ? err.message : 'Could not create tenant.';
		}
	}
</script>

<h1>Authorize yakka CLI</h1>

{#if !isCollectorMode()}
	<p>This page needs the collector (this site, or API base <code>https://api.yakka.build</code>).</p>
{:else if loading}
	<p>Loading…</p>
{:else if needsSignIn}
	<p>Sign in to continue authorizing this device.</p>
	<p>
		<a href={loginHref} data-testid="device-oauth-login">
			Sign in with GitHub
		</a>
	</p>
{:else if me}
	<p>Signed in as <strong>{me.github_login}</strong>.</p>

	{#if !paramsOk}
		<p class="warn" role="alert" data-testid="device-params-error">
			This link is missing a valid <code>state</code> and loopback <code>redirect_uri</code>. Start authorization
			from <code>yakka login</code> on your machine.
		</p>
	{/if}

	<section>
		<h2>Tenant</h2>
		{#if me.tenants.length === 0}
			<p>You do not have a tenant yet. Create one to issue a token.</p>
			<form onsubmit={submitTenant}>
				<label>
					Tenant name
					<input data-testid="device-tenant-name" bind:value={tenantName} required autocomplete="off" />
				</label>
				<button type="submit" data-testid="device-tenant-submit">Create tenant</button>
				<span role="status">{tenantStatus}</span>
			</form>
		{:else}
			<form
				id="device-form"
				method="POST"
				action={authorizeAction}
				data-testid="device-authorize-form"
			>
				<input type="hidden" name="redirect_uri" value={redirectUri} />
				<input type="hidden" name="state" value={deviceState} />
				{#if expiresAt}
					<input type="hidden" name="expires_at" value={expiresAt} />
				{/if}

				<label>
					Tenant
					<select data-testid="device-tenant" name="tenant" bind:value={selectedTenant} required>
						<option value="" disabled selected>Select tenant</option>
						{#each me.tenants as t (t.name)}
							<option value={t.name}>{t.name}</option>
						{/each}
					</select>
				</label>

				<label>
					Grant
					<select data-testid="device-grant" name="scope" bind:value={grantScope} required>
						<option value="" disabled selected>Select grant</option>
						<option value="read">read</option>
						<option value="read_write">read_write</option>
					</select>
				</label>

				<label>
					Expires (UTC)
					<input
						data-testid="device-expires"
						type="datetime-local"
						bind:value={expiresLocal}
						required
					/>
				</label>

				<button type="submit" data-testid="device-submit" disabled={!canSubmit}>
					Authorize
				</button>
			</form>
		{/if}
	</section>
{/if}

<style>
	section {
		margin: 1.5rem 0;
	}
	form {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		max-width: 28rem;
	}
	label {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}
	.warn {
		padding: 0.5rem 1rem;
		border: 1px solid #b54708;
		background: #fffaeb;
		color: #7a2e0e;
	}
</style>
