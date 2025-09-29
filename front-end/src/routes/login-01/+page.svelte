<script lang="ts">
	import LoginForm from "$lib/components/login-form.svelte";
</script>


<div class="min-h-screen flex flex-col items-center justify-center bg-primary-gradient">
	<div class="flex flex-col items-center mb-4">
		<img src="/src/lib/assets/bhive2.png" alt="bhive logo" class="h-20" />
	</div>
	<div class="w-full max-w-sm">
		<LoginForm />
	</div>
</div>
