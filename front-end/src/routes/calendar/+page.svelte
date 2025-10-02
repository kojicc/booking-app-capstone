<script lang="ts">
	import AppSidebar from "$lib/components/app-sidebar.svelte";
	import AuthGuard from "$lib/components/AuthGuard.svelte";
	import * as Breadcrumb from "$lib/components/ui/breadcrumb/index.js";
	import { Separator } from "$lib/components/ui/separator/index.js";
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import { page } from "$app/stores";
	import Plus from "@lucide/svelte/icons/plus";
	import ReservationModal from "$lib/components/reservation-modal.svelte";
	import SuccessModal from "$lib/components/success-modal.svelte";
	import AwaitingConfirmation from "$lib/components/awaiting-confirmation.svelte";
	import { toast } from 'svelte-sonner';
	// @ts-ignore - Event calendar library has no type definitions
	import {Calendar, TimeGrid} from '@event-calendar/core';
	import { showReservationModal, showAwaitingModal, showSuccessModal } from "$lib/stores/reservation";
	import ReservationsCalendar from './ReservationsCalendar.svelte';

    let options = $state({
		
        view: 'timeGridWeek',
        events: [
            // your list of events
        ]
    });
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
	};

	

	// Concrete page label to satisfy TypeScript when indexing pathToLabel
	let pageLabel = $state('Calendar');

	$effect(() => {
		pageLabel = (pathToLabel as Record<string, string>)[$page.url.pathname] ?? 'Calendar';
	});

function handleModalClose() {
    showReservationModal.set(false);
}

	function handleReservationSuccess(bookedTime?: string | Date | number | null, primetime?: boolean) {
		// ReservationModal calls this via onSuccess after confirm
		showReservationModal.set(false);
		lastBookedTime = bookedTime ?? null;
		
		// Show toast notification
		const message = primetime 
			? '🎉 Primetime reservation created! Waiting for admin approval.' 
			: '✅ Reservation created successfully!';
		toast.success(message, {
			duration: 5000,
			position: 'top-center',
		});
		
		// ensure only the correct modal is shown
		showSuccessModal.set(false);
		showAwaitingModal.set(false);
		if (primetime) {
			showAwaitingModal.set(true);
		} else {
			showSuccessModal.set(true);
		}
	}

	// Keep last booked time for success modal (reactive)
	let lastBookedTime = $state<string | Date | number | null>(null);
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
				</div>
			</div>
			<button class="bg-primary-200-var hover:bg-primary-300-var text-white font-medium rounded-lg px-4 py-2 flex items-center gap-2 text-sm shadow transition-colors" onclick={() => showReservationModal.set(true)}>
				<Plus class="h-4 w-4" />
				New Reservation
			</button>
		</header>



		<!-- <Calendar plugins={[TimeGrid]} {options} /> -->
		<ReservationsCalendar />


		{#if $showReservationModal}
			<ReservationModal open={$showReservationModal} onClose={handleModalClose} onSuccess={handleReservationSuccess} />
		{/if}

		{#if $showSuccessModal}
			<SuccessModal open={$showSuccessModal} onClose={() => $showSuccessModal = false } bookedTime={lastBookedTime} />
		{/if}
		{#if $showAwaitingModal}
			<AwaitingConfirmation open={$showAwaitingModal} onClose={() => $showAwaitingModal = false} bookedTime={lastBookedTime} />
		{/if}
	</Sidebar.Inset>
</Sidebar.Provider>
</AuthGuard>