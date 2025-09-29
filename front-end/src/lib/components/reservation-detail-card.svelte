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
        <p> {label}</p>
        <p> {value}</p>
    </div>
{/snippet}
<div>
    <ConfirmationBadge status={bookingStatus.toLowerCase()}/>
    <h3> {bookingName} </h3>
    <p> {buildEventSubtitle()} </p>
    <div>
        {@render detail('Reservation Under', userWhoBooked)}
        {@render detail('Booking Number', bookingNumber)}
        {@render detail('Date', date)}
        {@render detail('Time', startTime + ' - ' + endTime)}
    </div>
    {#if rejectionMessage != 'not rejected'}
    <p> {rejectionMessage} </p>
    {/if}
</div>