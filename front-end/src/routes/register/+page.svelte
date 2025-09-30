<script lang="ts">
	import RegisterForm from "$lib/components/register-form.svelte";
	import { Check } from "lucide-svelte";
</script>

<main class="w-screen min-h-screen flex items-center justify-center">
    <section class="flex w-full min-h-screen flex-col sm:flex-row">
        <aside class="hidden sm:flex sm:flex-col sm:items-center sm:justify-center sm:flex-1 bg-gray-50 px-12 py-10">
            <article class="w-full max-w-md mx-auto">
                <img src="/src/lib/assets/bhive.png" alt="bhive logo" class="w-24 h-14 mb-6" />
                <h1 class="text-4xl font-light mb-2 text-gray-800">B-Hive: Buri's Great Hall</h1>
                <p class="mb-6 text-gray-600">A simple and secure platform to manage reservations for events, meetings, and activities. Designed to make booking effortless for members.</p>
                <ul class="space-y-3 mb-8">
                    <li class="flex items-center gap-2 text-gray-700"><Check class="text-primary-400 w-5 h-5" /> Reserve spaces quickly and easily</li>
                    <li class="flex items-center gap-2 text-gray-700"><Check class="text-primary-400 w-5 h-5" /> Manage bookings with approval flows</li>
                    <li class="flex items-center gap-2 text-gray-700"><Check class="text-primary-400 w-5 h-5" /> Book add-ons for a better experience</li>
                </ul>
                <footer class="pt-8 text-base text-gray-400 border-t">B-Hive — From Buri to Raya to Adarna, one hall for all.</footer>
            </article>
        </aside>

        <section class="flex flex-col justify-center flex-1 bg-white px-8 py-10">
            <article class="w-full max-w-sm mx-auto">
                <!-- Mobile-only logo: visible below sm (hidden on sm and up) -->
                <img src="/src/lib/assets/bhive.png" alt="bhive logo" class="block sm:hidden w-24 h-14 mx-auto mb-6" />
                <RegisterForm />
            </article>
        </section>
    </section>
</main>
