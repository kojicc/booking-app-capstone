<script lang="ts">
interface Props {
  bookingName: string;
  date: string;
  space: string;
  startTime: string;
  endTime: string;
  totalHours: number;
  totalCost: number;
  primetimeSelected?: boolean;
}

let {
  bookingName = $bindable(),
  date = $bindable(),
  space = $bindable(),
  startTime = $bindable(),
  endTime = $bindable(),
  primetimeSelected = $bindable(false),
  totalHours,
  totalCost
}: Props = $props();

let selectedTimes = $state<string[]>([]);

// Mock availability data based on date
function getAvailableTimeRanges(selectedDate: string) {
  if (!selectedDate) return [];
  
  const dateObj = new Date(selectedDate);
  const dayOfWeek = dateObj.getDay(); // 0 = Sunday, 1 = Monday, etc.
  
  // Weekend availability (reduced hours)
  if (dayOfWeek === 0 || dayOfWeek === 6) {
    return [
      { label: "10:00 - 11:00" },
      { label: "11:00 - 12:00" },
      { label: "13:00 - 14:00" },
      { label: "14:00 - 15:00" },
      { label: "15:00 - 16:00", primetime: true },
      { label: "16:00 - 17:00", primetime: true }
    ];
  }
  
  // Weekday availability
  const baseRanges = [
    { label: "08:00 - 09:00" },
    { label: "09:00 - 10:00" },
    { label: "10:00 - 11:00" },
    { label: "11:00 - 12:00" },
    { label: "13:00 - 14:00" },
    { label: "14:00 - 15:00" },
    { label: "15:00 - 16:00", primetime: true },
    { label: "16:00 - 17:00", primetime: true },
    { label: "17:00 - 18:00" }
  ];
  
  // Mock some booked slots based on date
  const dateStr = selectedDate;
  const unavailableSlots = new Set<string>();
  
  // Some mock bookings for specific dates
  if (dateStr.endsWith('-01') || dateStr.endsWith('-15')) {
    unavailableSlots.add("09:00 - 10:00");
    unavailableSlots.add("14:00 - 15:00");
    unavailableSlots.add("16:00 - 17:00");
  }
  
  if (dayOfWeek === 1) { // Mondays are busy
    unavailableSlots.add("08:00 - 09:00");
    unavailableSlots.add("11:00 - 12:00");
  }
  
  if (dayOfWeek === 5) { // Fridays have limited morning slots
    unavailableSlots.add("08:00 - 09:00");
    unavailableSlots.add("09:00 - 10:00");
  }
  
  return baseRanges.filter(range => !unavailableSlots.has(range.label));
}

// Reactive time ranges based on selected date
let timeRanges = $state<{ label: string; primetime?: boolean }[]>([]);

$effect(() => {
  timeRanges = getAvailableTimeRanges(date);
});

// Function to extract start and end times from a time range label
function parseTimeRange(label: string) {
  const [start, end] = label.split(' - ');
  return { start, end };
}

function toggleTime(label: string) {
  if (selectedTimes.includes(label)) {
    selectedTimes = selectedTimes.filter(l => l !== label);
    // Clear start/end times when deselecting
    if (selectedTimes.length === 0) {
      startTime = "";
      endTime = "";
      primetimeSelected = false;
    }
  } else {
    selectedTimes = [label]; // single select for demo
    
    // Auto-populate start and end times based on selected range
    const { start, end } = parseTimeRange(label);
    startTime = start;
    endTime = end;
    // mark primetimeSelected based on the chosen range
    const match = timeRanges.find(r => r.label === label);
    primetimeSelected = !!(match && match.primetime);
  }
}

// Track previous date to detect changes
let previousDate = $state("");

// Clear selections when date changes
$effect(() => {
  if (date !== previousDate) {
    selectedTimes = [];
    startTime = "";
    endTime = "";
    previousDate = date;
    primetimeSelected = false;
  }
});

// Handle manual time input matching
$effect(() => {
  if (startTime && endTime && timeRanges.length > 0) {
    const currentRange = `${startTime} - ${endTime}`;
    const matchingRange = timeRanges.find(range => range.label === currentRange);
    
    if (!matchingRange) {
      selectedTimes = [];
      primetimeSelected = false;
    } else if (!selectedTimes.includes(currentRange)) {
      selectedTimes = [currentRange];
      primetimeSelected = !!matchingRange.primetime;
    }
  }
});

