<script lang="ts">
import '@event-calendar/core/index.css';
import {Calendar, TimeGrid} from '@event-calendar/core';
import { user } from '$lib/stores/user';
import { getCalendar } from '$lib/api/index';
import { invalidateCalendarCache } from '$lib/stores/reservation';

let ec = $state<any>();
let loading = $state(false);
let error = $state('');


let options = $state({
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
}); 
/*
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
}; */



/* eventClick: handleEventClick
   optional in future: Handle clicks on events to show details
*/

// Reload calendar data when cache is invalidated (e.g., after creating/updating a reservation)
/*$effect(() => {
	if ($invalidateCalendarCache && ec) {
    ec.refetchEvents();
	}
});*/



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

async function fetchEvents(fetchInfo: any, successCallback: any, failureCallback: any) {
    console.log('fetchEvents called:', fetchInfo);
    try {
      const calendarData = await getCalendar(formatDate(fetchInfo.start), formatDate(fetchInfo.end));
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
            title: getReservationTitle(reservation),
            //start: `${reservation.date}T${reservation.start_time}`,\
            start: new Date(`${reservation.date}T${reservation.start_time}`),
            // end: `${reservation.date}T${reservation.end_time}`,
            end: new Date(`${reservation.date}T${reservation.end_time}`),
            backgroundColor: getReservationColor(reservation),
            textColor: '#ffffff',
            extendedProps: {
              status: reservation.status,
              notes: reservation.notes,
              user_email: reservation.user_email,
              isOwner: reservation.user === $user?.id
            }
          });
        } 
      }
      console.log('Fetched events:', events);
      try {
        successCallback(events);
      } catch (error:any) {
        console.error('Error in successCallback:', error);
      }
      //successCallback(events);
      //return events;
    } catch (err: any) {
      error = err.message || 'Failed to load calendar data';
      console.error('Calendar load error:', err);
      failureCallback(err);
      //throw err;
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
function getReservationTitle(reservation: any): string {
  if ($user?.role === 'admin') {
    //return `${reservation.user.email} - ${reservation.status}`;
    return `${reservation.user.email}`;
  }
  if (reservation.user.id === $user?.id) {
    //return `Your Reservation (${reservation.status})`;
    return `Your Reservation`;
  }
  return 'Reserved';
}

  //NOTE: currently calendar api doesn't return pending or cancelled reservations
  // so technically that part is unnecessary, but if the api changes in the future, it's there!
function getReservationColor(reservation: any): string {
    if (reservation.user.id === $user?.id) {
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

{#if loading}
    <p>Loading calendar...</p>
{:else if error}
    <p class="text-red-500">Error: {error}</p>
{:else}
    <!-- why is calendar bound to itself?
    <Calendar plugins={[TimeGrid]} {options} bind:this={ec} /> -->
    <Calendar plugins={[TimeGrid]} {options} />
{/if}