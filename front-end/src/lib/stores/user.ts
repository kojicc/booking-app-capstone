import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export type User = {
	id?: number;
	name?: string;
	email?: string;
	avatar?: string;
	role?: 'admin' | 'user' | string;
};

// Initialize from localStorage if available
function createUserStore() {
	let initialUser: User | null = null;

	if (browser) {
		try {
			const stored = localStorage.getItem('user');
			if (stored) {
				initialUser = JSON.parse(stored);
			}
		} catch (e) {
			console.warn('Failed to parse user from localStorage:', e);
		}
	}

	const { subscribe, set, update } = writable<User | null>(initialUser);

	return {
		subscribe,
		set: (u: User | null) => {
			set(u);
			if (browser) {
				if (u) {
					localStorage.setItem('user', JSON.stringify(u));
				} else {
					localStorage.removeItem('user');
				}
			}
		},
		update,
		clear: () => {
			set(null);
			if (browser) {
				localStorage.removeItem('user');
			}
		}
	};
}

export const user = createUserStore();

export function setUser(u: User | null) {
	user.set(u);
}

export function clearUser() {
	user.clear();
}
