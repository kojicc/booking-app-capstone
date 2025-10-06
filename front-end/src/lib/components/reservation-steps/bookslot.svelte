<script lang="ts">
import { getCalendar, type CalendarDay, type TimeSlot } from "$lib/api/reservation";
import * as Popover from "$lib/components/ui/popover";
import Calendar from "$lib/components/ui/calendar/calendar.svelte";
import * as Select from "$lib/components/ui/select";
import { ScrollArea } from "$lib/components/ui/scroll-area/index.js";
import { Calendar as CalendarIcon } from "lucide-svelte";
import { DateFormatter, CalendarDate, getLocalTimeZone } from "@internationalized/date";
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
let customTimeError = $state<string>('');
// Manual input debounce helpers
let manualStartInput = $state('');
let manualEndInput = $state('');
let debounceTimer: number | null = null;

// Date restrictions
// Use local date (not toISOString which uses UTC) to avoid timezone drift where
// minDate could be the previous day in some timezones.
const _localToday = new Date();
const _pad = (n: number) => String(n).padStart(2, '0');
let minDate = $state(`${_localToday.getFullYear()}-${_pad(_localToday.getMonth() + 1)}-${_pad(_localToday.getDate())}`);

// shadcn calendar state
const df = new DateFormatter("en-US", { dateStyle: "long" });
// Initialize calendar to today's date so the picker opens on current month
const _today = new Date();
let value = $state<CalendarDate | undefined>(new CalendarDate(_today.getFullYear(), _today.getMonth() + 1, _today.getDate()));
let contentRef = $state<HTMLElement | null>(null);
// control popover open state to avoid duplicate renderings
let popoverOpen = $state(false);

// convert selected DateValue to ISO date string used by API and bindings
$effect(() => {
  if (value) {
    // value.toString() returns ISO date yyyy-mm-dd
    date = value.toString();
  }
});

// If the `date` string changes (for example from parent props or saved form state),
// make sure the CalendarDate `value` reflects it so the picker opens to correct month.
$effect(() => {
  if (date) {
    try {
      const parts = String(date).split('-').map(Number);
      if (parts.length === 3) {
        const [y, m, d] = parts;
        const parsed = new CalendarDate(y, m, d);
        if (!value || value.toString() !== parsed.toString()) {
          value = parsed;
        }
      }
    } catch (e) {
      // ignore invalid date formats
    }
  }
});

// Prevent selecting past dates by coercing value to minDate when necessary
$effect(() => {
  if (value) {
    const dateStr = value.toString();
    if (minDate && dateStr < minDate) {
      // reset to minDate
      const parts = minDate.split('-').map(Number);
      value = new CalendarDate(parts[0], parts[1], parts[2]);
      date = minDate;
    }
  }
});

