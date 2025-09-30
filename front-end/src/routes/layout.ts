// src/routes/+layout.ts
import { checkAuth } from '$lib/stores/auth';
import { browser } from '$app/environment';

export async function load() {
  if (browser) {
    // Try to refresh token on app load
    await checkAuth();
  }
  return {};
}