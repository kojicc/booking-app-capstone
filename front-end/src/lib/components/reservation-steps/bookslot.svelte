<script lang="ts">
import { getCalendar, type CalendarDay, type TimeSlot } from "$lib/api/reservation";
import * as Popover from "$lib/components/ui/popover";
import * as Calendar from "$lib/components/ui/calendar";
import * as Select from "$lib/components/ui/select";
import { ScrollArea } from "$lib/components/ui/scroll-area/index.js";
import { Calendar as CalendarIcon } from "lucide-svelte";
import { DateFormatter, type DateValue, getLocalTimeZone } from "@internationalized/date";
import { cn } from "$lib/utils";

interface Props {
  bookingName?: string;
  date?: string;
  space?: string;
  startTime?: string;
  endTime?: string;
  primetimeSelected?: boolean;
  totalHours?: number;
  totalCost?: number;
}

let { 
  bookingName = $bindable(""),
  date = $bindable(""),
  space = $bindable("Workspace Main"),
  startTime = $bindable(""),
  endTime = $bindable(""),
  primetimeSelected = $bindable(false),
  totalHours = 0,
  totalCost = 0
}: Props = $props();

// Local select value for the UI Select (it expects an array of strings)
// (Using Select in single mode bound directly to `space`)

// Time slots and availability
let selectedTimes = $state<string[]>([]);
let availableSlots = $state<TimeSlot[]>([]);
let calendarData = $state<CalendarDay[]>([]);

// Date restrictions
let minDate = $state(new Date().toISOString().split('T')[0]); // Today's date

// shadcn calendar state
const df = new DateFormatter("en-US", { dateStyle: "long" });
let value = $state<DateValue | undefined>();
let contentRef = $state<HTMLElement | null>(null);

// convert selected DateValue to ISO date string used by API and bindings
$effect(() => {
  if (value) {
    // value.toString() returns ISO date yyyy-mm-dd
    date = value.toString();
  }
});

// Real backend API functions
async function fetchCalendarData(selectedDate: string) {
  try {
    const startDate = selectedDate;
    // Fetch a month of data to show availability in calendar
    const endDate = new Date(selectedDate);
    endDate.setDate(endDate.getDate() + 30);
    
    const response = await getCalendar(startDate, endDate.toISOString().split('T')[0]);
    return response.calendar;
  } catch (error) {
    console.error('Error fetching calendar data:', error);
    return [];
  }
}

async function getAvailableTimeSlots(selectedDate: string): Promise<TimeSlot[]> {
  const dayData = calendarData.find(day => day.date === selectedDate);
  if (!dayData) return [];
  
  return dayData.available_slots || [];
}

// Check if a date has any available slots
function isDateAvailable(dateValue: DateValue): boolean {
  if (!dateValue) return false;
  const dateStr = dateValue.toString();
  const dayData = calendarData.find(day => day.date === dateStr);
  // If date is not in calendarData yet, assume it's available (will be fetched when selected)
  // Only mark as unavailable if we have the data AND all slots are unavailable
  if (!dayData) return true;
  return dayData.available_slots.some(slot => slot.available);
}

// Reactive data loading and time slot management
let loadingSlots = $state(false);
let fetchedRanges = $state<Set<string>>(new Set());

// Prefetch calendar data on component mount to populate calendar availability  
$effect(() => {
  async function prefetchCalendarData() {
    loadingSlots = true;
    const today = new Date();
    const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0];
    const endOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0).toISOString().split('T')[0];
    const rangeKey = `${startOfMonth}_${endOfMonth}`;
    
    if (!fetchedRanges.has(rangeKey)) {
      try {
        const response = await getCalendar(startOfMonth, endOfMonth);
        calendarData = response.calendar;
        fetchedRanges.add(rangeKey);
      } catch (error) {
        console.error('Failed to prefetch calendar:', error);
      }
    }
    loadingSlots = false;
  }
  prefetchCalendarData();
});

// Load available slots when date changes
$effect(() => {
  async function loadCalendarData() {
    if (date) {
      // Check if we already have data for this date
      const existingData = calendarData.find(day => day.date === date);
      
      if (!existingData) {
        // Calculate month range for this date
        const selectedDate = new Date(date);
        const startOfMonth = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1).toISOString().split('T')[0];
        const endOfMonth = new Date(selectedDate.getFullYear(), selectedDate.getMonth() + 1, 0).toISOString().split('T')[0];
        const rangeKey = `${startOfMonth}_${endOfMonth}`;
        
        // Only fetch if we haven't fetched this range
        if (!fetchedRanges.has(rangeKey)) {
          loadingSlots = true;
          try {
            const response = await getCalendar(startOfMonth, endOfMonth);
            calendarData = response.calendar;
            fetchedRanges.add(rangeKey);
          } catch (error) {
            console.error('Failed to fetch calendar:', error);
          }
          loadingSlots = false;
        }
      }
      
      // Get slots from existing or newly fetched data
      availableSlots = await getAvailableTimeSlots(date);
    } else {
      availableSlots = [];
    }
  }
  loadCalendarData();
});


