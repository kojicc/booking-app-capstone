<script lang="ts">
interface Props {
  selectedAddons: string[];
}

export let selectedAddons: string[] = [];

const availableAddons = [
  { label: 'Unlimited Coffee', value: 'coffee' },
  { label: 'Microwave Use', value: 'microwave' },
  { label: 'Internet', value: 'internet' },
  { label: 'Shower', value: 'shower' }
];
</script>

<div class="pt-2 pb-6">
  <div class="block text-base font-medium mb-4 ml-1">Select Add-ons:</div>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
    {#each availableAddons as addon}
      <label class="flex items-center justify-between border border-gray-200 rounded-lg px-4 py-3 bg-white hover:border-primary-200 transition cursor-pointer">
        <div class="flex items-center gap-2">
          <input 
            type="checkbox" 
            class="accent-primary-500 w-5 h-5" 
            bind:group={selectedAddons} 
            value={addon.value} 
          />
          <span class="text-gray-700 text-base">{addon.label}</span>
        </div>
        <span class="text-gray-600 font-medium text-base">+PHP 40.00</span>
      </label>
    {/each}
  </div>
</div>