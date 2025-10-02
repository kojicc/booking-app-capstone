<script lang="ts">
import '@event-calendar/core/index.css';
import {Calendar, TimeGrid} from '@event-calendar/core';
import { user } from '$lib/stores/user';
import { onMount } from 'svelte';
import { getCalendar } from '$lib/api/index';

let ec = $state<any>();
let loading = $state(true);
let error = $state('');

let options = $state({
    view: 'timeGridWeek',
    slotMinTime: '07:00:00',
    slotMaxTime: '19:00:00',
    events: [
        // list of events to be loaded from api
    ],
    editable: false,          // Cannot drag events
    selectable: false,        // Cannot select time slots
    dayMaxEvents: true,       // Show "more" link if too many events
    nowIndicator: true,       // Shows current time line
});


/* eventClick: handleEventClick
   optional in future: Handle clicks on events to show details
*/
onMount(async () => {
    await loadCalendarData();
  });

function formatDate(date: Date): string {
    // Format date as YYYY-MM-DD for the API
    return date.toISOString().split('T')[0];
  }

async function loadCalendarData(startDate?: string, endDate?: string) {
    loading = true;
    error = '';
    
    try {

      // If dates not provided, calculate current week
      if (!startDate || !endDate) {
        // Get current week range
        const today = new Date();
        // copy date to avoid mutating today
        const startOfWeek = new Date(today);
        // this gets the date of the previous Sunday
        // by subtracting the current day of the week (0-6) from the date of the month
        startOfWeek.setDate(today.getDate() - today.getDay());

        // end of week is 6 days after start of week
        const endOfWeek = new Date(startOfWeek);
        endOfWeek.setDate(startOfWeek.getDate() + 6);

        // convert to YYYY-MM-DD
        startDate = formatDate(startOfWeek);
        endDate = formatDate(endOfWeek);
      }
      const calendarData = await getCalendar(startDate, endDate);
      
      // Transform backend data to Event Calendar format
      const events = [];
      
      for (const day of calendarData.calendar) {
        // Add reserved slots as events
        for (const reservation of day.reserved_slots) {
          events.push({
            id: reservation.id,
            title: getReservationTitle(reservation),
            start: `${reservation.date}T${reservation.start_time}`,
            end: `${reservation.date}T${reservation.end_time}`,
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

        // Future feature (still buggy): display primetime hours
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
      }

      options.events = events;
    } catch (err: any) {
      error = err.message || 'Failed to load calendar data';
      console.error('Calendar load error:', err);
    } finally {
      loading = false;
    }
  }

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

//this function will be called as an event handler when the calendar view changes
function handleViewChange(info: any) {
    // Use the date range provided by the event
    const startDate = formatDate(new Date(info.start));
    const endDate = formatDate(new Date(info.end));
    loadCalendarData();
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
    <Calendar plugins={[TimeGrid]} {options} onViewDidMount={handleViewChange} bind:this={ec} />
{/if}