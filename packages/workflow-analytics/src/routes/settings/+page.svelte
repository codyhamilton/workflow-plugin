<script lang="ts">
	import { BASE_KEY, TOKEN_KEY } from '$lib/api';

	function read(k: string): string {
		try {
			return localStorage.getItem(k) ?? '';
		} catch {
			return '';
		}
	}

	let base = $state(read(BASE_KEY));
	let key = $state(read(TOKEN_KEY));
	let status = $state('');

	function save(e: Event) {
		e.preventDefault();
		try {
			localStorage.setItem(BASE_KEY, base.trim());
			localStorage.setItem(TOKEN_KEY, key.trim());
			status = 'Saved.';
		} catch {
			status = 'Could not write to localStorage in this browser.';
		}
	}
</script>

<h1>Connection</h1>
<p>
	An empty base URL means this site's own origin (<code>/v1</code>). The token is kept in this browser's
	<code>localStorage</code> for this origin and is sent only as an <code>Authorization: Bearer</code> header.
</p>
<form onsubmit={save}>
	<label>
		API base URL
		<input data-testid="settings-base" bind:value={base} placeholder="https://example.com" autocomplete="off" />
	</label>
	<label>
		Bearer token
		<input data-testid="settings-key" type="password" bind:value={key} autocomplete="off" />
	</label>
	<button type="submit" data-testid="settings-save">Save</button>
	<span role="status" data-testid="settings-status">{status}</span>
</form>

<style>
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
	button {
		align-self: flex-start;
	}
</style>
