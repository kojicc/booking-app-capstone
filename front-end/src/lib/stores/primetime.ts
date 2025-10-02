import { writable } from 'svelte/store';

// Signal to open the primetime management dialog. Set to true to request opening.
export const primetimeDialogOpen = writable(false);

// Helper to open the dialog
export function openPrimetimeDialog() {
	primetimeDialogOpen.set(true);
}

// Helper to reset (not strictly necessary but convenient)
export function resetPrimetimeDialog() {
	primetimeDialogOpen.set(false);
}
