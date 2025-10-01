<script lang="ts">
  import { user } from '$lib/stores/auth';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';

  interface Props {
    requiredRole?: 'admin' | 'user';
    redirectTo?: string;
    children?: import('svelte').Snippet;
  }

  let { requiredRole, redirectTo = '/login-01', children }: Props = $props();

  let isAuthorized = $state(false);
  let isChecking = $state(true);

  onMount(() => {
    const checkAuth = () => {
      isChecking = true;
      
      // Check if user is logged in
      if (!$user) {
        isAuthorized = false;
        isChecking = false;
        goto(redirectTo);
        return;
      }

      // Check role requirement
      if (requiredRole) {
        if ($user.role !== requiredRole) {
          isAuthorized = false;
          isChecking = false;
          
          // Redirect based on user role
          if ($user.role === 'admin') {
            goto('/dashboard'); // Admin goes to dashboard
          } else {
            goto('/reservations'); // Regular user goes to their reservations
          }
          return;
        }
      }

      isAuthorized = true;
      isChecking = false;
    };

    // Initial check
    checkAuth();

    // Subscribe to user changes
    const unsubscribe = user.subscribe(() => {
      checkAuth();
    });

    return () => {
      unsubscribe();
    };
  });
</script>

{#if isChecking}
  <div class="flex items-center justify-center min-h-[200px]">
    <div class="text-center">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
      <p class="text-sm text-muted-foreground">Checking permissions...</p>
    </div>
  </div>
{:else if isAuthorized}
  {@render children?.()}
{:else}
  <div class="flex items-center justify-center min-h-[200px]">
    <div class="text-center">
      <h2 class="text-xl font-semibold mb-2">Access Denied</h2>
      <p class="text-sm text-muted-foreground">You don't have permission to access this page.</p>
    </div>
  </div>
{/if}