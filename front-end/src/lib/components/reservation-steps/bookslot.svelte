<script lang="ts">
import { getCalendar, getCalendarForDate, getCalendarMonthCached, type CalendarDay, type TimeSlot } from "$lib/api/reservation";
import * as Popover from "$lib/components/ui/popover";
import Calendar from "$lib/components/ui/calendar/calendar.svelte";
import * as Select from "$lib/components/ui/select";
import { ScrollArea } from "$lib/components/ui/scroll-area";
import * as Alert from "$lib/components/ui/alert";
import { Spinner } from "$lib/components/ui/spinner";
import { Calendar as CalendarIcon } from "lucide-svelte";
import { Check } from "lucide-svelte";
import { Button } from "$lib/components/ui/button/index.js";
import { DateFormatter, CalendarDate, getLocalTimeZone } from "@internationalized/date";
import { cn } from "$lib/utils";
import { Input } from "$lib/components/ui/input/index.js";
import { Clock } from "lucide-svelte";



interface Props {
  bookingName?: string;
  date?: string;
  space?: string;
  startTime?: string;
  endTime?: string;
  primetimeSelected?: boolean;
  // parent should set open when modal is shown so the component can decide whether to show cached or check latest
  open?: boolean;
  totalHours?: number;
  totalCost?: number;
  // expose validation state to parent so modal can disable Next button
  isValidating?: boolean;
  validationError?: string;
}

let { 
  bookingName = $bindable(""),
  date = $bindable(""),
  space = $bindable("Workspace Main"),
  startTime = $bindable(""),
  endTime = $bindable(""),
  primetimeSelected = $bindable(false),
  open = $bindable(false),
  totalHours = 0,
  totalCost = 0,
  isValidating = $bindable(false),
  validationError = $bindable("")
}: Props = $props();

let endTimeRef;

// Local select value for the UI Select (it expects an array of strings)
// Date restrictions and calendar state
const _localToday = new Date();
const _pad = (n: number) => String(n).padStart(2, '0');
let minDate = $state(`${_localToday.getFullYear()}-${_pad(_localToday.getMonth() + 1)}-${_pad(_localToday.getDate())}`);

// shadcn calendar state
const df = new DateFormatter("en-US", { dateStyle: "long" });

// Initialize value - will be synced with incoming date prop via $effect
const _today = new Date();
let value = $state<CalendarDate | undefined>(new CalendarDate(_today.getFullYear(), _today.getMonth() + 1, _today.getDate()));
let contentRef = $state<HTMLElement | null>(null);
let popoverOpen = $state(false);

// Track if component just mounted to prioritize incoming date prop
let justMounted = $state(true);

$effect(() => {
  // On mount or when date prop changes, sync it to calendar value
  if (justMounted && date) {
    try {
      const parts = String(date).split('-').map(Number);
      if (parts.length === 3) {
        const parsed = new CalendarDate(parts[0], parts[1], parts[2]);
        value = parsed;
      }
    } catch (e) {
      // ignore parse errors
    }
    justMounted = false;
  }
});

$effect(() => {
  if (value) {
    // value.toString() returns ISO date yyyy-mm-dd
    date = value.toString();
  }
});

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
    }
  }
});

$effect(() => {
  if (value) {
    const dateStr = value.toString();
    if (minDate && dateStr < minDate) {
      const parts = minDate.split('-').map(Number);
      value = new CalendarDate(parts[0], parts[1], parts[2]);
      date = minDate;
    }
  }
});

// Time slots and availability
// State variables for time selection and server checks
let selectedTimes = $state<string[]>([]);
let availableSlots = $state<TimeSlot[]>([]);
let calendarData = $state<CalendarDay[]>([]);
let customTimeError = $state<string>('');
let isCheckingConflict = $state(false);
let serverReservedSlots = $state<any[] | null>(null);
let changesDetected = $state(false);
let checkingServerChanges = $state(false);
let validateTimer: any = null;
let validationSuccess = $state(false);
// Track what changed for user context
let changedSlots = $state<{added: any[], removed: any[]}>({added: [], removed: []});
// Track conflicting slots for display
let conflictingSlots = $state<any[]>([]);

