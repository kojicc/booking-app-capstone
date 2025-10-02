<script lang="ts">
import * as Dialog from "$lib/components/ui/dialog/index.js";
import DateTimeStep from "$lib/components/reservation-steps/bookslot.svelte";
import AddonsStep from "$lib/components/reservation-steps/addon.svelte";
import ReviewStep from "$lib/components/reservation-steps/review-form.svelte";
import { createReservation } from "$lib/api/reservation";
import { toast } from 'svelte-sonner';
import type {Reservation} from '$lib/api/reservation';
  import { Button, buttonVariants } from "$lib/components/ui/button/index.js";
import { clearOpenSignal } from '$lib/stores/reservation';



interface Props {
  open?: boolean;
  onClose?: () => void;
  // onSuccess receives optional bookedTime and a primetime flag
  onSuccess?: (bookedTime?: string | Date | number | null, primetime?: boolean) => void;
}

let { open = $bindable(false), onClose, onSuccess }: Props = $props();

let step = $state(1);
let loading = $state(false);
let errorMessage = $state('');

// Form state - centralized here and passed to components

let formData: Reservation | null = null;


let bookingName = $state("");
let isPrimetime = $state(false);
let date = $state("");
let space = $state("Workspace Main");
let selectedAddons = $state<string[]>([]);
let startTime = $state("");
let endTime = $state("");
let primetimeSelected = $state(false);

let totalHours = $state(0);
let totalCost = $state(0);

// Validation for Bookslot (step 1)
let canProceedStep1 = $state(false);

$effect(() => {
  // require bookingName, date, and a selected time range (start and end)
  canProceedStep1 = !!(bookingName && bookingName.toString().trim().length > 0 && date && startTime && endTime && totalHours > 0);
});

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
  if (totalHours < 0) totalHours += 24; // handle overnight
  totalCost = totalHours * 500;
});

function nextStep() {
  // If we're on the first step (bookslot) enforce validation
  if (step === 1 && !canProceedStep1) {
    // no-op; UX shows disabled Next button and a helper message
    return;
  }
  if (step < 3) step += 1;
}

function prevStep() {
  if (step > 1) step -= 1;
}

function closeModal() {
  open = false;  
  step = 1;
  onClose?.();
}

function handleConfirm() {
  loading = true;

  // Build payload
  const payload = {
    bookingName,
    date,
    space,
    startTime,
    endTime,
    addons: selectedAddons,
    totalHours,
    totalCost,
    isPrimetime
  };

  // Try to call backend if configured, otherwise fallback to local mock
  (async () => {
    try {
      // Try calling the real backend API
      const created = await createReservation({
        user: bookingName, // adapt when you have user id
        booking_name: bookingName,
        date,
        start_time: startTime,
        end_time: endTime,
        reservation_type: isPrimetime ? "PRIMETIME" : "FREE_FOR_ALL",
        notes: ''
      });

      // success path - show toast instead of modal
      const isPrimetimeCheck = isPrimetime || primetimeSelected;
      const message = isPrimetimeCheck 
        ? 'Primetime reservation created! Waiting for admin approval.' 
        : 'Reservation created successfully!';
      toast.success(message);
      onSuccess?.(created.start_time, primetimeSelected);
      closeModal(); // Close the reservation modal after success
    } catch (err: any) {
      console.error('Booking failed:', err);
      let serverBody = err?.body || err?.message || '';
      // If the body is JSON, try to extract useful messages
      try {
        if (typeof serverBody === 'string' && serverBody.trim().length > 0) {
          const parsed = JSON.parse(serverBody);
          // If the backend returns an object with field errors, join them
          if (typeof parsed === 'object' && parsed !== null) {
            const messages: string[] = [];
            for (const k of Object.keys(parsed)) {
              const v = parsed[k];
              if (Array.isArray(v)) messages.push(`${k}: ${v.join(', ')}`);
              else if (typeof v === 'string') messages.push(`${k}: ${v}`);
              else messages.push(`${k}: ${JSON.stringify(v)}`);
            }
            if (messages.length) serverBody = messages.join(' • ');
          }
        }
      } catch (parseErr) {
        // not JSON, ignore
      }

      errorMessage = serverBody ? String(serverBody) : 'Booking failed. Please try again.';
      toast.error(errorMessage);
    } finally {
      loading = false;
    }
  })();
}

// Reset step when modal closes
$effect(() => {
  if (!open) step = 1;
});

