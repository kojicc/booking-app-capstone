<script lang="ts">
    import ConfirmationBadge from '$lib/components/ConfirmationBadge.svelte';
    import { createEventDispatcher } from 'svelte';

    const dispatch = createEventDispatcher<{ confirm: { bookingNumber: string|number }, reject: { bookingNumber: string|number } }>();

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
        role = 'admin' } = $props();
   
    function buildEventSubtitle(){
        let eventSubtitle = space;
        if (addons.length > 0){
            eventSubtitle += ' | Add-ons:';
            for (let i = 0; i < addons.length; i++) {
                eventSubtitle += (' ' + addons[i]);
                eventSubtitle += ','
            }
            //remove trailing comma
            eventSubtitle = eventSubtitle.slice(0, -1);
        }
        return eventSubtitle;
    }

    function handleConfirm() {
        dispatch('confirm', { bookingNumber });
    }

    function handleReject() {
        dispatch('reject', { bookingNumber });
    }
   
   
</script>

{#snippet detail(label: string, value: string)}
    <div>
        <p class="text-xs text-neutral-500"> {label}</p>
        <p class="text-sm font-bold"> {value}</p>
    </div>
{/snippet}
<div class="flex flex-col space-y-4 rounded-xl border p-4 shadow-xs max-w-sm hover:shadow-md transition-shadow">
    <ConfirmationBadge status={bookingStatus.toLowerCase()}/>
    <h3 class="text-xl font-bold"> {bookingName} </h3>
    <p class="text-xs text-neutral-500"> {buildEventSubtitle()} </p>
    <div class ="grid grid-cols-1 gap-2 sm:grid-cols-2">

        {@render detail('Reservation Under', userWhoBooked)}
        {@render detail('Booking Number', bookingNumber)}
        {@render detail('Date', date)}
        {@render detail('Time', startTime + ' - ' + endTime)}
    </div>
    {#if rejectionMessage != 'not rejected'}
    <p class="text-xs text-red-600"> {rejectionMessage} </p>
    {/if}

    {#if role === 'admin'}
    <div class="flex space-x-2 mt-2">
    <button class="px-3 py-1 bg-primary-200-var text-white rounded-md" onclick={handleConfirm}>Confirm</button>
    <button class="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded-md" onclick={handleReject}>Reject</button>
    </div>
    {/if}
</div>