// Sync internal state to bindable props for parent
$effect(() => {
  isValidating = isCheckingConflict;
  validationError = customTimeError;
});

// Validate against cached data when times change
$effect(() => {
  // track changes to startTime/endTime and availableSlots
  const _start = startTime;
  const _end = endTime;
  const _slots = availableSlots;
  
  if (_start && _end && _slots.length > 0) {
    validateTimesAgainstCache();
  } else {
    // No times to validate or no slots loaded yet; clear state
    customTimeError = '';
    validationSuccess = false;
    isCheckingConflict = false;
  }
});

// Validate times against cached slots
function validateTimesAgainstCache() {
  // clear previous error
  customTimeError = '';
  validationSuccess = false;

  // Parse times
  const normalizeToHHMM = (t: string) => (t ? String(t).split(':').slice(0,2).join(':') : '');
  const [startHour, startMin] = startTime.split(':').map(Number);
  const [endHour, endMin] = endTime.split(':').map(Number);
  const startMinutes = startHour * 60 + startMin;
  const endMinutes = endHour * 60 + endMin;

  // Validate time range
  if (startMinutes >= endMinutes) {
    customTimeError = 'End time must be after start time';
    return;
  }

  // Enforce minimum 30 minutes
  if (endMinutes - startMinutes < 30) {
    customTimeError = 'Selected time range must be at least 30 minutes';
    return;
  }

  // Determine per-day business hours (fall back to 07:00-19:00)
  const dayData = calendarData.find(d => d.date === date);
  const businessStart = dayData?.business_hours?.start_time ? normalizeToHHMM(dayData.business_hours.start_time) : '07:00';
  const businessEnd = dayData?.business_hours?.end_time ? normalizeToHHMM(dayData.business_hours.end_time) : '19:00';
  const [bsH, bsM] = businessStart.split(':').map(Number);
  const [beH, beM] = businessEnd.split(':').map(Number);
  const businessStartMinutes = bsH * 60 + bsM;
  const businessEndMinutes = beH * 60 + beM;

  if (startMinutes < businessStartMinutes || endMinutes > businessEndMinutes) {
    customTimeError = `Time must be between ${businessStart} and ${businessEnd}`;
    return;
  }

  // Build list of reserved slots to check against: prefer server-provided reserved for freshness
  const localReserved = dayData?.reserved_slots || [];
  const reservedToCheck = serverReservedSlots && serverReservedSlots.length > 0 ? serverReservedSlots : localReserved;

  // Find conflicting slots - exclude PENDING status (those don't block booking)
  const conflicts = reservedToCheck.filter((r: any) => {
    // Skip PENDING reservations - they don't block other bookings
    if (r.status === 'PENDING') return false;
    
    const rStart = normalizeToHHMM(r.start_time);
    const rEnd = normalizeToHHMM(r.end_time);
    const [rsH, rsM] = rStart.split(':').map(Number);
    const [reH, reM] = rEnd.split(':').map(Number);
    const rStartMinutes = rsH * 60 + rsM;
    const rEndMinutes = reH * 60 + reM;
    return (startMinutes < rEndMinutes && endMinutes > rStartMinutes);
  });

  if (conflicts.length > 0) {
    conflictingSlots = conflicts;
    customTimeError = 'Selected time conflicts with an existing reservation';
    return;
  } else {
    conflictingSlots = [];
  }

  // Check if it's during primetime hours
  // Mark primetime if the selected range overlaps the day's primetime hours
  if (dayData?.primetime_hours?.start_time && dayData?.primetime_hours?.end_time) {
    const pStart = normalizeToHHMM(dayData.primetime_hours.start_time);
    const pEnd = normalizeToHHMM(dayData.primetime_hours.end_time);
    const [pSH, pSM] = pStart.split(':').map(Number);
    const [pEH, pEM] = pEnd.split(':').map(Number);
    const pStartMinutes = pSH * 60 + pSM;
    const pEndMinutes = pEH * 60 + pEM;
    primetimeSelected = (startMinutes < pEndMinutes && endMinutes > pStartMinutes);
  } else {
    primetimeSelected = false;
  }

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

  // No conflicts, mark as valid
  validationSuccess = true;
}

