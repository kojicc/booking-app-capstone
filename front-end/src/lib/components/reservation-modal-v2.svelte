<script lang="ts">
// ===================== IMPORTS =====================
import { MediaQuery } from "svelte/reactivity";
import * as Dialog from "$lib/components/ui/dialog/index.js";
import * as Drawer from "$lib/components/ui/drawer/index.js";
import { Button, buttonVariants } from "$lib/components/ui/button/index.js";
import { Label } from "$lib/components/ui/label/index.js";
import { Input } from "$lib/components/ui/input/index.js";
import * as Select from "$lib/components/ui/select";
import * as Popover from "$lib/components/ui/popover";
import * as Calendar from "$lib/components/ui/calendar";
import { Calendar as CalendarIcon } from "lucide-svelte";
import { DateFormatter, type DateValue, getLocalTimeZone } from "@internationalized/date";
import { cn } from "$lib/utils";
import { createReservation, getCalendar, type TimeSlot, type CalendarDay } from "$lib/api/reservation";
import { showSuccessModal } from '$lib/stores/reservation';
import { toast } from 'svelte-sonner';

// ===================== PROPS =====================
interface Props {
  open?: boolean;
  onClose?: () => void;
  onSuccess?: (bookedTime?: string | Date | number | null, primetime?: boolean) => void;
}

let { open = $bindable(false), onClose, onSuccess }: Props = $props();

// ===================== RESPONSIVE DETECTION =====================
const isDesktop = new MediaQuery("(min-width: 768px)");
const id = crypto.randomUUID();

// ===================== FORM STATE =====================
let step = $state(1);
let loading = $state(false);
let errorMessage = $state('');

// Basic info
let bookingName = $state("");
let date = $state("");
let space = $state("Workspace Main");

// Time selection
let startTime = $state("");
let endTime = $state("");
let selectedTimes = $state<string[]>([]);
let primetimeSelected = $state(false);

// Addons
let selectedAddons = $state<string[]>([]);

// Calendar and slots
let availableSlots = $state<TimeSlot[]>([]);
let calendarData = $state<CalendarDay[]>([]);
let loadingSlots = $state(false);

// Pricing
let totalHours = $state(0);
let totalCost = $state(0);

// ===================== DATE PICKER =====================
const df = new DateFormatter("en-US", { dateStyle: "long" });
let value = $state<DateValue | undefined>();

$effect(() => {
  if (value) {
    date = value.toString();
    loadAvailableSlots(date);
  }
});

// ===================== VALIDATION =====================
let canProceedStep1 = $state(false);

$effect(() => {
  canProceedStep1 = !!(
    bookingName && 
    bookingName.trim().length > 0 && 
    date && 
    startTime && 
    endTime && 
    totalHours > 0
  );
});

// ===================== PRICING =====================
$effect(() => {
  if (!startTime || !endTime) {
    totalHours = 0;
    totalCost = 0;
    return;
  }

  const [startHour, startMin] = startTime.split(':').map(Number);
  const [endHour, endMin] = endTime.split(':').map(Number);

  const startMinutes = startHour * 60 + startMin;
  const endMinutes = endHour * 60 + endMin;

  totalHours = (endMinutes - startMinutes) / 60;
  if (totalHours < 0) totalHours += 24;
  totalCost = totalHours * 500;
});

// ===================== TIME SLOTS =====================
async function loadAvailableSlots(selectedDate: string) {
  if (!selectedDate) return;
  
  loadingSlots = true;
  try {
    const response = await getCalendar(selectedDate, selectedDate);
    calendarData = response.calendar;
    
    const dayData = calendarData.find(day => day.date === selectedDate);
    if (dayData) {
      availableSlots = dayData.available_slots || [];
    } else {
      availableSlots = [];
    }
  } catch (error) {
    console.error('Error loading slots:', error);
    toast.error('Failed to load time slots');
    availableSlots = [];
  } finally {
    loadingSlots = false;
  }
}

