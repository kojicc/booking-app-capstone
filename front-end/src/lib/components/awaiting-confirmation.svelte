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
  <DialogContent class="max-w-sm !w-auto">
    <div class="flex flex-col items-center">
      <div class="rounded-full bg-yellow-100 p-4 mb-2">
        <svg width="48" height="48" fill="none" viewBox="0 0 48 48"><circle cx="24" cy="24" r="22" fill="#FEF3C7" stroke="#FDE68A" stroke-width="4"/><path d="M20 16h8v16h-8z" fill="#D97706"/></svg>
      </div>
      <div class="text-xl font-bold text-gray-800 text-center mb-1">Awaiting Confirmation</div>
      <div class="text-base text-gray-400 text-center mb-6">This booking is in primetime and requires admin approval. You will be notified when it's accepted.</div>
      <button class="w-full bg-primary-200-var hover:bg-primary-300-var text-white text-base font-medium rounded-md py-2 transition" type="button" onclick={onClose}>View Details</button>
    </div>
  </DialogContent>
</Dialog>