// Helper to get month key (YYYY-MM) from a date string
function getMonthKey(dateStr: string): string {
  const d = new Date(dateStr);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

// Check if a date has any available slots
function isDateAvailable(dateValue: CalendarDate): boolean {
  if (!dateValue) return false;
  const dateStr = dateValue.toString();

  if (minDate && dateStr < minDate) return false;

  const dayData = calendarData.find(day => day.date === dateStr);
  if (!dayData) return true;
  return dayData.available_slots.some(slot => slot.available);
}

// Helper to fetch month data
async function fetchMonthData(year: number, month: number) {
  const startOfMonth = new Date(year, month, 1).toISOString().split('T')[0];
  const endOfMonth = new Date(year, month + 1, 0).toISOString().split('T')[0];
  
  try {
    // use cached month fetch helper so we don't re-request the same month unnecessarily
    const response = await getCalendarMonthCached(year, month);
    const normalizeTime = (t: string) => (typeof t === 'string' ? t.split(':').slice(0,2).join(':') : t);

    calendarData = (response.calendar || []).map((day: any) => ({
      ...day,
      available_slots: (day.available_slots || []).map((slot: any) => ({
        ...slot,
        start_time: normalizeTime(slot.start_time),
        end_time: normalizeTime(slot.end_time),
      })),
    }));
    currentCachedMonth = `${year}-${String(month + 1).padStart(2, '0')}`;
  } catch (error) {
    console.error('Failed to fetch calendar:', error);
    calendarData = [];
  }
}

// State for loading and cached month
let loadingSlots = $state(false);
let currentCachedMonth = $state<string | null>(null);

async function getAvailableTimeSlots(selectedDate: string): Promise<TimeSlot[]> {
  const dayData = calendarData.find(day => day.date === selectedDate);
  if (!dayData) return [];
  return dayData.available_slots || [];
}

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
      
      if (monthKey !== currentCachedMonth) {
        loadingSlots = true;
        const selectedDate = new Date(date);
        await fetchMonthData(selectedDate.getFullYear(), selectedDate.getMonth());
        loadingSlots = false;
      }
      
      availableSlots = await getAvailableTimeSlots(date);
      // also fetch authoritative reserved_slots for this date to detect changes
      checkingServerChanges = true;
      try {
        const day = await getCalendarForDate(date);
        serverReservedSlots = day?.reserved_slots || [];
        // compare with local available/reserved slots to detect changes
        const localReserved = (calendarData.find(c => c.date === date)?.reserved_slots || []).map(r => `${r.start_time}-${r.end_time}-${r.status}`);
        const serverList = (serverReservedSlots || []).map((r: any) => `${r.start_time}-${r.end_time}-${r.status}`);
        changesDetected = JSON.stringify(localReserved) !== JSON.stringify(serverList);
      } catch (e) {
        console.error('Error checking server date:', e);
      } finally {
        checkingServerChanges = false;
      }
    } else {
      availableSlots = [];
    }
  }
  loadCalendarData();
});

// Reload month data from server (force) and refresh local state
async function reloadMonthFromServer() {
  if (!date) return;
  const d = new Date(date);
  loadingSlots = true;
  try {
    await getCalendarMonthCached(d.getFullYear(), d.getMonth(), true);
    await fetchMonthData(d.getFullYear(), d.getMonth());
    availableSlots = await getAvailableTimeSlots(date);
    changesDetected = false;
  } finally {
    loadingSlots = false;
  }
}


