<script lang="ts">
    import { Button } from "$lib/components/ui/button/index.js";
    import * as Card from "$lib/components/ui/card/index.js";
    import { Input } from "$lib/components/ui/input/index.js";
    import { Label } from "$lib/components/ui/label/index.js";
    import { goto } from "$app/navigation";
    import { register as apiRegister } from "$lib/api/index.js";
    import { toast } from 'svelte-sonner';

        let name: string = "";
        let email: string = "";
        let password: string = "";
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
            await apiRegister({ email, password });
            toast.success('Account created — please sign in');
            goto('/login-01');
        } catch (err: any) {
            const msg = (err && err.message) ? String(err.message) : '';
                let display = 'Registration failed. Please try again.';
                try {
                    if (err && typeof err === 'object') {
                        if (err.body) {
                            try {
                                const parsed = JSON.parse(err.body);
                                if (parsed.detail) display = String(parsed.detail);
                                else if (typeof parsed === 'object') {
                                    const firstKey = Object.keys(parsed)[0];
                                    const val = (parsed as any)[firstKey];
                                    if (Array.isArray(val)) display = String(val[0]);
                                    else display = String(val);
                                }
                            } catch (e) {
                                display = String(err.body);
                            }
                        } else if (err.message) {
                            display = String(err.message);
                        }
                    }
                } catch (e) {
                    console.error('Error parsing registration error:', e);
                    console.log('Original error:', err);
                }

                toast.error(display);
        } finally {
            loading = false;
        }
    };
</script>

<Card.Root class="mx-auto w-full max-w-sm ">
    <Card.Header class="text-center">
        <Card.Title class="text-2xl text-primary-300">Register</Card.Title>
        <Card.Description>Welcome to B-Hive!</Card.Description>
    </Card.Header>
    <Card.Content>
    <form class="grid gap-4" onsubmit={handleSubmit} autocomplete="on">
            <!-- <div class="grid gap-2">
                <Label for="name">Name</Label>
                <Input id="name" type="text" placeholder="John Doe" required bind:value={name} />
            </div> -->
            <div class="grid gap-2">
                <Label for="email">Email</Label>
                <Input id="email" type="email" placeholder="m@example.com" required bind:value={email} />
            </div>
            <div class="grid gap-2">
                <div class="flex items-center">
                    <Label for="password">Password</Label>
                </div>
                <Input id="password" type="password" required bind:value={password} />
                    {#if passwordError}
                        <span class="text-red-500 text-xs">{passwordError}</span>
                    {/if}
            </div>
            <!--<Button type="submit" class="w-full bg-primary-400 hover:bg-primary-500" disabled={loading}>-->
            <Button type="submit" variant="default" disabled={loading}>
                {#if loading}
                    <svg class="animate-spin h-4 w-4 mr-2 inline-block align-middle" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path></svg>
                    Loading...
                {:else}
                    Register
                {/if}
            </Button>
            <!-- <Button variant="outline" class="w-full" type="button">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                    <path
                        d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"
                        fill="currentColor"
                    />
                </svg>
                Login with Google
            </Button> -->
            <div class="mt-4 text-center text-sm">
               Have an account?
                <a href="/login-01" class="underline" onclick={(e) => { e.preventDefault(); goto('/login-01'); }}> Sign in </a>
            </div>
        </form>
    </Card.Content>
</Card.Root>