// Time slot selection functions
function toggleTimeSlot(slot: TimeSlot) {
  const slotKey = `${slot.start_time} - ${slot.end_time}`;
  
  if (selectedTimes.includes(slotKey)) {
    selectedTimes = selectedTimes.filter(t => t !== slotKey);
    // Clear start/end times when deselecting
    if (selectedTimes.length === 0) {
      startTime = "";
      endTime = "";
      primetimeSelected = false;
    }
  } else {
    selectedTimes = [slotKey]; // single select
    
    // Auto-populate start and end times based on selected slot
    startTime = slot.start_time;
    endTime = slot.end_time;
    primetimeSelected = slot.type === 'PRIMETIME';
  }
}

// Clear selections when date changes
$effect(() => {
  selectedTimes = [];
  startTime = "";
  endTime = "";
  primetimeSelected = false;
});

// Handle manual time input matching
$effect(() => {
  if (startTime && endTime && availableSlots.length > 0) {
    const currentRange = `${startTime} - ${endTime}`;
    const matchingSlot = availableSlots.find(slot => 
      `${slot.start_time} - ${slot.end_time}` === currentRange
    );
    
    if (!matchingSlot) {
      selectedTimes = [];
      primetimeSelected = false;
    } else if (!selectedTimes.includes(currentRange)) {
      selectedTimes = [currentRange];
      primetimeSelected = matchingSlot.type === 'PRIMETIME';
    }
  }
});

// Computed values for display
let hasDate = $state(false);
let hasAvailableSlots = $state(false);

$effect(() => {
  hasDate = !!date;
  hasAvailableSlots = availableSlots.length > 0;
});


</script>

