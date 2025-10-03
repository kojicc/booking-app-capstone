import { writable } from 'svelte/store';
import type { Reservation } from '$lib/api/reservation';

export const reservations = writable<Reservation[]>([]);

export const showReservationModal = writable(false);

export const showSuccessModal = writable(false);

export const showAwaitingModal = writable(false);

// Signal to instruct reservation-list children to clear any 'open' state that may persist
export const clearOpenSignal = writable(0);

// Signal to force calendar cache invalidation
export const invalidateCalendarCache = writable(0);

// Helper to reset all modal states and trigger cache invalidation
export function resetAllModals() {
	showReservationModal.set(false);
	showSuccessModal.set(false);
	showAwaitingModal.set(false);
	clearOpenSignal.update((n) => n + 1);
	// Invalidate calendar cache to ensure it shows latest data after modal operations
	invalidateCalendarCache.update((n) => n + 1);
}
