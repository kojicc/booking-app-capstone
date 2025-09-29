// Minimal API client for the frontend to talk to a backend.
// Uses Vite env var VITE_API_BASE (e.g. https://api.example.com) as the base URL.
// This file is small and intentionally framework-agnostic so it can be reused
// from Svelte components or SvelteKit load functions.

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
  // Prefer VITE_API_BASE for client-side access. If you prefer SvelteKit's $env,
  // swap this to use $env/static/public or $env/dynamic/public accordingly.
  // Vite exposes env vars prefixed with VITE_ to client-side code via import.meta.env.
  // Example .env: VITE_API_BASE=https://api.example.com
  // If undefined, caller should fallback to mocked behaviour.
  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  // @ts-ignore - import.meta.env typing varies by setup
  return (import.meta.env && import.meta.env.VITE_API_BASE) || undefined;
}

async function apiFetch(endpoint: string, options: RequestInit = {}) {
  const base = getBaseUrl();
  if (!base) throw new Error('VITE_API_BASE is not set. Set it in your environment to enable API calls.');

  const url = base.replace(/\/$/, '') + '/' + endpoint.replace(/^\//, '');

  const headers = new Headers(options.headers || {});
  if (options.body && !(options.body instanceof FormData)) {
    headers.set('content-type', 'application/json');
  }

  const res = await fetch(url, { ...options, headers });

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

export async function postBooking(payload: BookingPayload) {
  return apiFetch('/bookings', { method: 'POST', body: JSON.stringify(payload) });
}

export async function login(email: string, password: string) {
  return apiFetch('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
}

export default { postBooking, login };
