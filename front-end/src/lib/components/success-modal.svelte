<script lang="ts">
import { Dialog, DialogContent } from "$lib/components/ui/dialog/index.js";

interface Props {
  open?: boolean;
  onClose?: () => void;
  bookedTime?: string | Date | number | null;
}

let { open = $bindable(true), onClose = () => {}, bookedTime = null }: Props = $props();
</script>

<Dialog bind:open>
  <DialogContent class="max-w-md !w-auto">
    <div class="flex flex-col items-center">
      <div class="rounded-full bg-green-100 p-4 mb-2">
        <svg width="48" height="48" fill="none" viewBox="0 0 48 48"><circle cx="24" cy="24" r="22" fill="#D1FADF" stroke="#A7F3D0" stroke-width="4"/><path d="M16 24l6 6 10-12" stroke="#22C55E" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </div>
      <div class="text-xl font-bold text-gray-800 text-center mb-1">Booking Confirmed</div>
      <div class="text-base text-gray-400 text-center mb-6">Your reservation has been confirmed</div>
      <button class="w-full bg-primary-200-var hover:bg-primary-300-var text-white text-base font-medium rounded-md py-2 transition" type="button" onclick={onClose}>View Details</button>
    </div>
  </DialogContent>
</Dialog>