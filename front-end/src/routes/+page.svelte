<script>
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  
  // Redirect to landing page
  onMount(() => {
    goto('/landing');
  });
</script>