function toggleTimeSlot(timeSlot: TimeSlot) {
  const slotKey = `${timeSlot.start_time} - ${timeSlot.end_time}`;
  const index = selectedTimes.indexOf(slotKey);
  
  if (index > -1) {
    selectedTimes = selectedTimes.filter((_, i) => i !== index);
  } else {
    selectedTimes = [...selectedTimes, slotKey];
    
    if (selectedTimes.length === 1) {
      startTime = timeSlot.start_time.substring(0, 5);
      endTime = timeSlot.end_time.substring(0, 5);
    } else {
      endTime = timeSlot.end_time.substring(0, 5);
    }
    
    if (timeSlot.type === 'PRIMETIME') {
      primetimeSelected = true;
    }
  }
}

function handleCustomTimeChange() {
  selectedTimes = [];
  
  if (startTime && endTime) {
    const [startHour, startMin] = startTime.split(':').map(Number);
    const [endHour, endMin] = endTime.split(':').map(Number);
    
    if (startHour * 60 + startMin >= endHour * 60 + endMin) {
      toast.error('End time must be after start time');
      endTime = '';
    }
  }
}

// ===================== NAVIGATION =====================
function nextStep() {
  if (step === 1 && !canProceedStep1) return;
  if (step < 3) step += 1;
}

function prevStep() {
  if (step > 1) step -= 1;
}

function closeModal() {
  open = false;
  step = 1;
  bookingName = "";
  date = "";
  startTime = "";
  endTime = "";
  selectedTimes = [];
  selectedAddons = [];
  value = undefined;
  onClose?.();
}

// ===================== SUBMISSION =====================
async function handleConfirm() {
  loading = true;
  errorMessage = '';

  try {
    const created = await createReservation({
      user: bookingName,
      date,
      start_time: startTime + ':00',
      end_time: endTime + ':00',
      reservation_type: primetimeSelected ? "PRIMETIME" : "FREE_FOR_ALL",
      notes: selectedAddons.join(', ')
    });

    showSuccessModal.set(true);
    toast.success('Reservation created! ' + (primetimeSelected ? 'Pending approval.' : ''));
    onSuccess?.(created.start_time, primetimeSelected);
    closeModal();
  } catch (err: any) {
    console.error('Booking failed:', err);
    errorMessage = err?.message || 'Booking failed';
    toast.error(errorMessage);
  } finally {
    loading = false;
  }
}

$effect(() => {
  if (!open) {
    step = 1;
    errorMessage = '';
  }
});

// ===================== STEP TITLES =====================
function getStepTitle(stepNum: number): string {
  switch (stepNum) {
    case 1: return 'Date & Time';
    case 2: return 'Add-ons';
    case 3: return 'Review';
    default: return '';
  }
}

let stepTitles = $derived([1, 2, 3].map(stepNum => ({
  num: stepNum,
  title: getStepTitle(stepNum),
  active: step === stepNum
})));
</script>