<form class="space-y-6">
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
    <div class="sm:col-span-2">
      <label for="booking-name" class="block text-sm font-medium mb-1">Booking Name</label>
      <input 
        id="booking-name" 
        class="w-full rounded-md border border-gray-300 px-3 py-2 text-base focus:outline-none focus:ring-1 focus:ring-primary-200-var focus:border-primary-200-var transition" 
        placeholder="Build Day" 
        bind:value={bookingName} 
      />
    </div>
    
    <div>
      <label for="reservation-date" class="block text-sm font-medium mb-1">Date of Reservation</label>
      <input id="reservation-date" class="sr-only" type="text" bind:value={date} aria-hidden="true" />
      <Popover.Root>
        <Popover.Trigger id="reservation-date-trigger"
          class={cn(
            "w-full justify-start text-left font-normal inline-flex items-center gap-2 px-3 py-2 border rounded-md",
            !value && "text-muted-foreground"
          )}
        >
          <CalendarIcon class="h-4 w-4" />
          {#if value}
            {df.format(value.toDate(getLocalTimeZone()))}
          {:else}
            Pick a date
          {/if}
        </Popover.Trigger>
        <Popover.Content bind:ref={contentRef} class="w-auto max-w-[92vw] sm:max-w-[320px] p-2">
          <Calendar.Calendar 
            type="single" 
            fixedWeeks  
            bind:value 
            isDateUnavailable={(dateValue) => !isDateAvailable(dateValue)}
          />
        </Popover.Content>
      </Popover.Root>
      {#if date}
        <p class="text-xs text-gray-600 mt-1">Selected: {new Date(date).toLocaleDateString('en-US', { dateStyle: 'full' })}</p>
      {/if}
    </div>
    
    <div>
      <label for="reservation-space" class="block text-sm font-medium mb-1">Space</label>
      <Select.Root type="single" bind:value={space}>
        <Select.Trigger id="reservation-space" class="w-full justify-start text-left font-normal inline-flex items-center gap-2 px-3 py-2 border rounded-md">
          <span data-slot="select-value" class={space ? '' : 'text-muted-foreground'}>{space ? space : 'Select a space'}</span>
        </Select.Trigger>
        <Select.Content>
          <div class="p-1">
            <Select.Item value="Great Hall" label="Great Hall" />
            <Select.Item value="Recording Studio" label="Recording Studio" />
            <Select.Item value="Workspace Main" label="Workspace Main" />
          </div>
        </Select.Content>
      </Select.Root>
    </div>
  </div>

  <div class="space-y-3">
    <div class="block text-sm font-medium">Available Time Ranges</div>
    {#if loadingSlots}
      <div class="text-sm text-gray-500 p-4 bg-gray-50 rounded-lg text-center">
        Loading available slots...
      </div>
    {:else if !hasDate}
      <div class="text-sm text-gray-500 p-4 bg-gray-50 rounded-lg text-center">
        Please select a date to view available time slots.
      </div>
    {:else if !hasAvailableSlots}
      <div class="text-sm text-red-600 p-4 bg-red-50 rounded-lg text-center">
        No time slots available for the selected date. Please choose a different date.
      </div>
    {:else}
      <div class="text-xs mb-3 p-2 bg-yellow-50 rounded-lg">
        <span class="inline-flex items-center gap-2 flex-wrap">
          <span class="px-2 py-0.5 rounded-full bg-yellow-200 text-yellow-900 font-semibold text-xs">Primetime</span>
          <span class="text-gray-700">Primetime hours need admin approval and may be pending.</span>
        </span>
      </div>
      <ScrollArea class="h-64 sm:h-72 w-full rounded-md border p-2">
        <div class="grid grid-cols-1 xs:grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 sm:gap-3">
          {#each availableSlots as timeSlot}
          {@const slotKey = `${timeSlot.start_time} - ${timeSlot.end_time}`}
          {@const isSelected = selectedTimes.includes(slotKey)}
          {@const isAvailable = timeSlot.available}
          {@const isPrimetime = timeSlot.type === 'PRIMETIME'}
          <div class={
            'flex flex-col gap-1.5 sm:gap-2 border rounded-lg p-2 sm:p-3 transition-all duration-200 ' +
            (isAvailable 
              ? (isSelected ? 'bg-emerald-50 border-emerald-300 shadow-sm' : 'bg-white border-gray-200 hover:border-emerald-300 hover:shadow-sm') 
              : 'bg-gray-50 border-gray-200 opacity-70')
          }>
            <div class="flex items-center justify-between gap-1 sm:gap-2">
              <span class={
                'text-xs sm:text-sm font-semibold break-all ' +
                (isAvailable ? 'text-gray-900' : 'text-gray-500')
              }>
                {slotKey}
              </span>
              {#if isPrimetime}
                <span class="px-1 sm:px-1.5 py-0.5 rounded text-[9px] sm:text-[10px] font-semibold bg-yellow-100 text-yellow-800 whitespace-nowrap flex-shrink-0">
                  PT
                </span>
              {/if}
            </div>
            <button
              type="button"
              disabled={!isAvailable}
              class={
                'w-full px-2 sm:px-3 py-1 sm:py-1.5 rounded-md font-medium text-[10px] sm:text-xs transition-all ' +
                (!isAvailable
                  ? 'bg-gray-300 text-gray-600 cursor-not-allowed'
                  : isSelected
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-emerald-600 hover:bg-emerald-700 text-white')
              }
              onclick={() => isAvailable && toggleTimeSlot(timeSlot)}
            >
              {!isAvailable ? 'Booked' : isSelected ? 'Cancel' : 'Select'}
            </button>
          </div>
        {/each}
        </div>
      </ScrollArea>
    {/if}
  </div>

  <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
    <div>
      <label for="start-time" class="block text-sm font-medium mb-1">Start Time</label>
      <input 
        id="start-time" 
        type="time" 
        class="w-full rounded-md border border-gray-300 px-3 py-2 text-base focus:outline-none focus:ring-1 focus:ring-primary-200-var focus:border-primary-200-var transition" 
        bind:value={startTime} 
        readonly
      />
    </div>
    <div>
      <label for="end-time" class="block text-sm font-medium mb-1">End Time</label>
      <input 
        id="end-time" 
        type="time" 
        class="w-full rounded-md border border-gray-300 px-3 py-2 text-base focus:outline-none focus:ring-1 focus:ring-primary-200-var focus:border-primary-200-var transition" 
        bind:value={endTime} 
        readonly
      />
    </div>
  </div>

  <div class="bg-blue-50 border border-blue-200 text-blue-700 rounded-lg p-4">
    <div class="flex justify-between items-center gap-4 flex-wrap">
      <span>Hourly Rate: PHP 500.00</span>
      {#if totalHours > 0}
        <span class="font-medium">
          {totalHours} {totalHours === 1 ? 'hour' : 'hours'} × PHP 500.00 = PHP {totalCost.toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </span>
      {:else}
        <span class="text-blue-500">Select time range to calculate total</span>
      {/if}
    </div>
  </div>
</form>