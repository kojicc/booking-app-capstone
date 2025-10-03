<script lang="ts">
	import { onMount } from 'svelte';
  import ReservationDetailCard from "$lib/components/ReservationDetailCard.svelte";
  import { getReservations, deleteReservation, updateReservation } from '$lib/api/reservation';
  import { reservations } from '$lib/stores/reservation';
  import { user } from '$lib/stores/user';
  import type { Reservation } from '$lib/api/reservation';
	import { toast } from 'svelte-sonner';
	import { goto } from '$app/navigation';
	import { clearOpenSignal } from '$lib/stores/reservation';
  import * as AlertDialog from "$lib/components/ui/alert-dialog";
  import * as Dialog from "$lib/components/ui/dialog";
  import * as Table from "$lib/components/ui/table";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { MoreHorizontal, Edit, Trash2 } from 'lucide-svelte';

		let { openReservationId = null }: { openReservationId?: number | null } = $props();

		let loading = $state(false);
		let handledOpenId = $state<number | null>(null);
  let error = $state<string | null>(null);
  
  // Dialog state
  let showCancelDialogOpen = $state(false);
  let reservationToCancel = $state<Reservation | null>(null);
  
  let showEditDialogOpen = $state(false);
  let reservationToEdit = $state<Reservation | null>(null);
  
  // Edit form state
  let editBookingName = $state('');
  let editDate = $state('');
  let editStartTime = $state('');
  let editEndTime = $state('');
  let editNotes = $state('');
  
  // Table functionality
  let searchTerm = $state('');
  let sortColumn = $state<'id' | 'type' | 'date' | 'status' | null>(null);
  let sortDirection = $state<'asc' | 'desc'>('asc');
  let currentPage = $state(0);
  let pageSize = $state(10);
  
  // Column visibility
  let visibleColumns = $state({
    id: true,
    type: true,
    date: true,
    time: true,
    status: true,
    notes: true,
    rejection: true,
    actions: true
  });

  async function loadReservations() {
    loading = true;
    error = null;
    try {
      const data = await getReservations();
      // Filter to only show current user's reservations
      const userReservations = data.filter(r => {
        if (typeof r.user === 'object' && r.user && 'email' in r.user) {
          return r.user.email === $user?.email;
        }
        return r.user === $user?.email;
      });
      reservations.set(userReservations);
    } catch (e: any) {
      error = e?.message || 'Failed to load reservations';
      if (error) toast.error(error);
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    loading = true; // Start with loading state
    loadReservations();
  });

$effect(() => {
	// If an openReservationId was supplied via URL param, try to open the edit dialog
	if (openReservationId && $reservations.length > 0 && handledOpenId !== openReservationId) {
		const match = $reservations.find(r => r.id === openReservationId);
		if (match) {
			// Open edit dialog for this reservation
			showEditDialog(match);
			handledOpenId = openReservationId;
					// Remove the query param from the URL so re-navigation doesn't re-open it
					try {
						const url = new URL(window.location.href);
						url.searchParams.delete('open');
						// Use SvelteKit's goto with replaceState so $page updates
						goto(url.pathname + url.search + url.hash, { replaceState: true });
					} catch (e) {
						// ignore
					}
		}
	}
});