<!-- ===================== DESKTOP VERSION ===================== -->
{#if isDesktop.current}
  <Dialog.Root bind:open>
    <Dialog.Trigger class={buttonVariants({ variant: "outline" })}>
      New Reservation
    </Dialog.Trigger>
    <Dialog.Content class="sm:max-w-[650px]">
      <Dialog.Header>
        <Dialog.Title>New Reservation</Dialog.Title>
        <Dialog.Description>
          <div class="flex items-center gap-2 mt-2 text-sm">
            {#each stepTitles as stepItem, i}
              <span class={stepItem.active ? 'font-bold' : 'text-muted-foreground'}>
                {stepItem.title}
              </span>
              {#if i < stepTitles.length - 1}
                <span class="mx-1">›</span>
              {/if}
            {/each}
          </div>
        </Dialog.Description>
      </Dialog.Header>

      <!-- FORM CONTENT - No nested ScrollArea -->
      <div class="space-y-4 py-2">
        {#if step === 1}
          <div class="grid gap-3">
            <div class="grid gap-2">
              <Label for="booking-name-{id}">Booking Name</Label>
              <Input id="booking-name-{id}" placeholder="Build Day" bind:value={bookingName} />
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div class="grid gap-2">
                <Label>Date</Label>
                <Popover.Root>
                  <Popover.Trigger class={cn(buttonVariants({ variant: "outline" }), "justify-start text-left font-normal w-full", !value && "text-muted-foreground")}>
                    <CalendarIcon class="mr-2 h-4 w-4" />
                    {value ? df.format(value.toDate(getLocalTimeZone())) : "Pick date"}
                  </Popover.Trigger>
                  <Popover.Content class="w-auto p-0">
                    <Calendar.Calendar type="single" bind:value fixedWeeks />
                  </Popover.Content>
                </Popover.Root>
              </div>

              <div class="grid gap-2">
                <Label>Space</Label>
                <Select.Root type="single" bind:value={space}>
                  <Select.Trigger class="w-full">
                    <span>{space}</span>
                  </Select.Trigger>
                  <Select.Content>
                    <Select.Item value="Great Hall">Great Hall</Select.Item>
                    <Select.Item value="Recording Studio">Recording Studio</Select.Item>
                    <Select.Item value="Workspace Main">Workspace Main</Select.Item>
                  </Select.Content>
                </Select.Root>
              </div>
            </div>

            {#if date}
              {#if loadingSlots}
                <div class="text-sm text-muted-foreground py-3 text-center">Loading slots...</div>
              {:else if availableSlots.length === 0}
                <div class="text-sm text-destructive py-3 text-center">No slots available</div>
              {:else}
                <div class="grid gap-2">
                  <Label>Time Slots</Label>
                  <div class="grid grid-cols-3 gap-2 max-h-[200px] overflow-y-auto p-1">
                    {#each availableSlots as slot}
                      {@const slotKey = `${slot.start_time} - ${slot.end_time}`}
                      {@const isSelected = selectedTimes.includes(slotKey)}
                      {@const isPrime = slot.type === 'PRIMETIME'}
                      <button
                        type="button"
                        class={cn(
                          "relative px-2 py-2 rounded text-xs border transition-all text-left",
                          isSelected && "border-primary bg-primary/10 font-medium",
                          !isSelected && "border-border hover:border-primary/50"
                        )}
                        onclick={() => toggleTimeSlot(slot)}
                      >
                        <div class="font-medium">{slot.start_time.substring(0, 5)}-{slot.end_time.substring(0, 5)}</div>
                        {#if isPrime}
                          <span class="absolute top-0.5 right-0.5 px-1 py-0.5 text-[9px] font-bold bg-yellow-100 text-yellow-800 rounded">PRIME</span>
                        {/if}
                      </button>
                    {/each}
                  </div>
                  <p class="text-xs text-muted-foreground">💡 Primetime needs approval</p>
                </div>
              {/if}

              <div class="grid grid-cols-2 gap-3">
                <div class="grid gap-2">
                  <Label for="start-{id}">Start</Label>
                  <Input id="start-{id}" type="time" bind:value={startTime} onchange={handleCustomTimeChange} />
                </div>
                <div class="grid gap-2">
                  <Label for="end-{id}">End</Label>
                  <Input id="end-{id}" type="time" bind:value={endTime} onchange={handleCustomTimeChange} />
                </div>
              </div>

              {#if totalHours > 0}
                <div class="p-2 rounded bg-primary/5 border text-sm">
                  <strong>{totalHours} hrs</strong> × ₱500 = <strong>₱{totalCost.toLocaleString()}</strong>
                </div>
              {/if}
            {/if}
          </div>

        {:else if step === 2}
          <div class="space-y-2">
            <p class="text-sm text-muted-foreground">Optional add-ons</p>
            <label class="flex items-center gap-2 text-sm">
              <input type="checkbox" value="projector" bind:group={selectedAddons} />
              Projector (₱200)
            </label>
            <label class="flex items-center gap-2 text-sm">
              <input type="checkbox" value="whiteboard" bind:group={selectedAddons} />
              Whiteboard (₱100)
            </label>
            <label class="flex items-center gap-2 text-sm">
              <input type="checkbox" value="sound" bind:group={selectedAddons} />
              Sound System (₱300)
            </label>
          </div>

        {:else}
          <div class="space-y-2">
            <h3 class="font-semibold text-sm">Summary</h3>
            <div class="grid gap-1 text-sm">
              <div class="flex justify-between"><span class="text-muted-foreground">Name:</span><span>{bookingName}</span></div>
              <div class="flex justify-between"><span class="text-muted-foreground">Date:</span><span>{date}</span></div>
              <div class="flex justify-between"><span class="text-muted-foreground">Time:</span><span>{startTime}-{endTime}</span></div>
              <div class="flex justify-between"><span class="text-muted-foreground">Space:</span><span>{space}</span></div>
              {#if selectedAddons.length > 0}
                <div class="flex justify-between"><span class="text-muted-foreground">Add-ons:</span><span class="text-xs">{selectedAddons.join(', ')}</span></div>
              {/if}
              <div class="flex justify-between pt-2 border-t font-semibold"><span>Total:</span><span>₱{totalCost.toLocaleString()}</span></div>
            </div>
          </div>
        {/if}

        {#if errorMessage}
          <div class="p-2 rounded bg-destructive/10 border text-sm text-destructive">{errorMessage}</div>
        {/if}
      </div>

      <div class="flex justify-between mt-2">
        {#if step > 1}
          <Button variant="outline" onclick={prevStep} size="sm">Previous</Button>
        {:else}
          <div></div>
        {/if}

        {#if step < 3}
          <Button onclick={nextStep} disabled={step === 1 && !canProceedStep1} size="sm">Next</Button>
        {:else}
          <Button onclick={handleConfirm} disabled={loading} size="sm">
            {loading ? 'Processing...' : 'Confirm'}
          </Button>
        {/if}
      </div>
    </Dialog.Content>
  </Dialog.Root>

{:else}
  <!-- ===================== MOBILE VERSION ===================== -->
  <Drawer.Root bind:open>
    <Drawer.Trigger class={buttonVariants({ variant: "outline" })}>New Reservation</Drawer.Trigger>
    <Drawer.Content>
      <Drawer.Header class="text-left">
        <Drawer.Title>New Reservation</Drawer.Title>
        <Drawer.Description>
          <div class="flex gap-2 text-xs mt-1">
            {#each stepTitles as s, i}
              <span class={s.active ? 'font-bold' : 'text-muted-foreground'}>{s.title}</span>
              {#if i < 2}<span>›</span>{/if}
            {/each}
          </div>
        </Drawer.Description>
      </Drawer.Header>

      <div class="px-4 space-y-3 max-h-[60vh] overflow-y-auto">
        {#if step === 1}
          <div class="grid gap-3">
            <div class="grid gap-2">
              <Label>Booking Name</Label>
              <Input placeholder="Build Day" bind:value={bookingName} />
            </div>
            <div class="grid gap-2">
              <Label>Date</Label>
              <Popover.Root>
                <Popover.Trigger class={cn(buttonVariants({ variant: "outline" }), "w-full justify-start", !value && "text-muted-foreground")}>
                  <CalendarIcon class="mr-2 h-4 w-4" />
                  {value ? df.format(value.toDate(getLocalTimeZone())) : "Pick"}
                </Popover.Trigger>
                <Popover.Content class="w-auto p-0">
                  <Calendar.Calendar type="single" bind:value fixedWeeks />
                </Popover.Content>
              </Popover.Root>
            </div>
            <div class="grid gap-2">
              <Label>Space</Label>
              <Select.Root type="single" bind:value={space}>
                <Select.Trigger class="w-full"><span>{space}</span></Select.Trigger>
                <Select.Content>
                  <Select.Item value="Great Hall">Great Hall</Select.Item>
                  <Select.Item value="Recording Studio">Recording Studio</Select.Item>
                  <Select.Item value="Workspace Main">Workspace Main</Select.Item>
                </Select.Content>
              </Select.Root>
            </div>
            {#if date && availableSlots.length > 0}
              <div class="grid gap-2">
                <Label>Time</Label>
                <div class="grid grid-cols-2 gap-2 max-h-[150px] overflow-y-auto">
                  {#each availableSlots as slot}
                    {@const key = `${slot.start_time}-${slot.end_time}`}
                    {@const sel = selectedTimes.includes(key)}
                    <button type="button" class={cn("px-2 py-1.5 text-xs border rounded", sel && "bg-primary/10 border-primary")} onclick={() => toggleTimeSlot(slot)}>
                      {slot.start_time.substring(0,5)}-{slot.end_time.substring(0,5)}
                      {#if slot.type === 'PRIMETIME'}<span class="text-[8px] ml-1">⭐</span>{/if}
                    </button>
                  {/each}
                </div>
              </div>
            {/if}
            <div class="grid grid-cols-2 gap-2">
              <div class="grid gap-2">
                <Label>Start</Label>
                <Input type="time" bind:value={startTime} onchange={handleCustomTimeChange} />
              </div>
              <div class="grid gap-2">
                <Label>End</Label>
                <Input type="time" bind:value={endTime} onchange={handleCustomTimeChange} />
              </div>
            </div>
            {#if totalHours > 0}
              <div class="text-xs p-2 bg-primary/5 rounded">{totalHours}h × ₱500 = ₱{totalCost.toLocaleString()}</div>
            {/if}
          </div>
        {:else if step === 2}
          <div class="space-y-2">
            <label class="flex gap-2 text-sm"><input type="checkbox" value="projector" bind:group={selectedAddons} />Projector (₱200)</label>
            <label class="flex gap-2 text-sm"><input type="checkbox" value="whiteboard" bind:group={selectedAddons} />Whiteboard (₱100)</label>
            <label class="flex gap-2 text-sm"><input type="checkbox" value="sound" bind:group={selectedAddons} />Sound (₱300)</label>
          </div>
        {:else}
          <div class="space-y-2 text-sm">
            <div class="flex justify-between"><span>Name:</span><span>{bookingName}</span></div>
            <div class="flex justify-between"><span>Date:</span><span>{date}</span></div>
            <div class="flex justify-between"><span>Time:</span><span>{startTime}-{endTime}</span></div>
            <div class="flex justify-between font-semibold border-t pt-2"><span>Total:</span><span>₱{totalCost.toLocaleString()}</span></div>
          </div>
        {/if}
      </div>

      <Drawer.Footer class="pt-2">
        <div class="flex gap-2 w-full">
          {#if step > 1}<Button variant="outline" onclick={prevStep} class="flex-1" size="sm">Previous</Button>{/if}
          {#if step < 3}
            <Button onclick={nextStep} disabled={step === 1 && !canProceedStep1} class="flex-1" size="sm">Next</Button>
          {:else}
            <Button onclick={handleConfirm} disabled={loading} class="flex-1" size="sm">{loading ? 'Processing...' : 'Confirm'}</Button>
          {/if}
        </div>
        <Drawer.Close class={buttonVariants({ variant: "outline" })}>Cancel</Drawer.Close>
      </Drawer.Footer>
    </Drawer.Content>
  </Drawer.Root>
{/if}

{#if loading}
  <div class="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50">
    <div class="flex flex-col items-center gap-3">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
      <p class="text-sm">Processing...</p>
    </div>
  </div>
{/if}
