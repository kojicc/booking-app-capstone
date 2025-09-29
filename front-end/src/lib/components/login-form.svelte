<script lang="ts">
    import { Button } from "$lib/components/ui/button/index.js";
    import * as Card from "$lib/components/ui/card/index.js";
    import { Input } from "$lib/components/ui/input/index.js";
    import { Label } from "$lib/components/ui/label/index.js";
    import { goto } from "$app/navigation";
    import { login as apiLogin } from "$lib/api/index.js";

        let email = "";
        let password = "";
        let passwordError = "";
        let loading = false;

    const handleSubmit = async (event: Event) => {
        event.preventDefault();
        passwordError = "";
        if (password.length < 8) {
            passwordError = "Password must be at least 8 characters.";
            return;
        }
        loading = true;
        try {
            try {
                await apiLogin(email, password);
                //   auth tokens  (localStorage/cookies)
            } catch (err) {
                // If API isn't configured, fallback to mocked login
                console.warn('Login API failed or not configured, falling back to mock.', err);
                await new Promise((resolve) => setTimeout(resolve, 1200));
            }
            goto("/dashboard");
        } finally {
            loading = false;
        }
    };
</script>

<Card.Root class="mx-auto w-full max-w-sm ">
    <Card.Header class="text-center">
        <Card.Title class="text-2xl text-primary-300">Login</Card.Title>
        <Card.Description>Nice to see you again!</Card.Description>
    </Card.Header>
    <Card.Content>
        <form class="grid gap-4" on:submit={handleSubmit} autocomplete="on">
            <div class="grid gap-2">
                <Label for="email">Email</Label>
                <Input id="email" type="email" placeholder="m@example.com" required bind:value={email} />
            </div>
            <div class="grid gap-2">
                <div class="flex items-center">
                    <Label for="password">Password</Label>
                    <a href="#" class="ml-auto inline-block text-sm underline">
                        Forgot your password?
                    </a>
                </div>
                <Input id="password" type="password" required bind:value={password} />
                    {#if passwordError}
                        <span class="text-red-500 text-xs">{passwordError}</span>
                    {/if}
            </div>
            <Button type="submit" variant="custom" class="w-full" disabled={loading}>
                {#if loading}
                    <svg class="animate-spin h-4 w-4 mr-2 inline-block align-middle" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path></svg>
                    Loading...
                {:else}
                    Login
                {/if}
            </Button>
            <Button variant="outline" class="w-full" type="button">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                    <path
                        d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"
                        fill="currentColor"
                    />
                </svg>
                Login with Google
            </Button>
            <div class="mt-4 text-center text-sm">
                Don't have an account?
                <a href="#" class="underline"> Sign up </a>
            </div>
        </form>
    </Card.Content>
</Card.Root>