$effect(() => {
	if ($clearOpenSignal) {
		if (showEditDialogOpen) closeEditDialog();
		if (showCancelDialogOpen) closeCancelDialog();
		handledOpenId = null;
	}
});

  function showCancelDialog(reservation: Reservation) {
    reservationToCancel = reservation;
    showCancelDialogOpen = true;
  }

  async function confirmCancel() {
    if (!reservationToCancel) return;
    
    try {
      await deleteReservation(reservationToCancel.id);
      toast.success(`Reservation #${reservationToCancel.id} cancelled successfully`);
      showCancelDialogOpen = false;
      reservationToCancel = null;
      await loadReservations();
    } catch (e: any) {
      const errorMsg = e?.message || 'Failed to cancel reservation';
      toast.error(errorMsg);
    }
  }

  function showEditDialog(reservation: Reservation) {
    reservationToEdit = reservation;
    editBookingName = reservation.booking_name || reservation.reservation_type_display || reservation.reservation_type;
    const dateValue = reservation.date;
    editDate = dateValue instanceof Date ? dateValue.toISOString().split('T')[0] : String(dateValue);
    editStartTime = reservation.start_time;
    editEndTime = reservation.end_time;
    editNotes = reservation.notes || '';
    showEditDialogOpen = true;
  }

  async function saveEdit() {
    if (!reservationToEdit) return;
    
    try {
      await updateReservation(reservationToEdit.id, {
        booking_name: editBookingName,
        date: editDate,
        start_time: editStartTime,
        end_time: editEndTime,
        notes: editNotes
      });
      toast.success(`Reservation #${reservationToEdit.id} updated successfully`);
      closeEditDialog();
      await loadReservations();
    } catch (e: any) {
      const errorMsg = e?.message || 'Failed to update reservation';
      toast.error(errorMsg);
    }
  }

  function closeCancelDialog() {
    showCancelDialogOpen = false;
    reservationToCancel = null;
  }

  function closeEditDialog() {
    showEditDialogOpen = false;
    reservationToEdit = null;
  }

  // Get user's reservations only (sorted by updated_at - most recently updated first)
  let userReservations = $derived.by(() => {
    return [...$reservations].sort((a, b) => {
      const dateA = new Date(a.updated_at).getTime();
      const dateB = new Date(b.updated_at).getTime();
      return dateB - dateA; // Most recent first
    });
  });

  // Table sorting and filtering (separate from cards)
  let tableReservations = $derived.by(() => {
    let filtered = userReservations;
    
    // Apply search
    if (searchTerm) {
      filtered = filtered.filter(r =>
        r.id.toString().includes(searchTerm) ||
        (r.booking_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (r.reservation_type_display || r.reservation_type).toLowerCase().includes(searchTerm.toLowerCase()) ||
        (r.status_display || r.status || '').toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    // Apply sort
    if (sortColumn) {
      const sorted = [...filtered].sort((a, b) => {
        let aVal: any;
        let bVal: any;
        
        switch (sortColumn) {
          case 'id':
            aVal = a.id;
            bVal = b.id;
            break;
          case 'type':
            aVal = a.reservation_type_display || a.reservation_type;
            bVal = b.reservation_type_display || b.reservation_type;
            break;
          case 'date':
            aVal = new Date(a.date).getTime();
            bVal = new Date(b.date).getTime();
            break;
          case 'status':
            aVal = a.status_display || a.status || '';
            bVal = b.status_display || b.status || '';
            break;
          default:
            return 0;
        }
        
        if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
        if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
        return 0;
      });
      return sorted;
    }
    
    // No sort column selected, return filtered (already sorted by date desc from userReservations)
    return filtered;
  });
  
  let totalPages = $derived(Math.ceil(tableReservations.length / pageSize));
  
  let paginatedReservations = $derived(
    tableReservations.slice(currentPage * pageSize, (currentPage + 1) * pageSize)
  );

  function handleSort(column: typeof sortColumn) {
    if (sortColumn === column) {
      sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      sortColumn = column;
      sortDirection = 'asc';
    }
  }

  function nextPage() {
    if (currentPage < totalPages - 1) {
      currentPage++;
    }
  }

  function prevPage() {
    if (currentPage > 0) {
      currentPage--;
    }
  }
</script>

<div class="p-6 max-w-7xl mx-auto">
	<div class="mb-6">
		<h2 class="text-2xl font-bold">My Reservations</h2>
		<p class="text-sm text-gray-600 mt-1">View your confirmed and pending reservations here.</p>
	</div>
	
	{#if loading}
		<div class="flex justify-center py-12">
			<div class="flex flex-col items-center gap-3">
				<div class="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-200-var"></div>
				<p class="text-sm text-gray-500">Loading your reservations...</p>
			</div>
		</div>
	{:else if error}
		<div class="text-red-600 p-4 bg-red-50 rounded-lg">
			{error}
			<button 
				onclick={loadReservations}
				class="ml-2 underline hover:no-underline"
			>
				Try again
			</button>
		</div>
	{:else if userReservations.length === 0}
		<div class="text-gray-500 text-center py-12 bg-gray-50 rounded-lg">
			<p class="text-lg font-medium">No reservations found</p>
			<p class="text-sm mt-2">Create your first reservation to see it here.</p>
		</div>
	{:else}
		<!-- Latest 3 Reservations -->
		<div class="mb-8">
			<h3 class="text-lg font-semibold mb-4">Latest Reservations</h3>
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
				{#each userReservations.slice(0, 3) as reservation}
					<ReservationDetailCard
						bookingName={reservation.booking_name || reservation.reservation_type_display || reservation.reservation_type}
						userWhoBooked={typeof reservation.user === 'object' ? reservation.user.email : reservation.user}
						bookingStatus={reservation.status_display || reservation.status || 'pending'}
						rawStatus={reservation.status || 'PENDING'}
						bookingNumber={reservation.id}
						date={new Date(reservation.date).toLocaleDateString()}
						space={reservation.reservation_type_display || reservation.reservation_type}
						startTime={reservation.start_time}
						endTime={reservation.end_time}
						addons={reservation.notes ? [reservation.notes] : []}
						rejectionMessage={reservation.rejection_reason || ''}
						role="user"
						on:edit={() => showEditDialog(reservation)}
						on:cancel={() => showCancelDialog(reservation)}
					/>
				{/each}
			</div>
		</div>

		<!-- All Reservations Table -->
		<div class="mt-8">
			<h3 class="text-lg font-semibold mb-4">All Reservations</h3>
			
			<div class="space-y-6 bg-white rounded-lg border p-6">
						<!-- Table Controls -->
						<div class="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
							<!-- Search -->
							<div class="flex-1 max-w-sm">
								<Input
									type="text"
									placeholder="Search reservations..."
									bind:value={searchTerm}
									class="w-full"
								/>
							</div>
							
							<!-- Column Visibility -->
							<DropdownMenu.Root>
								<DropdownMenu.Trigger>
									<Button variant="outline">
										Columns ↓
									</Button>
								</DropdownMenu.Trigger>
								<DropdownMenu.Content align="end" class="w-40">
									<DropdownMenu.Label>Toggle columns</DropdownMenu.Label>
									<DropdownMenu.Separator />
									<DropdownMenu.CheckboxItem bind:checked={visibleColumns.id}>
										ID
									</DropdownMenu.CheckboxItem>
									<DropdownMenu.CheckboxItem bind:checked={visibleColumns.type}>
										Type
									</DropdownMenu.CheckboxItem>
									<DropdownMenu.CheckboxItem bind:checked={visibleColumns.date}>
										Date
									</DropdownMenu.CheckboxItem>
									<DropdownMenu.CheckboxItem bind:checked={visibleColumns.time}>
										Time
									</DropdownMenu.CheckboxItem>
									<DropdownMenu.CheckboxItem bind:checked={visibleColumns.status}>
										Status
									</DropdownMenu.CheckboxItem>
                  <DropdownMenu.CheckboxItem bind:checked={visibleColumns.notes}>
                  Notes
                </DropdownMenu.CheckboxItem>
                <DropdownMenu.CheckboxItem bind:checked={visibleColumns.rejection}>
                  Rejection
                </DropdownMenu.CheckboxItem>
									<DropdownMenu.CheckboxItem bind:checked={visibleColumns.actions}>
										Actions
									</DropdownMenu.CheckboxItem>
								</DropdownMenu.Content>
							</DropdownMenu.Root>
						</div>
						
						<!-- Enhanced Table -->
						<div class="rounded-md border overflow-x-auto">
							<Table.Root>
								<Table.Header>
									<Table.Row>
										{#if visibleColumns.id}
											<Table.Head>
												<button class="cursor-pointer hover:text-gray-600" onclick={() => handleSort('id')}>
													ID {sortColumn === 'id' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
												</button>
											</Table.Head>
										{/if}
										{#if visibleColumns.type}
											<Table.Head>
												<button class="cursor-pointer hover:text-gray-600" onclick={() => handleSort('type')}>
													Type {sortColumn === 'type' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
												</button>
											</Table.Head>
										{/if}
										{#if visibleColumns.date}
											<Table.Head>
												<button class="cursor-pointer hover:text-gray-600" onclick={() => handleSort('date')}>
													Date {sortColumn === 'date' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
												</button>
											</Table.Head>
										{/if}
										{#if visibleColumns.time}
											<Table.Head>Time</Table.Head>
										{/if}
										{#if visibleColumns.status}
											<Table.Head>
												<button class="cursor-pointer hover:text-gray-600" onclick={() => handleSort('status')}>
													Status {sortColumn === 'status' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
												</button>
											</Table.Head>
										{/if}
                    {#if visibleColumns.notes}
                      <Table.Head>Notes</Table.Head>
                    {/if}
                    {#if visibleColumns.rejection}
                      <Table.Head>Rejection Reason</Table.Head>
                    {/if}
										{#if visibleColumns.actions}
											<Table.Head class="text-right">Actions</Table.Head>
										{/if}
									</Table.Row>
								</Table.Header>
								<Table.Body>
									{#each paginatedReservations as reservation}
										<Table.Row>
											{#if visibleColumns.id}
												<Table.Cell class="font-medium">{reservation.id}</Table.Cell>
											{/if}
											{#if visibleColumns.type}
												<Table.Cell>{reservation.reservation_type_display || reservation.reservation_type}</Table.Cell>
											{/if}
											{#if visibleColumns.date}
												<Table.Cell>{new Date(reservation.date).toLocaleDateString()}</Table.Cell>
											{/if}
											{#if visibleColumns.time}
												<Table.Cell>{reservation.start_time} - {reservation.end_time}</Table.Cell>
											{/if}
											{#if visibleColumns.status}
												<Table.Cell>
													<span class="inline-flex px-2 py-1 text-xs rounded-full {reservation.status === 'CONFIRMED' ? 'bg-green-100 text-green-800' : reservation.status === 'PENDING' ? 'bg-yellow-100 text-yellow-800' : reservation.status === 'REJECTED' || reservation.status === 'CANCELLED' ? 'bg-red-100 text-red-800' : reservation.status === 'COMPLETED' ? 'bg-gray-100 text-gray-800' : 'bg-gray-100 text-gray-800'}" 
													>
														{reservation.status_display || reservation.status}
													</span>
												</Table.Cell>
											{/if}
											{#if visibleColumns.notes}
                  <Table.Cell class="max-w-[240px] break-words">{reservation.notes ? reservation.notes : '—'}</Table.Cell>
                {/if}
                {#if visibleColumns.rejection}
                  <Table.Cell class="max-w-[240px] break-words">{reservation.rejection_reason ? reservation.rejection_reason : '—'}</Table.Cell>
                {/if}
											{#if visibleColumns.actions}
												<Table.Cell class="text-right">
													{#if reservation.status !== 'CANCELLED' && reservation.status !== 'COMPLETED' && reservation.status !== 'REJECTED'}
														<DropdownMenu.Root>
															<DropdownMenu.Trigger>
																<Button variant="ghost" size="sm" class="h-8 px-2 py-1">
																	<MoreHorizontal class="h-4 w-4 mr-1" />
																	<span class="text-xs">Options</span>
																</Button>
															</DropdownMenu.Trigger>
															<DropdownMenu.Content align="end" class="w-40">
																<DropdownMenu.Label>Actions</DropdownMenu.Label>
																<DropdownMenu.Separator />
																<DropdownMenu.Item onclick={() => showEditDialog(reservation)}>
																	<Edit class="mr-2 h-4 w-4" />
																	Edit
																</DropdownMenu.Item>
																<DropdownMenu.Item onclick={() => showCancelDialog(reservation)} class="text-red-600">
																	<Trash2 class="mr-2 h-4 w-4" />
																	Cancel
																</DropdownMenu.Item>
															</DropdownMenu.Content>
														</DropdownMenu.Root>
													{:else}
														<span class="text-gray-400 text-xs">No actions</span>
													{/if}
												</Table.Cell>
											{/if}
										</Table.Row>
									{/each}
								</Table.Body>
							</Table.Root>
						</div>
						
						<!-- Pagination -->
						<div class="flex items-center justify-between py-4">
							<div class="text-sm text-muted-foreground">
								Showing {currentPage * pageSize + 1} to {Math.min((currentPage + 1) * pageSize, tableReservations.length)} of {tableReservations.length} results
							</div>
							<div class="flex items-center space-x-2">
								<Button variant="outline" size="sm" disabled={currentPage === 0} onclick={prevPage}>
									Previous
								</Button>
								<div class="text-sm font-medium">
									Page {currentPage + 1} of {totalPages}
								</div>
								<Button variant="outline" size="sm" disabled={currentPage >= totalPages - 1} onclick={nextPage}>
									Next
								</Button>
							</div>
						</div>
					</div>
		</div>
	{/if}
</div>

<!-- Cancel Confirmation Dialog -->
<AlertDialog.Root bind:open={showCancelDialogOpen}>
	<AlertDialog.Content>
		<AlertDialog.Header>
			<AlertDialog.Title>Cancel Reservation</AlertDialog.Title>
			<AlertDialog.Description>
				Are you sure you want to cancel this reservation? This action cannot be undone.
				{#if reservationToCancel}
					<div class="mt-3 p-3 bg-gray-50 rounded">
						<strong>Reservation #{reservationToCancel.id}</strong><br>
						{reservationToCancel.reservation_type_display || reservationToCancel.reservation_type}<br>
						{new Date(reservationToCancel.date).toLocaleDateString()} • {reservationToCancel.start_time} - {reservationToCancel.end_time}
					</div>
				{/if}
			</AlertDialog.Description>
		</AlertDialog.Header>
		<AlertDialog.Footer>
			<AlertDialog.Cancel onclick={closeCancelDialog}>No, keep it</AlertDialog.Cancel>
			<AlertDialog.Action onclick={confirmCancel} class="bg-red-600 hover:bg-red-700">
				Yes, cancel reservation
			</AlertDialog.Action>
		</AlertDialog.Footer>
	</AlertDialog.Content>
</AlertDialog.Root>

<!-- Edit Reservation Dialog -->
<Dialog.Root bind:open={showEditDialogOpen}>
	<Dialog.Content class="max-w-md">
		<Dialog.Header>
			<Dialog.Title>Edit Reservation</Dialog.Title>
			<Dialog.Description>
				Update your reservation details below.
			</Dialog.Description>
		</Dialog.Header>
		
		<div class="space-y-4 py-4">
			<div>
				<label for="edit-booking-name" class="block text-sm font-medium mb-1">Booking Name</label>
				<Input id="edit-booking-name" type="text" bind:value={editBookingName} placeholder="e.g., Team Meeting, Workshop" />
			</div>
			<div>
				<label for="edit-date" class="block text-sm font-medium mb-1">Date</label>
				<Input id="edit-date" type="date" bind:value={editDate} />
			</div>
			<div class="grid grid-cols-2 gap-4">
				<div>
					<label for="edit-start" class="block text-sm font-medium mb-1">Start Time</label>
					<Input id="edit-start" type="time" bind:value={editStartTime} />
				</div>
				<div>
					<label for="edit-end" class="block text-sm font-medium mb-1">End Time</label>
					<Input id="edit-end" type="time" bind:value={editEndTime} />
				</div>
			</div>
			<div>
				<label for="edit-notes" class="block text-sm font-medium mb-1">Notes (optional)</label>
				<Input id="edit-notes" type="text" bind:value={editNotes} placeholder="Any special requests..." />
			</div>
		</div>
		
		<Dialog.Footer>
			<Button variant="outline" onclick={closeEditDialog}>Cancel</Button>
			<Button onclick={saveEdit}>Save Changes</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>