// Time slot selection functions
function toggleTimeSlot(slot: TimeSlot) {
  const fmt = (t: string) => (t ? String(t).split(':').slice(0,2).join(':') : '');
  const startNorm = fmt(slot.start_time);
  const endNorm = fmt(slot.end_time);
  const slotKey = `${startNorm} - ${endNorm}`;
  
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

    startTime = startNorm;
    endTime = endNorm;
    primetimeSelected = slot.type === 'PRIMETIME';
  }
}

// Track previous date to only clear when date actually changes
let previousDate = $state<string>("");

// Clear selections only when date changes to a different date
$effect(() => {
  const _d = date;
  if (previousDate && _d && previousDate !== _d) {
    // Date changed to a different date - clear selections
    selectedTimes = [];
    startTime = "";
    endTime = "";
    primetimeSelected = false;
  }
  previousDate = _d;
});

// Handle manual time input matching
// Note: the primary validation flow is handled by validateTimesLocalThenServer()

// Validate against cache for fast feedback (called by parent modal)
async function validateManualTimesWithServer(): Promise<boolean> {
  if (!date || !startTime || !endTime) return false;

  const normalizeToHHMM = (t: string) => (t ? String(t).split(':').slice(0,2).join(':') : '');

  // Parse times
  const [sh, sm] = startTime.split(':').map(Number);
  const [eh, em] = endTime.split(':').map(Number);
  const s = sh * 60 + sm;
  const e = eh * 60 + em;

  // Basic range checks
  if (s >= e) {
    customTimeError = 'End time must be after start time';
    validationSuccess = false;
    return true;
  }

  if (e - s < 30) {
    customTimeError = 'Selected time range must be at least 30 minutes';
    validationSuccess = false;
    return true;
  }

  // Per-day business hours
  const dayData = calendarData.find(d => d.date === date);
  const businessStart = dayData?.business_hours?.start_time ? normalizeToHHMM(dayData.business_hours.start_time) : '07:00';
  const businessEnd = dayData?.business_hours?.end_time ? normalizeToHHMM(dayData.business_hours.end_time) : '19:00';
  const [bsH, bsM] = businessStart.split(':').map(Number);
  const [beH, beM] = businessEnd.split(':').map(Number);
  const businessStartMinutes = bsH * 60 + bsM;
  const businessEndMinutes = beH * 60 + beM;

  if (s < businessStartMinutes || e > businessEndMinutes) {
    customTimeError = `Time must be between ${businessStart} and ${businessEnd}`;
    validationSuccess = false;
    return true;
  }

  // Use serverReservedSlots if available, otherwise dayData reserved slots
  const localReserved = dayData?.reserved_slots || [];
  const reservedToCheck = serverReservedSlots && serverReservedSlots.length > 0 ? serverReservedSlots : localReserved;

  // Find conflicting slots - exclude PENDING status (those don't block booking)
  const conflicts = reservedToCheck.filter((r: any) => {
    // Skip PENDING reservations - they don't block other bookings
    if (r.status === 'PENDING') return false;
    
    const rStart = normalizeToHHMM(r.start_time);
    const rEnd = normalizeToHHMM(r.end_time);
    const [rsH, rsM] = rStart.split(':').map(Number);
    const [reH, reM] = rEnd.split(':').map(Number);
    const rStartMinutes = rsH * 60 + rsM;
    const rEndMinutes = reH * 60 + reM;
    return (s < rEndMinutes && e > rStartMinutes);
  });

  if (conflicts.length > 0) {
    conflictingSlots = conflicts;
    customTimeError = 'Selected time conflicts with an existing reservation';
    validationSuccess = false;
    return true; // true = conflict found
  } else {
    conflictingSlots = [];
    customTimeError = '';
    validationSuccess = true;
    return false; // false = no conflict
  }
}

// Expose a validate method so parent can call it (e.g. modal before advancing steps)
export function validate(): Promise<boolean> {
  return validateManualTimesWithServer();
}

