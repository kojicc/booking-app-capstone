<script lang="ts">
    import ConfirmationBadge from '$lib/components/ConfirmationBadge.svelte';
    let {bookingName, 
        userWhoBooked, 
        bookingStatus, 
        bookingNumber, 
        date, 
        space, 
        startTime, 
        endTime, 
        addons,
        rejectionMessage = "not rejected"} = $props();
   
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
</div>