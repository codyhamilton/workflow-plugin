import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
export default {
	preprocess: vitePreprocess(),
	kit: {
		// A pure client SPA: every route is served by the fallback page.
		adapter: adapter({ pages: 'build', assets: 'build', fallback: 'index.html', strict: false })
	}
};