// Expose a reset validation method so parent can call it when user navigates back
// Preserves user input (startTime/endTime) but clears validation state
export function resetValidation() {
  customTimeError = '';
  validationSuccess = false; // Clear success state too
  isCheckingConflict = false;
  if (validateTimer) clearTimeout(validateTimer);
  // Don't clear startTime/endTime - preserve user input
}

// Expose a clearAndReload method for when booking creation fails
// Clears all inputs and forces fresh data reload
export async function clearAndReload() {
  // Clear all form inputs
  bookingName = '';
  startTime = '';
  endTime = '';
  space = 'Workspace Main';
  selectedTimes = [];
  primetimeSelected = false;
  
  // Clear validation state
  customTimeError = '';
  validationSuccess = false;
  isCheckingConflict = false;
  changesDetected = false;
  if (validateTimer) clearTimeout(validateTimer);
  
  // Reset calendar to today
  const today = new Date();
  value = new CalendarDate(today.getFullYear(), today.getMonth() + 1, today.getDate());
  date = value.toString();
  
  // Force reload current month data from server
  loadingSlots = true;
  try {
    await getCalendarMonthCached(today.getFullYear(), today.getMonth(), true);
    await fetchMonthData(today.getFullYear(), today.getMonth());
    availableSlots = await getAvailableTimeSlots(date);
  } finally {
    loadingSlots = false;
  }
}

// Open/reopen logic: when the component receives `open=true`, show cached data immediately
// and then call the server to check for latest changes; only show the refresh alert
// if the server returns a different reserved_slots set than our cached month response.
import { onMount } from 'svelte';
let hasLoadedOnce = false;

async function handleOpenChange(isOpen: boolean) {
  if (!isOpen) return;
  // When opening, if we have not loaded this month yet, fetch month (this will populate cache)
  if (!hasLoadedOnce) {
    const d = date ? new Date(date) : new Date();
    await fetchMonthData(d.getFullYear(), d.getMonth());
    availableSlots = await getAvailableTimeSlots(date || d.toISOString().split('T')[0]);
    hasLoadedOnce = true;
    // do not show refresh UI on first load
    changesDetected = false;
    return;
  }

  // For subsequent openings: show cached data but also check latest server state
  checkingServerChanges = true;
  try {
    const d = date ? new Date(date) : new Date();
    const serverDay = await getCalendarForDate((date || d.toISOString().split('T')[0]), true);
    const serverSlots = serverDay?.reserved_slots || [];
    const localDay = calendarData.find(c => c.date === (date || d.toISOString().split('T')[0]));
    const localSlots = localDay?.reserved_slots || [];
    
    // Build string representations for comparison
    const serverList = serverSlots.map((r: any) => `${r.start_time}-${r.end_time}-${r.status}`);
    const localList = localSlots.map((r: any) => `${r.start_time}-${r.end_time}-${r.status}`);
    
    if (JSON.stringify(serverList) !== JSON.stringify(localList)) {
      changesDetected = true;
      serverReservedSlots = serverSlots;
      
      // Compute diff: which slots were added or removed
      const added = serverSlots.filter((s: any) => 
        !localSlots.some((l: any) => l.start_time === s.start_time && l.end_time === s.end_time)
      );
      const removed = localSlots.filter((l: any) => 
        !serverSlots.some((s: any) => s.start_time === l.start_time && s.end_time === l.end_time)
      );
      changedSlots = { added, removed };
    } else {
      changesDetected = false;
      changedSlots = { added: [], removed: [] };
    }
  } catch (e) {
    console.error('Error checking latest on open:', e);
  } finally {
    checkingServerChanges = false;
  }
}

