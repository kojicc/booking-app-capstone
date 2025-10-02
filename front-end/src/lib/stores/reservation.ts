import { writable } from 'svelte/store';
import type { Reservation } from '$lib/api/reservation';

export const reservations = writable<Reservation[]>([]);

export const showReservationModal = writable(false);

export const showSuccessModal = writable(false);

export const showAwaitingModal = writable(false);
