import { writable } from 'svelte/store';

export type User = {
  id?: number;
  name?: string;
  email?: string;
  avatar?: string;
  role?: 'admin' | 'user' | string;
};

export const user = writable<User | null>(null);

export function setUser(u: User | null) {
  user.set(u);
  console.log('User set to:', u);
}

export function clearUser() {
  user.set(null);
}