$effect(() => {
  if ($clearOpenSignal) {
    // If parent asked to clear open signals, make sure modal is closed and reset
    open = false;
    step = 1;
    errorMessage = '';
  }
});

// Get step title for breadcrumb
function getStepTitle(stepNum: number): string {
  switch (stepNum) {
    case 1: return 'Date and Time';
    case 2: return 'Add-ons';
    case 3: return 'Review';
    default: return '';
  }
}

let stepTitles = $state([{ num: 1, title: getStepTitle(1), active: false }, { num: 2, title: getStepTitle(2), active: false }, { num: 3, title: getStepTitle(3), active: false }]);

$effect(() => {
  // update active state when `step` changes
  stepTitles = [1, 2, 3].map(stepNum => ({
    num: stepNum,
    title: getStepTitle(stepNum),
    active: step === stepNum
  }));
});
</script>

<Dialog.Root bind:open>
  <Dialog.Trigger class={buttonVariants({ variant: "outline" })}
    >New Reservation</Dialog.Trigger
  >
  <Dialog.Content class="sm:max-w-[700px] max-h-[90vh] flex flex-col p-6">
    <Dialog.Header class="flex-shrink-0 pb-4">
      <Dialog.Title>New Reservation</Dialog.Title>
      <div class="flex items-center gap-2 mt-1 text-sm">
        {#each stepTitles as stepItem, i}
          <span class={stepItem.active ? 'font-bold text-gray-600' : 'text-gray-500'}>
            {stepItem.title}
          </span>
          {#if i < stepTitles.length - 1}
            <span class="mx-1 text-gray-400">&gt;</span>
          {/if}
        {/each}
      </div>
    </Dialog.Header>

    <div class="flex-1 overflow-y-auto -mx-6 px-6">
      {#if step === 1}
        <DateTimeStep
          bind:bookingName
          bind:date
          bind:space
          bind:startTime
          bind:endTime
          bind:primetimeSelected
          {totalHours}
          {totalCost}
        />
      {:else if step === 2}
        <AddonsStep bind:selectedAddons />
      {:else}
        <ReviewStep
          {bookingName}
          {date}
          {space}
          {startTime}
          {endTime}
          {selectedAddons}
          {totalHours}
          {totalCost}
        />
      {/if}
    </div>

    <Dialog.Footer class="mt-4 flex justify-between">
     
      <div class="flex gap-2">
        {#if step > 1}
          <button 
            type="button" 
            class="bg-secondary text-foreground font-medium rounded-lg px-4 py-2 border border-border shadow-sm transition-colors" 
            onclick={prevStep}
          >
            Previous
          </button>
        {/if}
        {#if step < 3}
          <div class="flex flex-col items-end">
            <button 
              type="button" 
              class={
                'bg-primary-200-var text-white font-medium rounded-lg px-4 py-2 flex items-center gap-2 text-sm shadow transition-colors ' +
                (step === 1 && !canProceedStep1 ? 'opacity-60 cursor-not-allowed' : 'hover:bg-primary-300-var')
              }
              onclick={nextStep}
              disabled={step === 1 && !canProceedStep1}
            >
              Next
            </button>
            {#if step === 1 && !canProceedStep1}
              <div class="text-xs text-red-600 mt-2">Please fill booking name, select a date and a time range before continuing.</div>
            {/if}
          </div>
        {:else}
          <button 
            type="button" 
            class="bg-primary-200-var hover:bg-primary-300-var text-white font-medium rounded-lg px-4 py-2 flex items-center gap-2 text-sm shadow transition-colors" 
            onclick={handleConfirm}
          >
            Confirm Booking
          </button>
        {/if}
      </div>
    </Dialog.Footer>

    {#if errorMessage}
      <div class="mt-3 text-sm text-red-600 px-4">
        {errorMessage}
      </div>
    {/if}

    {#if loading}
      <div class="absolute inset-0 flex items-center justify-center bg-white bg-opacity-80 z-50 rounded-xl">
        <div class="flex flex-col items-center gap-4">
          <svg class="animate-spin" width="48" height="48" fill="none" viewBox="0 0 48 48">
            <circle class="opacity-20" cx="24" cy="24" r="20" stroke="#6366F1" stroke-width="6" />
            <path d="M44 24a20 20 0 0 0-20-20" stroke="#6366F1" stroke-width="6" stroke-linecap="round" />
          </svg>
          <div class="text-lg text-gray-500 mt-2">Processing your booking...</div>
        </div>
      </div>
    {/if}
  </Dialog.Content>
</Dialog.Root>