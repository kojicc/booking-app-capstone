<script lang="ts">
interface Props {
  bookingName: string;
  date: string;
  space: string;
  startTime: string;
  endTime: string;
  selectedAddons: string[];
  totalHours: number;
  totalCost: number;
}

const {
  bookingName,
  date,
  space,
  startTime,
  endTime,
  selectedAddons,
  totalHours,
  totalCost
}: Props = $props();

// Helper to get add-on label from value
function addonLabel(val: string): string {
  const map: Record<string, string> = {
    coffee: 'Unlimited Coffee',
    microwave: 'Microwave Use',
    internet: 'Internet',
    shower: 'Shower',
    water: 'Water',
  };
  return map[val] || val;
}

// Computed values (runes-friendly concrete state)
let formattedDate = $state('Not selected');
let timeRange = $state('Not selected');
let addonCost = $state(0);
let grandTotal = $state(0);
let addonLabelsText = $state('None');

$effect(() => {
  formattedDate = !date
    ? 'Not selected'
    : new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });

  timeRange = (!startTime || !endTime) ? 'Not selected' : `${startTime} - ${endTime}`;

  addonCost = selectedAddons.length * 40;
  grandTotal = totalCost + addonCost;

  addonLabelsText = selectedAddons.length === 0 ? 'None' : selectedAddons.map(a => addonLabel(a)).join(', ');
});
</script>

<div class="pt-2 pb-6">
  <div class="text-lg font-semibold mb-6">Booking Summary</div>
  
  <div class="space-y-4">
    <!-- Basic Info Section -->
    <div class="flex justify-between items-center py-2">
      <span class="text-gray-600">Booking Name:</span>
      <span class="font-medium text-gray-900">{bookingName || 'Not specified'}</span>
    </div>
    
    <div class="flex justify-between items-center py-2">
      <span class="text-gray-600">Date:</span>
      <span class="font-medium text-gray-900">{formattedDate}</span>
    </div>
    
    <div class="flex justify-between items-center py-2">
      <span class="text-gray-600">Time:</span>
      <span class="font-medium text-gray-900">{timeRange}</span>
    </div>
    
    <div class="flex justify-between items-center py-2 pb-4">
      <span class="text-gray-600">Space:</span>
      <span class="font-medium text-gray-900">{space}</span>
    </div>
    
    <!-- Pricing Section -->
    <div class="border-t border-gray-200 pt-4 space-y-3">
      <div class="flex justify-between items-center">
        <span class="text-gray-600">Base Price:</span>
        <span class="font-medium text-gray-900">
          PHP 500 × {totalHours} hr{totalHours === 1 ? '' : 's'} = PHP {totalCost.toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </span>
      </div>
      
      <div class="flex justify-between items-start">
        <span class="text-gray-600">Add-ons:</span>
        <div class="text-right">
          {#if selectedAddons.length > 0}
            <div class="font-medium text-gray-900">{addonLabelsText}</div>
            <div class="text-sm text-gray-600">
              + PHP {addonCost.toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          {:else}
            <span class="font-medium text-gray-900">None</span>
          {/if}
        </div>
      </div>
    </div>
    
    <!-- Total Section -->
    <div class="border-t border-gray-300 pt-4 mt-6">
      <div class="flex justify-between items-center">
        <span class="text-xl font-bold text-gray-900">Total</span>
        <span class="text-xl font-bold text-gray-900">
          PHP {grandTotal.toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </span>
      </div>
    </div>
  </div>
</div>