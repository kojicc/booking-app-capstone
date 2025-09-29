<script lang="ts">
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "$lib/components/ui/dialog/index.js";
import DateTimeStep from "$lib/components/reservation-steps/bookslot.svelte";
import AddonsStep from "$lib/components/reservation-steps/addon.svelte";
import ReviewStep from "$lib/components/reservation-steps/review-form.svelte";


interface Props {
  open?: boolean;
  onClose?: () => void;
  onSuccess?: () => void;
}

let { open = $bindable(false), onClose, onSuccess }: Props = $props();

let step = $state(1);
let loading = $state(false);

// Form state - centralized here and passed to components
let bookingName = $state("");
let date = $state("");
let space = $state("Workspace Main");
let selectedAddons = $state<string[]>([]);
let startTime = $state("");
let endTime = $state("");

// Reactive calculations (runes-compatible)
let totalHours = $state(0);
let totalCost = $state(0);

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
  setTimeout(() => {
    loading = false;
    // close the modal and notify parent to show success
    closeModal();
    onSuccess?.();
  }, 1200);
}

// Reset step when modal closes
$effect(() => {
  if (!open) step = 1;
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

<Dialog bind:open>
  <DialogContent class="max-w-4xl">
    <DialogHeader>
      <DialogTitle>New Reservation</DialogTitle>
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
    </DialogHeader>

    {#if step === 1}
      <DateTimeStep
        bind:bookingName
        bind:date
        bind:space
        bind:startTime
        bind:endTime
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

    <DialogFooter class="mt-4 flex justify-between">
      <div>
        <button 
          type="button" 
          class="bg-secondary text-foreground font-medium rounded-lg px-4 py-2 border border-border shadow-sm transition-colors" 
          onclick={closeModal}
        >
          Cancel
        </button>
      </div>
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
          <button 
            type="button" 
            class="bg-primary-200-var hover:bg-primary-300-var text-white font-medium rounded-lg px-4 py-2 flex items-center gap-2 text-sm shadow transition-colors" 
            onclick={nextStep}
          >
            Next
          </button>
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
    </DialogFooter>

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

    <!-- Success modal is handled by the parent page via onSuccess -->
  </DialogContent>
</Dialog>