// react to open changes
$effect(() => { void handleOpenChange(open); });

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
        placeholder="Booking name" 
        bind:value={bookingName} 
      />
    </div>
    
    <div>
      <label for="reservation-date" class="block text-sm font-medium mb-1">Date of Reservation</label>
      <input id="reservation-date" class="sr-only" type="text" bind:value={date} aria-hidden="true" />
  <Popover.Root bind:open={popoverOpen}>
        <Popover.Trigger id="reservation-date-trigger"
          class={cn(
            "w-full justify-start text-left font-normal inline-flex items-center gap-2 px-3 border rounded-md h-9",
            !value && "text-muted-foreground"
          )}
        >
          {#if value}
            {df.format(value.toDate(getLocalTimeZone()))}
          {:else}
            Pick a date
          {/if}
          <CalendarIcon class="ml-auto h-4 w-4" />
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
        <Select.Trigger id="reservation-space" class="w-full justify-start text-left font-normal inline-flex items-center gap-2 px-3 border rounded-md h-10">
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
    <div class="flex items-center justify-between">
      <div class="block text-sm font-medium">Available Time Ranges</div>
      <div class="flex items-center gap-2">
        {#if checkingServerChanges}
          <span class="inline-flex items-center gap-2 text-xs text-gray-600">
            <Spinner class="h-3 w-3 text-gray-600" />
            <span>Checking for changes</span>
          </span>
        {/if}
        {#if changesDetected}
          <span class="inline-flex items-center gap-2 text-xs text-red-600 font-semibold">
            <span>Changes detected</span>
            <Button variant="outline" size="sm" onclick={reloadMonthFromServer}>Reload</Button>
          </span>
        {/if}
      </div>
    </div>
    
    {#if changesDetected && (changedSlots.added.length > 0 || changedSlots.removed.length > 0)}
      <div class="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs">
        <div class="font-semibold text-amber-800 mb-2">Reservation changes detected:</div>
        {#if changedSlots.added.length > 0}
          <div class="mb-2">
            <span class="font-medium text-emerald-700">New reservations:</span>
            <ul class="ml-4 mt-1 space-y-1">
              {#each changedSlots.added as slot}
                <li class="text-gray-700">{slot.start_time} - {slot.end_time}</li>
              {/each}
            </ul>
          </div>
        {/if}
        {#if changedSlots.removed.length > 0}
          <div>
            <span class="font-medium text-red-700">Cancelled reservations:</span>
            <ul class="ml-4 mt-1 space-y-1">
              {#each changedSlots.removed as slot}
                <li class="text-gray-700">{slot.start_time} - {slot.end_time}</li>
              {/each}
            </ul>
          </div>
        {/if}
      </div>
    {/if}
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
            'relative flex flex-col gap-1.5 sm:gap-2 border rounded-lg p-2 sm:p-3 transition-all duration-200 ' +
            (isAvailable 
              ? (isSelected ? 'bg-emerald-50 border-emerald-300 shadow-sm' : 'bg-white border-gray-200 hover:border-emerald-300 hover:shadow-sm') 
              : 'bg-gray-50 border-gray-200 opacity-70')
          }>
            <div class="flex items-center justify-between gap-0.5 ">
              <span class={
                'text-xs sm:text-sm font-semibold whitespace-nowrap ' +
                (isAvailable ? 'text-gray-900' : 'text-gray-500')
              }>
                {slotKey}
              </span>
            </div>
            {#if isPrimetime}
              <!-- Absolute badge positioned above the top-right of the slot card; on large screens sit at far edge -->
              <span aria-hidden="true" class="absolute -top-2 sm:right-5 md:right-0 lg:right-4 lg:translate-x-1/2 inline-flex items-center justify-center px-2 py-0.5 rounded text-[9px] sm:text-[10px] font-semibold bg-yellow-100 text-yellow-800 whitespace-nowrap shadow-sm">
                PT
              </span>
            {/if}
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

  <!-- Time Input Section -->
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
    <div>
      <label for="start-time" class="block text-sm font-medium mb-1">Start Time</label>
      <div class="space-y-1">
        <Input
          id="start-time"
          type="time"
          class="w-full rounded-md border border-gray-300 px-3 py-2 text-base focus:outline-none focus:ring-1 focus:ring-primary-200-var focus:border-primary-200-var transition"
          bind:value={startTime}
          min="07:00"
          max="19:00"
          disabled={loadingSlots}
          placeholder="HH:MM"
        />
        <div class="flex items-center gap-2 text-xs text-gray-600">
          <Clock class="h-3.5 w-3.5" />
          <span>Click to select time (07:00 - 19:00)</span>
        </div>
      </div>
      {#if loadingSlots}
        <p class="text-xs text-gray-500 mt-1">Time inputs disabled while availability loads...</p>
      {/if}
    </div>
    <div>
      <label for="end-time" class="block text-sm font-medium mb-1">End Time</label>
      <div class="space-y-1">
        <Input 
          id="end-time" 
          type="time" 
          class="w-full rounded-md border border-gray-300 px-3 py-2 text-base focus:outline-none focus:ring-1 focus:ring-primary-200-var focus:border-primary-200-var transition" 
          bind:this={endTimeRef}
          bind:value={endTime}
          min="07:00"
          max="19:00"
          disabled={loadingSlots}
          placeholder="HH:MM"
        />
        <div class="flex items-center gap-2 text-xs text-gray-600">
          <Clock class="h-3.5 w-3.5" />
          <span>Click to select time (07:00 - 19:00)</span>
        </div>
      </div>
      {#if loadingSlots}
        <p class="text-xs text-gray-500 mt-1">Time inputs disabled while availability loads...</p>
      {/if}
    </div>
  </div>

  {#if isCheckingConflict}
    <Alert.Root class="border-blue-200 bg-blue-50">
      <Alert.Title>
        <div class="flex items-center gap-2">
          <Spinner class="h-4 w-4 text-blue-600" />
          <span>Checking availability…</span>
        </div>
      </Alert.Title>
      <Alert.Description>
        Validating your selected time range. You can proceed to the next step while this completes.
      </Alert.Description>
    </Alert.Root>
  {:else if customTimeError}
    <Alert.Root variant="destructive" class="border-red-200 bg-red-50">
      <Alert.Title>Unable to book selected time</Alert.Title>
      <Alert.Description>
        <div class="space-y-2">
          <p>{customTimeError}</p>
          {#if conflictingSlots.length > 0}
            <div class="mt-3 pt-3 border-t border-red-300">
              <p class="font-semibold mb-2">Conflicting reservations:</p>
              <ul class="space-y-1">
                {#each conflictingSlots as slot}
                  <li class="text-sm">
                    <span class="font-medium">{slot.booking_name || 'Reservation'}</span>
                    {' • '}
                    <span>{slot.start_time?.split(':').slice(0,2).join(':')} - {slot.end_time?.split(':').slice(0,2).join(':')}</span>
                    {#if slot.status}
                      {' • '}
                      <span class="capitalize">{slot.status_display || slot.status.toLowerCase()}</span>
                    {/if}
                  </li>
                {/each}
              </ul>
            </div>
          {/if}
        </div>
      </Alert.Description>
    </Alert.Root>
  {:else if validationSuccess}
    <Alert.Root class="border-emerald-200 bg-emerald-50">
      <Alert.Title>
        <div class="flex items-center gap-2">
          <Check class="h-4 w-4 text-emerald-600" />
          <span>Time range valid</span>
        </div>
      </Alert.Title>
      <Alert.Description>
        No conflicts detected for the selected time.
        {#if primetimeSelected}
          <div class="mt-2 inline-flex items-center gap-2 px-2 py-1 rounded bg-yellow-100 border border-yellow-300 text-yellow-900 font-semibold text-xs">
            <span class="px-1.5 py-0.5 rounded-full bg-yellow-200">PT</span>
            <span>This is a Primetime booking and will require admin approval</span>
          </div>
        {/if}
      </Alert.Description>
    </Alert.Root>
  {:else if startTime && endTime && !selectedTimes.length}
    <Alert.Root class="border-blue-200 bg-blue-50">
      <Alert.Title>Custom time range selected</Alert.Title>
      <Alert.Description>Make sure the range doesn't conflict with existing reservations.</Alert.Description>
    </Alert.Root>
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