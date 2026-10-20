<script lang="ts">
	import { page } from '$app/state';
	import InvestigationShell from '$lib/investigation/InvestigationShell.svelte';
	import LandingView from '$lib/investigation/LandingView.svelte';
	import { isInvestigationQuery } from '$lib/investigation/request-url';

	const investigation = $derived(isInvestigationQuery(page.url.searchParams));
</script>

{#if investigation}
	<InvestigationShell />
{:else}
	<LandingView />
{/if}