$effect(() => {
  // Keep manual inputs in sync when programmatic changes occur
  if (startTime !== manualStartInput) manualStartInput = startTime || '';
  if (endTime !== manualEndInput) manualEndInput = endTime || '';
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
function isDateAvailable(dateValue: CalendarDate): boolean {
  if (!dateValue) return false;
  const dateStr = dateValue.toString();

  // Disallow dates earlier than minDate (past dates)
  if (minDate && dateStr < minDate) return false;

  const dayData = calendarData.find(day => day.date === dateStr);
  // If date is not in calendarData yet, assume it's available (will be fetched when selected)
  // Only mark as unavailable if we have the data AND all slots are unavailable
  if (!dayData) return true;
  return dayData.available_slots.some(slot => slot.available);
}

// Reactive data loading and time slot management
let loadingSlots = $state(false);
let currentCachedMonth = $state<string | null>(null); // Track which month is currently cached (format: YYYY-MM)

// Helper to get month key from a date
function getMonthKey(dateStr: string): string {
  const d = new Date(dateStr);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

// Helper to fetch month data
async function fetchMonthData(year: number, month: number) {
  const startOfMonth = new Date(year, month, 1).toISOString().split('T')[0];
  const endOfMonth = new Date(year, month + 1, 0).toISOString().split('T')[0];
  
  try {
    const response = await getCalendar(startOfMonth, endOfMonth);
    calendarData = response.calendar;
    currentCachedMonth = `${year}-${String(month + 1).padStart(2, '0')}`;
  } catch (error) {
    console.error('Failed to fetch calendar:', error);
    calendarData = [];
  }
}

// Prefetch current month on component mount
$effect(() => {
  async function prefetchCurrentMonth() {
    loadingSlots = true;
    const today = new Date();
    await fetchMonthData(today.getFullYear(), today.getMonth());
    loadingSlots = false;
  }
  prefetchCurrentMonth();
});

// Load month data when date changes to a different month
$effect(() => {
  async function loadCalendarData() {
    if (date) {
      const monthKey = getMonthKey(date);
      
      // If the selected date is in a different month than cached, fetch that month
      if (monthKey !== currentCachedMonth) {
        loadingSlots = true;
        const selectedDate = new Date(date);
        await fetchMonthData(selectedDate.getFullYear(), selectedDate.getMonth());
        loadingSlots = false;
      }
      
      // Get slots from cached data
      availableSlots = await getAvailableTimeSlots(date);
    } else {
      availableSlots = [];
    }
  }
  loadCalendarData();
});


// Time slot selection functions
function toggleTimeSlot(slot: TimeSlot) {
  // Normalize times to HH:MM (drop seconds) so display and comparisons match
  const fmt = (t: string) => t.split(':').slice(0,2).join(':');
  const slotKey = `${fmt(slot.start_time)} - ${fmt(slot.end_time)}`;
  
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
  // referencing `date` ensures this effect runs only when the selected date changes
  const _d = date;
  selectedTimes = [];
  startTime = "";
  endTime = "";
  primetimeSelected = false;
});

// Handle manual time input matching
$effect(() => {
  if (startTime && endTime && availableSlots.length > 0) {
    customTimeError = '';
    
    // Parse times
    const [startHour, startMin] = startTime.split(':').map(Number);
    const [endHour, endMin] = endTime.split(':').map(Number);
    const startMinutes = startHour * 60 + startMin;
    const endMinutes = endHour * 60 + endMin;
    
    // Validate time range
    if (startMinutes >= endMinutes) {
      customTimeError = 'End time must be after start time';
      return;
    }
    
    // Check if custom time is within business hours (7 AM - 7 PM)
    if (startHour < 7 || endHour > 19 || (endHour === 19 && endMin > 0)) {
      customTimeError = 'Time must be between 7:00 AM and 7:00 PM';
      return;
    }
    
    // Check if time overlaps with any unavailable slots
    const hasConflict = availableSlots.some(slot => {
      if (!slot.available) {
        const [slotStartHour, slotStartMin] = slot.start_time.split(':').map(Number);
        const [slotEndHour, slotEndMin] = slot.end_time.split(':').map(Number);
        const slotStartMinutes = slotStartHour * 60 + slotStartMin;
        const slotEndMinutes = slotEndHour * 60 + slotEndMin;
        
        // Check if custom range overlaps with unavailable slot
        return (startMinutes < slotEndMinutes && endMinutes > slotStartMinutes);
      }
      return false;
    });
    
    if (hasConflict) {
      customTimeError = 'Selected time conflicts with an existing reservation';
      return;
    }
    
    // Check if it's during primetime hours
    const primetimeSlot = availableSlots.find(slot => 
      slot.type === 'PRIMETIME' && 
      slot.start_time <= startTime && 
      slot.end_time >= endTime
    );
    primetimeSelected = !!primetimeSlot;
    
    // Update selected times if valid
    const currentRange = `${startTime} - ${endTime}`;
    const matchingSlot = availableSlots.find(slot => 
      `${slot.start_time} - ${slot.end_time}` === currentRange
    );
    
      if (matchingSlot) {
        if (!(selectedTimes.length === 1 && selectedTimes[0] === currentRange)) {
          selectedTimes = [currentRange];
        }
      } else {
        // Custom time range (not a predefined slot)
        if (selectedTimes.length !== 0) selectedTimes = [];
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

// Debounce manual input updates: when user types, wait 250ms before applying
function onManualStartInput(v: string) {
  manualStartInput = v;
  if (debounceTimer) window.clearTimeout(debounceTimer);
  debounceTimer = window.setTimeout(() => {
    if (/^\d{2}:\d{2}$/.test(manualStartInput)) {
      startTime = manualStartInput;
    }
  }, 250);
}

function onManualEndInput(v: string) {
  manualEndInput = v;
  if (debounceTimer) window.clearTimeout(debounceTimer);
  debounceTimer = window.setTimeout(() => {
    if (/^\d{2}:\d{2}$/.test(manualEndInput)) {
      endTime = manualEndInput;
    }
  }, 250);
}


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
  <Popover.Root bind:open={popoverOpen}>
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
        <Popover.Content
          bind:ref={contentRef}
          class={'w-auto max-w-[92vw] sm:max-w-[320px] p-2 bg-white'}
        >
          {#if popoverOpen}
            <Calendar
              type="single"
              bind:value
              class="rounded-lg"
              isDateUnavailable={(date) => !isDateAvailable(date as CalendarDate)}
            />
          {/if}
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
          {@const fmt = (t: string) => t.split(':').slice(0,2).join(':')}
          {@const slotKey = `${fmt(timeSlot.start_time)} - ${fmt(timeSlot.end_time)}`}
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
                'text-xs sm:text-sm font-semibold whitespace-nowrap ' +
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
        bind:value={manualStartInput}
        oninput={(e) => onManualStartInput(((e.target as HTMLInputElement)?.value) ?? '')}
        min="07:00"
        max="19:00"
        disabled={loadingSlots}
      />
      {#if loadingSlots}
        <p class="text-xs text-gray-500 mt-1">Time inputs disabled while availability loads...</p>
      {/if}
    </div>
    <div>
      <label for="end-time" class="block text-sm font-medium mb-1">End Time</label>
      <input 
        id="end-time" 
        type="time" 
        class="w-full rounded-md border border-gray-300 px-3 py-2 text-base focus:outline-none focus:ring-1 focus:ring-primary-200-var focus:border-primary-200-var transition" 
        bind:value={manualEndInput}
        oninput={(e) => onManualEndInput(((e.target as HTMLInputElement)?.value) ?? '')}
        min="07:00"
        max="19:00"
        disabled={loadingSlots}
      />
      {#if loadingSlots}
        <p class="text-xs text-gray-500 mt-1">Time inputs disabled while availability loads...</p>
      {/if}
    </div>
  </div>

  {#if customTimeError}
    <div class="bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 text-sm">
      {customTimeError}
    </div>
  {:else if startTime && endTime && !selectedTimes.length}
    <div class="bg-blue-50 border border-blue-200 text-blue-700 rounded-lg p-3 text-sm">
      ℹ️ Custom time range selected. Make sure it doesn't conflict with existing reservations.
    </div>
  {/if}

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