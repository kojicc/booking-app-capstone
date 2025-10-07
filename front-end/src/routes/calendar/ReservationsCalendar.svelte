<script lang="ts">
import '@event-calendar/core/index.css';
import {Calendar, TimeGrid} from '@event-calendar/core';
import { user } from '$lib/stores/user';
import { getCalendar } from '$lib/api/index';
import { invalidateCalendarCache } from '$lib/stores/reservation';

let ec = $state<any>();
let loading = $state(false);
let error = $state('');
let fetchCount = 0;

/*let options = $state({
    view: 'timeGridWeek',
    slotMinTime: '07:00:00',
    slotMaxTime: '19:00:00',
    eventSources: [{
      events: fetchEvents
    }],
    editable: false,          // Cannot drag events
    selectable: false,        // Cannot select time slots
    dayMaxEvents: true,       // Show "more" link if too many events
    nowIndicator: true,       // Shows current time line
    loading: handleLoading
}); */

let options = {
    view: 'timeGridWeek',
    slotMinTime: '07:00:00',
    slotMaxTime: '19:00:00',
    eventSources: [{
      events: fetchEvents
    }],
    editable: false,          // Cannot drag events
    selectable: false,        // Cannot select time slots
    dayMaxEvents: true,       // Show "more" link if too many events
    nowIndicator: true,       // Shows current time line
    loading: handleLoading
}; 



/* eventClick: handleEventClick
   optional in future: Handle clicks on events to show details
*/

// Reload calendar data when cache is invalidated (e.g., after creating/updating a reservation)
$effect(() => {
	if ($invalidateCalendarCache && ec) {
    console.log('Cache invalidated, refetching');
    ec.refetchEvents();
	}
});



function handleLoading(isLoading: boolean) {
    // this just sets the state variable to the current loading status
    // down in the actual component display there's an if else that checks it
    // for displaying the loading message  
    loading = isLoading;
  }

function formatDate(date: Date): string {
    // Format date as YYYY-MM-DD for the API
    return date.toISOString().split('T')[0];
  }

async function fetchEvents(fetchInfo: any) {
    // Snapshot the user values at the START of this function call
    // This prevents reactive tracking
    const userSnapshot = $user ? { role: $user.role, id: $user.id } : null;
    // Don't even access $user here - use a fixed snapshot for testing
    //const userSnapshot = null; // Temporarily set to null to test
    
    fetchCount += 1;
    console.log(`===== fetchEvents called #${fetchCount} =====`);
    console.log('Stack trace:', new Error().stack);
    console.log('fetchInfo:', {
        start: fetchInfo.start,
        end: fetchInfo.end,
        startStr: formatDate(fetchInfo.start),
        endStr: formatDate(fetchInfo.end)
    });

    

    try {
      console.log('Calling getCalendar API...');
      const calendarData = await getCalendar(formatDate(fetchInfo.start), formatDate(fetchInfo.end));
      console.log('API response received');
      // Transform backend data to Event Calendar format
      const events = [];

      for (const day of calendarData.calendar) {
        // Add reserved slots as events
        if (!day.reserved_slots || !Array.isArray(day.reserved_slots)) {
          console.warn('Day missing reserved_slots:', day);
          continue;
        }
        for (const reservation of day.reserved_slots) {
          events.push({
            id: reservation.id,
            resourceIds: [],
            allDay: false,
            title: getReservationTitle(reservation, userSnapshot),
            start: `${reservation.date}T${reservation.start_time}`,
            end: `${reservation.date}T${reservation.end_time}`,
            backgroundColor: getReservationColor(reservation, userSnapshot),
            textColor: '#ffffff',
            extendedProps: {
              status: reservation.status,
              notes: reservation.notes,
              user_email: reservation.user_email,
              isOwner: reservation.user === userSnapshot?.id
            }
          });
        } 
      }
      console.log(`Returning ${events.length} events for fetch #${fetchCount}`);
      //successCallback(events);
      return events;
    } catch (err: any) {
      console.error(`Error in fetch #${fetchCount}:`, err);
      error = err.message || 'Failed to load calendar data';
      return [];
    }
}
       // Future feature (still buggy): display primetime hours (place this in fetchEvents)
        /*if (day.available_slots) {
          for (const slot of day.available_slots) {
            if (slot.available) {
              events.push({
                start: `${day.date}T${slot.start_time}`,
                end: `${day.date}T${slot.end_time}`,
                display: 'background',
                backgroundColor: slot.type === 'PRIMETIME' ? '#fff3cd' : '#e8f5e9'
              });
            }
          } 
        } */
     

// this shows different event details for admins or for users 
function getReservationTitle(reservation: any, userSnapshot: {role?: string, id?: number} | null): string {
  if (userSnapshot?.role === 'admin') {
    //return `${reservation.user.email} - ${reservation.status}`;
    return `${reservation.user.email}`;
  }
  if (reservation.user.id === userSnapshot?.id) {
    //return `Your Reservation (${reservation.status})`;
    return `Your Reservation`;
  }
  return 'Reserved';
}

  //NOTE: currently calendar api doesn't return pending or cancelled reservations
  // so technically that part is unnecessary, but if the api changes in the future, it's there!
function getReservationColor(reservation: any, userSnapshot: {role?: string, id?: number} | null): string {
    if (reservation.user.id === userSnapshot?.id) {
      console.log(reservation.status);
      switch (reservation.status) {
        case 'CONFIRMED': return '#4caf50'; //green if it's your confirmed reservation
        case 'PENDING': return '#ff9800'; //orange if it's your pending reservation
        case 'CANCELLED': return '#9e9e9e'; //cancelled - red
        default: return '#2196f3';
      }
    }
    return '#757575'; // Other users' reservations will be dark grey
  }

</script>

<div style="position: relative;">
    {#if loading}
        <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(255,255,255,0.8); display: flex; align-items: center; justify-content: center; z-index: 10;">
            <p>Loading calendar...</p>
        </div>
    {/if}
    
    {#if error}
        <div style="position: absolute; top: 0; left: 0; right: 0; background: #fee; border: 1px solid #fcc; padding: 1rem; z-index: 10;">
            <p class="text-red-500">Error: {error}</p>
        </div>
    {/if}
    
    <Calendar plugins={[TimeGrid]} {options} bind:this={ec} />
</div>

