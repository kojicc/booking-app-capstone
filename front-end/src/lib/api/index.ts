// Minimal API client for the frontend to talk to a backend.
// Uses Vite env var VITE_API_BASE (e.g. https://api.example.com) as the base URL.
// This file is small and intentionally framework-agnostic so it can be reused
// from Svelte components or SvelteKit load functions.

//store the login access token in memory
let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
	accessToken = token;
}

export function getAccessToken() {
	return accessToken;
}

export type BookingPayload = {
	bookingName: string;
	date: string; // ISO date or yyyy-mm-dd string
	space: string;
	startTime: string; // hh:mm
	endTime: string; // hh:mm
	addons?: string[];
	totalHours: number;
	totalCost: number;
};

function getBaseUrl(): string | undefined {
	return (import.meta.env && import.meta.env.VITE_API_BASE) || undefined;
}

export async function apiFetch(endpoint: string, options: RequestInit = {}) {
	const base = getBaseUrl();
	if (!base)
		throw new Error('VITE_API_BASE is not set. Set it in your environment to enable API calls.');

	const url = base.replace(/\/$/, '') + '/' + endpoint.replace(/^\//, '');

	const headers = new Headers(options.headers || {});

	// Add Authorization header if access token exists
	if (accessToken) {
		headers.set('Authorization', `Bearer ${accessToken}`);
	}

	if (options.body && !(options.body instanceof FormData)) {
		headers.set('content-type', 'application/json');
	}

	const res = await fetch(url, { ...options, headers });

	// Handle token expiration
	if (res.status === 401) {
		// Attempt token refresh
		const refreshed = await tryRefreshToken();
		if (refreshed) {
			// Retry the original request with new token
			headers.set('Authorization', `Bearer ${accessToken}`);
			const retryRes = await fetch(url, { ...options, headers });
			if (!retryRes.ok) {
				accessToken = null; // Clear the token as it might be invalid
				const text = await retryRes.text().catch(() => '');
				throw new Error('Authentication failed. Please login again.');
			}
			const ct = retryRes.headers.get('content-type') || '';
			if (ct.includes('application/json')) return retryRes.json();
			return retryRes.text();
		} else {
			// Refresh failed, clear everything
			accessToken = null;
			throw new Error('Session expired. Please login again.');
		}
	}

	if (!res.ok) {
		const text = await res.text().catch(() => '');
		const err: any = new Error(`Request failed: ${res.status} ${res.statusText}`);
		err.status = res.status;
		err.body = text;
		throw err;
	}

	const ct = res.headers.get('content-type') || '';
	if (ct.includes('application/json')) return res.json();
	return res.text();
}

async function tryRefreshToken(): Promise<boolean> {
	try {
		const response = await fetch(getBaseUrl() + 'api/users/refresh/', {
			method: 'POST',
			credentials: 'include' // Important: sends the httpOnly refresh cookie
		});

		if (response.ok) {
			const data = await response.json();
			if (data.access) {
				accessToken = data.access;
				return true;
			} else {
				return false;
			}
		} else {
			const errorText = await response.text().catch(() => 'Unknown error');
			return false;
		}
	} catch (error) {
		return false;
	}
}

export async function postBooking(payload: BookingPayload) {
	return apiFetch('/bookings', { method: 'POST', body: JSON.stringify(payload) });
}

export async function login(email: string, password: string) {
	const response = await apiFetch('/api/users/login/', {
		method: 'POST',
		body: JSON.stringify({ email, password }),
		credentials: 'include'
	});

	// Store the access token
	if (response.tokens?.access) {
		setAccessToken(response.tokens.access);
	}

	return response;
}

export async function logout() {
	try {
		await apiFetch('/api/users/logout/', {
			method: 'POST',
			credentials: 'include'
		});
	} finally {
		setAccessToken(null);
	}
}
export async function register(payload: {
	email: string;
	password: string;
	first_name?: string;
	last_name?: string;
	username?: string;
}) {
	// Registers a new user against the Django endpoint
	return apiFetch('/api/users/register/', {
		method: 'POST',
		body: JSON.stringify(payload),
		credentials: 'include'
	});
}

// Refresh the access token manually
export async function refreshAccessToken() {
	const response = await fetch(getBaseUrl() + 'api/users/refresh/', {
		method: 'POST',
		credentials: 'include'
	});

	if (response.ok) {
		const data = await response.json();
		setAccessToken(data.access);
		return data.access;
	}

	throw new Error('Token refresh failed');
}

//calendar api functions
export async function getCalendar(startDate: string, endDate: string) {
  return apiFetch(
    `/api/reservations/calendar/?start_date=${startDate}&end_date=${endDate}`,
    {
      method: 'GET',
      credentials: 'include'
    }
  );
}

export default { postBooking, login, register, getCalendar };
