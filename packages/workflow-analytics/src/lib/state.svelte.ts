import { ApiError } from './api';

/** The one visible fetch error, shown by the layout's error panel. */
export const fetchError = $state<{ message: string; status: number; network: boolean }>({
	message: '',
	status: 0,
	network: false
});

export function setError(e: unknown) {
	if (e instanceof ApiError) {
		fetchError.message = e.message;
		fetchError.status = e.status;
		fetchError.network = false;
	} else {
		fetchError.message = e instanceof Error ? e.message : String(e);
		fetchError.status = 0;
		fetchError.network = true;
	}
}

export function clearError() {
	fetchError.message = '';
	fetchError.status = 0;
	fetchError.network = false;
}
