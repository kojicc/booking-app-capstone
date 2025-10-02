<script lang="ts">
    import ConfirmationBadge from '$lib/components/ConfirmationBadge.svelte';
    import { createEventDispatcher } from 'svelte';

    const dispatch = createEventDispatcher<{ 
        confirm: { bookingNumber: string|number }, 
        reject: { bookingNumber: string|number },
        edit: { bookingNumber: string|number },
        cancel: { bookingNumber: string|number }
    }>();

    let {bookingName, 
        userWhoBooked, 
        bookingStatus, 
        bookingNumber, 
        date, 
        space, 
        startTime, 
        endTime, 
        addons = [],
        rejectionMessage = "not rejected",
        role = 'admin',
        rawStatus = '' } = $props();
   
    function buildEventSubtitle(){
        let eventSubtitle = space;
        // Hide add-ons for now - they're shown in notes section instead
        // if (addons.length > 0){
        //     eventSubtitle += ' | Add-ons:';
        //     for (let i = 0; i < addons.length; i++) {
        //         eventSubtitle += (' ' + addons[i]);
        //         eventSubtitle += ','
        //     }
        //     //remove trailing comma
        //     eventSubtitle = eventSubtitle.slice(0, -1);
        // }
        return eventSubtitle;
    }

    function handleConfirm() {
        dispatch('confirm', { bookingNumber });
    }

    function handleReject() {
        dispatch('reject', { bookingNumber });
    }

    function handleEdit() {
        dispatch('edit', { bookingNumber });
    }

    function handleCancel() {
        dispatch('cancel', { bookingNumber });
    }
   
   
</script>

{#snippet detail(label: string, value: string)}
    <div class="min-w-0">
        <p class="text-xs text-neutral-500">{label}</p>
        <p class="text-sm font-bold break-words">{value}</p>
    </div>
{/snippet}
<div class="flex flex-col space-y-4 rounded-xl border p-4 shadow-xs w-full max-w-sm hover:shadow-md transition-shadow">
    <ConfirmationBadge status={bookingStatus.toLowerCase()}/>
    <h3 class="text-xl font-bold break-words">{bookingName}</h3>
    <p class="text-xs text-neutral-500 break-words">{buildEventSubtitle()}</p>
    <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {@render detail('Reservation Under', userWhoBooked)}
        {@render detail('Booking Number', bookingNumber.toString())}
        {@render detail('Date', date)}
        {@render detail('Time', startTime + ' - ' + endTime)}
    </div>
    
    <!-- Notes section - only show for admin -->
    {#if role === 'admin'}
        <div class="pt-2 border-t border-gray-100 min-h-[60px]">
            <p class="text-xs text-neutral-500 mb-1">Notes</p>
            {#if addons.length > 0 && addons[0] !== ''}
                <p class="text-sm text-gray-700 break-words">{addons.join(', ')}</p>
            {:else}
                <p class="text-sm text-gray-400 italic">No additional notes</p>
            {/if}
        </div>
    {/if}
    
    <!-- Rejection reason - only show for admin -->
    {#if role === 'admin' && bookingStatus.toLowerCase() === 'rejected' && rejectionMessage !== 'not rejected' && rejectionMessage !== ''}
        <div class="pt-2 border-t border-red-100 bg-red-50 -mx-4 -mb-4 px-4 py-3 rounded-b-xl">
            <p class="text-xs text-red-600 font-semibold mb-1">Rejection Reason</p>
            <p class="text-sm text-red-700 break-words">{rejectionMessage}</p>
        </div>
    {/if}

    {#if role === 'admin' && (rawStatus ? rawStatus.toLowerCase() === 'pending' : bookingStatus.toLowerCase() === 'pending')}
        <div class="flex space-x-2 mt-2">
            <button class="px-3 py-1 bg-primary-200-var hover:bg-primary-300-var text-white rounded-md transition-colors" onclick={handleConfirm}>Confirm</button>
            <button class="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors" onclick={handleReject}>Reject</button>
        </div>
    {:else if role === 'user' && bookingStatus.toLowerCase() !== 'cancelled' && bookingStatus.toLowerCase() !== 'completed' && bookingStatus.toLowerCase() !== 'rejected'}
        <div class="flex gap-2 mt-2">
            <button class="flex-1 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm transition-colors" onclick={handleEdit}>Edit</button>
            <button class="flex-1 px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded-md text-sm transition-colors" onclick={handleCancel}>Cancel</button>
        </div>
    {/if}
</div>