<script lang="ts">
  import { onMount } from 'svelte';
  import ReservationDetailCard from "$lib/components/ReservationDetailCard.svelte";
  import type { Reservation } from '$lib/api/reservation';
  import { getReservations, approveReservation, rejectReservation } from '$lib/api/reservation';
  import { user } from '$lib/stores/user';
  import { toast } from 'svelte-sonner';
  import * as AlertDialog from "$lib/components/ui/alert-dialog";
  import * as Dialog from "$lib/components/ui/dialog";
  import * as Table from "$lib/components/ui/table";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { MoreHorizontal, CheckCircle, XCircle } from 'lucide-svelte';

  let allReservations = $state<Reservation[]>([]);
  let loading = $state(false);
  let error = $state<string | null>(null);
  
  // Dialog state
  let showRejectDialog = $state(false);
  let reservationToReject = $state<Reservation | null>(null);
  let rejectionReason = $state('');
  
  // Table functionality
  let searchTerm = $state('');
  let sortColumn = $state<'id' | 'user' | 'type' | 'date' | 'status' | null>(null);
  let sortDirection = $state<'asc' | 'desc'>('asc');
  let currentPage = $state(0);
  let pageSize = $state(10);
  let filterStatus = $state('ALL');
  
  // Column visibility
  let visibleColumns = $state({
    id: true,
    user: true,
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
      allReservations = data;
    } catch (e: any) {
      error = e?.message || 'Failed to load reservations';
      if (error) toast.error(error);
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    loading = true;
    loadReservations();
  });

  async function handleApprove(reservation: Reservation) {
    try {
      await approveReservation(reservation.id);
      toast.success(`Reservation #${reservation.id} approved successfully`);
      await loadReservations();
    } catch (e: any) {
      const errorMsg = e?.message || 'Failed to approve reservation';
      toast.error(errorMsg);
    }
  }

  function showRejectConfirmation(reservation: Reservation) {
    reservationToReject = reservation;
    rejectionReason = '';
    showRejectDialog = true;
  }

  async function confirmReject() {
    if (!reservationToReject) return;
    
    if (!rejectionReason.trim()) {
      toast.error('Please provide a reason for rejection');
      return;
    }

    try {
      await rejectReservation(reservationToReject.id, rejectionReason);
      toast.success(`Reservation #${reservationToReject.id} rejected`);
      showRejectDialog = false;
      reservationToReject = null;
      rejectionReason = '';
      await loadReservations();
    } catch (e: any) {
      const errorMsg = e?.message || 'Failed to reject reservation';
      toast.error(errorMsg);
    }
  }

  function closeRejectDialog() {
    showRejectDialog = false;
    reservationToReject = null;
    rejectionReason = '';
  }

  // Base reservations sorted by date (for cards)
  let sortedReservations = $derived.by(() => {
    return [...allReservations].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  });

  // Table reservations with filtering and sorting
  let tableReservations = $derived.by(() => {
    let filtered = sortedReservations;
    
    // Apply status filter
    if (filterStatus !== 'ALL') {
      filtered = filtered.filter(r => r.status === filterStatus);
    }
    
    // Apply search
    if (searchTerm) {
      filtered = filtered.filter(r => {
        const userName = typeof r.user === 'object' ? 
          `${r.user.first_name || ''} ${r.user.last_name || ''} ${r.user.email}`.toLowerCase() : 
          String(r.user).toLowerCase();
        
        return r.id.toString().includes(searchTerm) ||
          userName.includes(searchTerm.toLowerCase()) ||
          (r.reservation_type_display || r.reservation_type).toLowerCase().includes(searchTerm.toLowerCase()) ||
          (r.status_display || r.status || '').toLowerCase().includes(searchTerm.toLowerCase());
      });
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
          case 'user':
            aVal = typeof a.user === 'object' ? a.user.email : a.user;
            bVal = typeof b.user === 'object' ? b.user.email : b.user;
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

  function getUserName(reservation: Reservation): string {
    if (typeof reservation.user === 'object') {
      return `${reservation.user.first_name || ''} ${reservation.user.last_name || ''}`.trim() || reservation.user.email;
    }
    return reservation.user;
  }
</script>

<div class="p-6 max-w-7xl mx-auto">
  <div class="mb-6">
    <h2 class="text-2xl font-bold">Reservation Management</h2>
    <p class="text-sm text-gray-600 mt-1">Review and manage all reservation requests.</p>
  </div>
  
  {#if loading}
    <div class="flex justify-center py-12">
      <div class="flex flex-col items-center gap-3">
        <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-200-var"></div>
        <p class="text-sm text-gray-500">Loading reservations...</p>
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
  {:else if sortedReservations.length === 0}
    <div class="text-gray-500 text-center py-12 bg-gray-50 rounded-lg">
      <p class="text-lg font-medium">No reservations found</p>
      <p class="text-sm mt-2">Reservations will appear here once users make bookings.</p>
    </div>
  {:else}
    <!-- Latest 3 Reservations -->
    <div class="mb-8">
      <h3 class="text-lg font-semibold mb-4">Latest Reservations</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {#each sortedReservations.slice(0, 3) as reservation}
          <ReservationDetailCard
            bookingName={reservation.reservation_type_display || reservation.reservation_type}
            userWhoBooked={getUserName(reservation)}
            bookingStatus={reservation.status_display || reservation.status || 'pending'}
            rawStatus={reservation.status || 'PENDING'}
            bookingNumber={reservation.id}
            date={new Date(reservation.date).toLocaleDateString()}
            space={reservation.reservation_type_display || reservation.reservation_type}
            startTime={reservation.start_time}
            endTime={reservation.end_time}
            addons={reservation.notes ? [reservation.notes] : []}
            rejectionMessage={reservation.rejection_reason || ''}
            role="admin"
            on:confirm={() => handleApprove(reservation)}
            on:reject={() => showRejectConfirmation(reservation)}
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
          
          <div class="flex items-center gap-2">
            <!-- Status Filter -->
            <select 
              bind:value={filterStatus}
              class="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="ALL">All Status</option>
              <option value="PENDING">Pending</option>
              <option value="CONFIRMED">Confirmed</option>
              <option value="REJECTED">Rejected</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
            
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
                <DropdownMenu.CheckboxItem bind:checked={visibleColumns.user}>
                  User
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
                {#if visibleColumns.user}
                  <Table.Head>
                    <button class="cursor-pointer hover:text-gray-600" onclick={() => handleSort('user')}>
                      User {sortColumn === 'user' ? (sortDirection === 'asc' ? '↑' : '↓') : ''}
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
                  <Table.Head>Rejection</Table.Head>
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
                  {#if visibleColumns.user}
                    <Table.Cell class="break-words max-w-[200px]">{getUserName(reservation)}</Table.Cell>
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
                      <span class="inline-flex px-2 py-1 text-xs rounded-full {
                        reservation.status === 'CONFIRMED' ? 'bg-green-100 text-green-800' : 
                        reservation.status === 'PENDING' ? 'bg-yellow-100 text-yellow-800' : 
                        reservation.status === 'REJECTED' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }">
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
                      {#if reservation.status === 'PENDING'}
                        <DropdownMenu.Root>
                          <DropdownMenu.Trigger>
                            <Button variant="ghost" size="sm" class="h-8 px-2 py-1">
                              <MoreHorizontal class="h-4 w-4 mr-1" />
                              <span class="text-xs">Actions</span>
                            </Button>
                          </DropdownMenu.Trigger>
                          <DropdownMenu.Content align="end" class="w-40">
                            <DropdownMenu.Label>Actions</DropdownMenu.Label>
                            <DropdownMenu.Separator />
                            <DropdownMenu.Item onclick={() => handleApprove(reservation)} class="text-green-600">
                              <CheckCircle class="mr-2 h-4 w-4" />
                              Approve
                            </DropdownMenu.Item>
                            <DropdownMenu.Item onclick={() => showRejectConfirmation(reservation)} class="text-red-600">
                              <XCircle class="mr-2 h-4 w-4" />
                              Reject
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

<!-- Rejection Confirmation Dialog -->
<AlertDialog.Root bind:open={showRejectDialog}>
  <AlertDialog.Content class="max-w-md">
    <AlertDialog.Header>
      <AlertDialog.Title>Reject Reservation</AlertDialog.Title>
      <AlertDialog.Description>
        Please provide a reason for rejecting this reservation. This will be sent to the user.
        {#if reservationToReject}
          <div class="mt-3 p-3 bg-gray-50 rounded">
            <strong>Reservation #{reservationToReject.id}</strong><br>
            {reservationToReject.reservation_type_display || reservationToReject.reservation_type}<br>
            {new Date(reservationToReject.date).toLocaleDateString()} • {reservationToReject.start_time} - {reservationToReject.end_time}
          </div>
        {/if}
      </AlertDialog.Description>
    </AlertDialog.Header>
    
    <div class="py-4">
      <textarea 
        bind:value={rejectionReason}
        placeholder="Enter reason for rejection..."
        rows="3"
        class="w-full min-h-[80px] px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      ></textarea>
    </div>
    
    <AlertDialog.Footer>
      <AlertDialog.Cancel onclick={closeRejectDialog}>Cancel</AlertDialog.Cancel>
      <AlertDialog.Action onclick={confirmReject} class="bg-red-600 hover:bg-red-700">
        Reject Reservation
      </AlertDialog.Action>
    </AlertDialog.Footer>
  </AlertDialog.Content>
</AlertDialog.Root>