// Computed values for display (concrete state updated by effects)
let hasDate = $state(false);
let hasAvailableSlots = $state(false);
let showTimeSlots = $state(false);

$effect(() => {
  hasDate = !!date;
  hasAvailableSlots = timeRanges.length > 0;
  showTimeSlots = hasDate && hasAvailableSlots;
});
</script>

<form class="space-y-4">
  <div class="grid grid-cols-2 gap-4">
    <div>
      <label for="booking-name" class="block text-sm font-medium mb-1">Booking Name</label>
      <input 
        id="booking-name" 
        class="w-full rounded-md border border-gray-300 px-3 py-2 text-base focus:outline-none focus:ring-1 focus:ring-primary-200-var focus:border-primary-200-var transition" 
        placeholder="Build Day" 
        bind:value={bookingName} 
      />
    </div>
    <div></div>
    <div>
      <label for="reservation-date" class="block text-sm font-medium mb-1">Date of Reservation</label>
      <input 
        id="reservation-date" 
        class="w-full rounded-md border border-gray-300 px-3 py-2 text-base focus:outline-none focus:ring-1 focus:ring-primary-200-var focus:border-primary-200-var transition" 
        type="date" 
        bind:value={date} 
      />
    </div>
    <div>
      <label for="reservation-space" class="block text-sm font-medium mb-1">Space</label>
      <select 
        id="reservation-space" 
        class="w-full rounded-md border border-gray-300 px-3 py-2 text-base focus:outline-none focus:ring-1 focus:ring-primary-200-var focus:border-primary-200-var transition" 
        bind:value={space}
      >
        <option>Workspace Main</option>
        <option>Workspace 2</option>
      </select>
    </div>
  </div>

  <div>
    <div class="block text-sm font-medium mb-1">Available Time Ranges</div>
    {#if !hasDate}
      <div class="text-sm text-gray-500 mb-4 p-3 bg-gray-50 rounded-lg">
        Please select a date to view available time slots.
      </div>
    {:else if !hasAvailableSlots}
      <div class="text-sm text-red-600 mb-4 p-3 bg-red-50 rounded-lg">
        No time slots available for the selected date. Please choose a different date.
      </div>
    {:else}
      <div class="text-xs text-green-700 mb-2">
        * Primetime Hours needs approval prior to booking. Your booking wont be confirmed unless approved by admin.
      </div>
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-3 gap-3">
        {#each timeRanges as timeSlot}
          {@const isSelected = selectedTimes.includes(timeSlot.label)}
          <div class={
            'flex items-center justify-between border-1 border-emerald-200 rounded-xl px-4 py-2 gap-4 hover:scale-105 transition-transform ease-in-out duration-200 ' +
            (isSelected ? 'bg-emerald-50' : 'bg-white')
          }>
            <div class="flex flex-col justify-center flex-1">
              <span class="text-emerald-600 text-base tracking-wide">{timeSlot.label}</span>
              {#if timeSlot.primetime}
                <span class="text-emerald-600 text-xs mt-1">* Primetime Hours</span>
              {/if}
            </div>
            <button
              type="button"
              class={isSelected
                ? 'bg-red-600 hover:bg-red-700 text-white rounded-md px-8 py-2 font-semibold text-base shadow transition-colors' 
                : 'bg-emerald-600 hover:bg-emerald-700 text-white rounded-md px-8 py-2 font-semibold text-base shadow transition-colors'}
              onclick={() => toggleTime(timeSlot.label)}
            >
              {isSelected ? 'Cancel' : 'Select'}
            </button>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <div class="grid grid-cols-2 gap-4">
    <div>
      <label for="start-time" class="block text-sm font-medium mb-1">Start Time</label>
      <input 
        id="start-time" 
        type="time" 
        class="w-full rounded-md border border-gray-300 px-3 py-2 text-base focus:outline-none focus:ring-1 focus:ring-primary-200-var focus:border-primary-200-var transition" 
        bind:value={startTime} 
      />
    </div>
    <div>
      <label for="end-time" class="block text-sm font-medium mb-1">End Time</label>
      <input 
        id="end-time" 
        type="time" 
        class="w-full rounded-md border border-gray-300 px-3 py-2 text-base focus:outline-none focus:ring-1 focus:ring-primary-200-var focus:border-primary-200-var transition" 
        bind:value={endTime} 
      />
    </div>
  </div>

  <div class="bg-blue-50 text-blue-700 rounded p-2 mt-2 text-sm">
    <div class="flex justify-between items-center">
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