import { user, setUser, clearUser, type User } from './user';
import { login as apiLogin, logout as apiLogout, setAccessToken, refreshAccessToken } from '$lib/api';

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
        role: response.user.role,
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

export async function checkAuth() {
  try {
    // Try to refresh the token on app load
    await refreshAccessToken();
    // If refresh succeeds, we're authenticated but we don't have user data yet
    // You might want to add a /api/users/me/ endpoint to fetch current user
    // For now, we know the token is valid
    return true;
  } catch (error) {
    clearUser();
    return false;
  }
}