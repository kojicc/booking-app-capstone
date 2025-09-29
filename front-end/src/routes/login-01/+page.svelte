<script lang="ts">
		import LoginForm from "$lib/components/login-form.svelte";
		import { Check } from "lucide-svelte";
</script>

<div class="w-screen h-screen flex items-center justify-center ">
  <div class="flex w-full h-full min-h-screen">
    <!-- Left column -->
    <div class="flex flex-col items-center justify-center flex-1 bg-gray-50 px-12 py-10">
      <div class="w-full max-w-md mx-auto">
        <img src="/src/lib/assets/bhive.png" alt="bhive logo" class="w-24 h-14 mb-6" />
        <h1 class="text-4xl font-light mb-2 text-gray-800">B-Hive: Buri's Great Hall</h1>
        <p class="mb-6 text-gray-600">A simple and secure platform to manage reservations for events, meetings, and activities. Designed to make booking effortless for members.</p>
        <ul class="space-y-3 mb-8">
          <li class="flex items-center gap-2 text-gray-700"><Check class="text-primary-400 w-5 h-5" /> Reserve spaces quickly and easily</li>
          <li class="flex items-center gap-2 text-gray-700"><Check class="text-primary-400 w-5 h-5" /> Manage bookings with approval flows</li>
          <li class="flex items-center gap-2 text-gray-700"><Check class="text-primary-400 w-5 h-5" /> Book add-ons for a better experience</li>
        </ul>
        <div class="pt-8 text-base text-gray-400 border-t">B-Hive — From Buri to Raya to Adarna, one hall for all.</div>
      </div>
    </div>
    <!-- Right column -->
    <div class="flex flex-col justify-center flex-1 bg-white px-8 py-10">
      <div class="w-full max-w-sm mx-auto">
        <LoginForm />
      </div>
    </div>
  </div>
</div>
