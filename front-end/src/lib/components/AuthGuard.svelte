<script lang="ts">
  import { user } from '$lib/stores/user';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import * as AlertDialog from "$lib/components/ui/alert-dialog";
  import { Button } from "$lib/components/ui/button";

  interface Props {
    requiredRole?: 'admin' | 'user';
    children?: import('svelte').Snippet;
  }

  let { requiredRole, children }: Props = $props();

  let isAuthorized = $state(false);
  let isChecking = $state(true);
  let showAuthAlert = $state(false);

  onMount(() => {
    const checkAuth = () => {
      isChecking = true;
      
      // Check if user is logged in
      if (!$user) {
        isAuthorized = false;
        isChecking = false;
        showAuthAlert = true;
        return;
      }

      // Check role requirement
      if (requiredRole) {
        if ($user.role !== requiredRole) {
          isAuthorized = false;
          isChecking = false;
          
          // Redirect based on user role
          if ($user.role === 'admin') {
            goto('/dashboard');
          } else {
            goto('/reservations');
          }
          return;
        }
      }

      isAuthorized = true;
      isChecking = false;
      showAuthAlert = false;
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

  function handleGoToLogin() {
    showAuthAlert = false;
    goto('/login-01');
  }
</script>

{#if isChecking}
  <div class="flex items-center justify-center min-h-screen">
    <div class="text-center">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-400 mx-auto mb-4"></div>
      <p class="text-sm text-muted-foreground">Verifying authentication...</p>
    </div>
  </div>
{:else if isAuthorized}
  {@render children?.()}
{:else}
  <AlertDialog.Root open={showAuthAlert}>
    <AlertDialog.Content>
      <AlertDialog.Header>
        <AlertDialog.Title>Authentication Required</AlertDialog.Title>
        <AlertDialog.Description>
          You need to be logged in to access this page. Please log in to continue.
        </AlertDialog.Description>
      </AlertDialog.Header>
      <AlertDialog.Footer>
        <Button onclick={handleGoToLogin}>Go to Login</Button>
      </AlertDialog.Footer>
    </AlertDialog.Content>
  </AlertDialog.Root>
{/if}
