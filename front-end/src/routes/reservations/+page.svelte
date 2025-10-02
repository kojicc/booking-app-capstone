<script lang="ts">
	import AppSidebar from "$lib/components/app-sidebar.svelte";
	import AuthGuard from "$lib/components/AuthGuard.svelte";
	import * as Breadcrumb from "$lib/components/ui/breadcrumb/index.js";
	import { Separator } from "$lib/components/ui/separator/index.js";
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import { page } from "$app/stores";
	import Plus from "@lucide/svelte/icons/plus";
	import { Clock } from "lucide-svelte";
	import { user } from '$lib/stores/user';
	import { showReservationModal, showSuccessModal } from '$lib/stores/reservation';
	import ReservationModal from '$lib/components/reservation-modal.svelte';
	import AdminReservations from '$lib/components/reservations-admin.svelte';
	import UserReservations from '$lib/components/reservations-user.svelte';
	import PrimetimeManagement from '$lib/components/primetime-management-dialog.svelte';
	import { openPrimetimeDialog } from '$lib/stores/primetime';
	import { Badge } from "$lib/components/ui/badge/index.js";
	import { Button } from "$lib/components/ui/button/index.js";
	import { getPrimeTimeSettings } from '$lib/api/reservation';
	import { toast } from "svelte-sonner";

	// Map path to label for breadcrumb
	const pathToLabel = {
		"/dashboard": "Dashboard",
		"/calendar": "Calendar",
		"/reservations": "Reservations",
		"/reservations/all": "All Reservations",
		"/reservations/requests": "Reservation Requests",
		"/trade-requests": "Trade Requests",
		"/settings": "Settings",
		"/help": "Get Help",
		"/search": "Search",
	};

let pageLabel = $state('Reservations');
let primetimeRef: any = null;

// Refresh key to force child components to reload
let refreshKey = $state(0);

// Primetime state para sa badge
let todayPrimetime = $state<{start: string, end: string} | null>(null);

// Check kung admin ba yung user
let isAdmin = $derived($user?.role === 'admin');

// Load primetime settings para sa today
async function loadTodayPrimetime() {
	try {
		const settings = await getPrimeTimeSettings();
		const today = new Date().getDay(); // 0 = Sunday, 1 = Monday, etc.
		// Backend uses 0 = Monday, so convert: Sunday=6, Monday=0, Tuesday=1, etc.
		const backendWeekday = today === 0 ? 6 : today - 1;
		
		const todaySetting = settings.find(s => s.weekday === backendWeekday && s.is_active);
		if (todaySetting) {
			todayPrimetime = {
				start: todaySetting.start_time.substring(0, 5),
				end: todaySetting.end_time.substring(0, 5)
			};
		} else {
			todayPrimetime = null;
		}
	} catch (error) {
		console.error('Failed to load primetime:', error);
	}
}

// Load primetime on mount for all users (to show badge)
$effect(() => {
	loadTodayPrimetime();
});

function handleModalClose() {
	showReservationModal.set(false);
}

function handleReservationSuccess(bookedTime?: string|Date|number|null, primetime?: boolean) {
	// Show a success indicator/modal and optionally show primetime info
	showSuccessModal.set(true);
	// Force child components to refresh by incrementing key
	refreshKey++;
	// Reload primetime badge
	loadTodayPrimetime();
}

// Svelte auto-subscription: use $user in template

$effect(() => {
	pageLabel = (pathToLabel as Record<string, string>)[$page.url.pathname] ?? 'Reservations';
});

</script>

<AuthGuard>
<Sidebar.Provider>
	<AppSidebar />
	<Sidebar.Inset>
				<header
					class="group-has-data-[collapsible=icon]/sidebar-wrapper:h-12 flex h-16 shrink-0 items-center justify-between gap-2 transition-[width,height] ease-linear px-4 border-b"
				>
					<div class="flex flex-col justify-center">
						<div class="flex items-center gap-2">
							<Sidebar.Trigger class="-ml-1" />
							<Separator orientation="vertical" class="mr-2 data-[orientation=vertical]:h-4" />
							<Breadcrumb.Root>
								<Breadcrumb.List>
									<Breadcrumb.Item>
										<Breadcrumb.Page class="text-xl font-light">{pageLabel}</Breadcrumb.Page>
									</Breadcrumb.Item>
								</Breadcrumb.List>
							</Breadcrumb.Root>
							{#if todayPrimetime}
								<Badge variant="outline" class="ml-2 bg-yellow-100 text-yellow-800 border-yellow-300">
									<Clock class="h-3 w-3 mr-1" />
									{todayPrimetime.start}-{todayPrimetime.end}
								</Badge>
							{:else}
								<Badge variant="outline" class="ml-2 bg-gray-100 text-gray-600 border-gray-300 text-xs">
									<Clock class="h-3 w-3 mr-1" />
									No primetime
								</Badge>
							{/if}
						</div>
					</div>
					<div class="flex items-center gap-2">
						{#if isAdmin}
							<Button variant="outline" size="sm" class="flex items-center gap-2" onclick={() => openPrimetimeDialog()}>
								<Clock class="h-4 w-4" />
								Manage Primetime
							</Button>
						{/if}
						<button class="bg-primary-200-var hover:bg-primary-300-var text-white font-medium rounded-lg px-4 py-2 flex items-center gap-2 text-sm shadow transition-colors" onclick={() => showReservationModal.set(true)}>
							<Plus  class="h-4 w-4" />
							New Reservation
						</button>
					</div>

				</header>
							{#if $showReservationModal}
			
						<ReservationModal bind:open={$showReservationModal} onClose={handleModalClose} onSuccess={handleReservationSuccess} />
						{/if}

						<!-- Hidden component instance to control primetime dialog programmatically -->
						<div style="display:none">
							<PrimetimeManagement onSuccess={loadTodayPrimetime} />
						</div>
				<div class="flex flex-1 flex-col gap-4 p-4 pt-0">
					<!-- Main content here -->

					{#if $user?.role === 'admin'}
						{#key refreshKey}
							<AdminReservations />
						{/key}
					{:else}
						{#key refreshKey}
							<UserReservations />
						{/key}
					{/if}
				</div>
	</Sidebar.Inset>
</Sidebar.Provider>
</AuthGuard>
