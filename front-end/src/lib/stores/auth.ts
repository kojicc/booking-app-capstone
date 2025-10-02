import { user, setUser, clearUser, type User } from './user';
import {
	login as apiLogin,
	logout as apiLogout,
	setAccessToken,
	refreshAccessToken
} from '$lib/api';

export { user }; // Re-export for convenience

export async function login(email: string, password: string) {
	try {
		const response = await apiLogin(email, password);

		// The response contains: { message, tokens: { access, refresh }, user: { id, email, username, role } }
		if (response.user) {
			// Map the backend user to your User type
			const userData: User = {
				id: response.user.id,
				email: response.user.email,
				name: response.user.username || response.user.email, // fallback to email if no username
				role: response.user.role
				// avatar not provided by backend, so it stays undefined
			};
			setUser(userData);
		}

		return response;
	} catch (error) {
		clearUser();
		throw error;
	}
}

export async function logout() {
	try {
		await apiLogout();
	} catch (error) {
		console.error('Logout failed:', error);
	} finally {
		clearUser();
	}
}

export async function getCurrentUser() {
	try {
		const { apiFetch } = await import('$lib/api');
		const response = await apiFetch('/api/users/me/', { method: 'GET' });

		if (response) {
			const userData: User = {
				id: response.id,
				email: response.email,
				name: response.username || response.first_name || response.email,
				role: response.role
			};
			setUser(userData);
			return userData;
		}
		return null;
	} catch (error) {
		console.error('Failed to get current user:', error);
		return null;
	}
}

export async function checkAuth() {
	try {
		// Try to refresh the token on app load
		await refreshAccessToken();

		// If refresh succeeds, try to get user data
		// First check if we have user in localStorage
		const currentUser = await getCurrentUser();

		return !!currentUser;
	} catch (error) {
		clearUser();
		return false;
	}
}
