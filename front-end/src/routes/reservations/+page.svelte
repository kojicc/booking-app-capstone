
<script lang="ts">
	import AppSidebar from "$lib/components/app-sidebar.svelte";
	import * as Breadcrumb from "$lib/components/ui/breadcrumb/index.js";
	import { Separator } from "$lib/components/ui/separator/index.js";
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import { page } from "$app/stores";
	import Plus from "@lucide/svelte/icons/plus";
	import ReservationDetailCard from "$lib/components/ReservationDetailCard.svelte";
	import { user } from '$lib/stores/user';
	import AdminReservations from '$lib/components/reservations-admin.svelte';
	import UserReservations from '$lib/components/reservations-user.svelte';
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

// Svelte auto-subscription: use $user in template

$effect(() => {
	pageLabel = (pathToLabel as Record<string, string>)[$page.url.pathname] ?? 'Reservations';
});

// Tester or sample content for reservation card

const sampleReservation = {
    bookingName: 'Birthday ni Anne', 
    userWhoBooked: 'Vice Ganda', 
    bookingStatus: 'rejected', 
    bookingNumber: 'CLD09738PL', 
    date: 'October 5, 2025', 
    space: 'Recording Room', 
    startTime: '13:00', 
    endTime: '15:00', 
    addons: ['Water', 'Internet'],
    rejectionMessage: 'Please select another date'
  };

</script>

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
						</div>
					</div>
					<button class="bg-primary-200-var hover:bg-primary-300-var text-white font-medium rounded-lg px-4 py-2 flex items-center gap-2 text-sm shadow transition-colors">
						<Plus  class="h-4 w-4" />
						New Reservation
					</button>
				</header>
				<div class="flex flex-1 flex-col gap-4 p-4 pt-0">
					<!-- Main content here -->
					<!-- Tester reservation card -->
					 <ReservationDetailCard {...sampleReservation}/>
					{#if $user?.role === 'admin'}
						<AdminReservations />
					{:else}
						<UserReservations />
					{/if}
				</div>
	</Sidebar.Inset>
</Sidebar.Provider>
