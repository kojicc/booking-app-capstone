<script lang="ts">
// ===================== IMPORTS =====================
import { MediaQuery } from "svelte/reactivity";
import * as Dialog from "$lib/components/ui/dialog/index.js";
import * as Drawer from "$lib/components/ui/drawer/index.js";
import * as Select from "$lib/components/ui/select";
import * as AlertDialog from "$lib/components/ui/alert-dialog";
import { Button, buttonVariants } from "$lib/components/ui/button/index.js";
import { Label } from "$lib/components/ui/label/index.js";
import { Input } from "$lib/components/ui/input/index.js";
import { ScrollArea } from "$lib/components/ui/scroll-area";
import * as Table from "$lib/components/ui/table";
import { 
  getPrimeTimeSettings, 
  createPrimeTime, 
  updatePrimeTime, 
  deletePrimeTime,
  type PrimeTimeSettings 
} from "$lib/api/reservation";
import { toast } from 'svelte-sonner';
import { Trash2, Edit, Plus } from 'lucide-svelte';
import { primetimeDialogOpen, resetPrimetimeDialog } from '$lib/stores/primetime';

// ===================== PROPS =====================
interface Props {
  open?: boolean;
  onClose?: () => void;
  onSuccess?: () => void;
}

let { open = $bindable(false), onClose, onSuccess }: Props = $props();

// ===================== RESPONSIVE DETECTION =====================
const isDesktop = new MediaQuery("(min-width: 768px)");
const id = crypto.randomUUID();

// ===================== STATE =====================
let primeTimeSettings = $state<PrimeTimeSettings[]>([]);
let loading = $state(false);
let editMode = $state(false);
let editingId = $state<number | null>(null);

// Delete confirmation state
let showDeleteDialog = $state(false);
let settingToDelete = $state<number | null>(null);

// Form fields para sa bagong o i-edit na primetime setting
let selectedWeekday = $state("0"); // String para sa Select component
let startTime = $state("18:00");
let endTime = $state("21:00");
let isActive = $state(true);

// Weekday names para sa dropdown at display
const WEEKDAYS = [
  { value: "0", label: 'Monday' },
  { value: "1", label: 'Tuesday' },
  { value: "2", label: 'Wednesday' },
  { value: "3", label: 'Thursday' },
  { value: "4", label: 'Friday' },
  { value: "5", label: 'Saturday' },
  { value: "6", label: 'Sunday' }
];

// ===================== LIFECYCLE =====================
// Load existing settings pag nag-open ang dialog
$effect(() => {
  if (open) {
    loadSettings();
  }
});

// Listen to global open signal and open the dialog when requested
$effect(() => {
  const unsub = primetimeDialogOpen.subscribe((val) => {
    if (val) {
      open = true;
      // Reset so repeated opens work
      resetPrimetimeDialog();
    }
  });

  return unsub;
});

// ===================== DATA LOADING =====================
async function loadSettings() {
  loading = true;
  try {
    primeTimeSettings = await getPrimeTimeSettings();
  } catch (error) {
    console.error('Error loading primetime settings:', error);
    toast.error('Failed to load primetime settings');
  } finally {
    loading = false;
  }
}

// ===================== FORM ACTIONS =====================
// Reset form to initial state (para sa bagong entry)
function resetForm() {
  editMode = false;
  editingId = null;
  selectedWeekday = "0";
  startTime = "18:00";
  endTime = "21:00";
  isActive = true;
}

// Mag-switch to edit mode at i-populate yung form
function startEdit(setting: PrimeTimeSettings) {
  editMode = true;
  editingId = setting.id;
  selectedWeekday = setting.weekday.toString(); // Convert to string
  // Remove seconds from time strings
  startTime = setting.start_time.substring(0, 5);
  endTime = setting.end_time.substring(0, 5);
  isActive = setting.is_active;
}

// I-save ang bagong o naka-edit na primetime setting
async function handleSave() {
  // Validation: end time dapat mas late kaysa start time
  const [startHour, startMin] = startTime.split(':').map(Number);
  const [endHour, endMin] = endTime.split(':').map(Number);
  
  if (startHour * 60 + startMin >= endHour * 60 + endMin) {
    toast.error('End time must be after start time');
    return;
  }

  loading = true;
  try {
    const payload = {
      weekday: parseInt(selectedWeekday), // Convert back to number
      start_time: startTime + ':00', // Add seconds
      end_time: endTime + ':00',
      is_active: isActive
    };

    if (editMode && editingId !== null) {
      // Update existing
      await updatePrimeTime(editingId, payload);
      toast.success('Primetime setting updated successfully');
    } else {
      // Create new
      await createPrimeTime(payload);
      toast.success('Primetime setting created successfully');
    }

    // Reload at reset form
    await loadSettings();
    resetForm();
    onSuccess?.(); // Call parent refresh callback
  } catch (error: any) {
    console.error('Error saving primetime setting:', error);
    toast.error(error?.message || 'Failed to save primetime setting');
  } finally {
    loading = false;
  }
}

// Tanggalin ang primetime setting
function showDeleteConfirmation(id: number) {
  settingToDelete = id;
  showDeleteDialog = true;
}

async function confirmDelete() {
  if (settingToDelete === null) return;

  loading = true;
  try {
    await deletePrimeTime(settingToDelete);
    toast.success('Primetime setting deleted successfully');
    await loadSettings();
    showDeleteDialog = false;
    settingToDelete = null;
  } catch (error: any) {
    console.error('Error deleting primetime setting:', error);
    toast.error(error?.message || 'Failed to delete primetime setting');
  } finally {
    loading = false;
  }
}

function cancelDelete() {
  showDeleteDialog = false;
  settingToDelete = null;
}

// ===================== HELPER FUNCTIONS =====================
function getWeekdayLabel(weekday: number | string): string {
  const weekdayNum = typeof weekday === 'string' ? parseInt(weekday) : weekday;
  return WEEKDAYS.find(w => w.value === weekdayNum.toString())?.label || 'Unknown';
}

function closeDialog() {
  resetForm();
  open = false;
  onClose?.();
}

// Public API for parent components to open/close the dialog programmatically
export function openDialog() {
  open = true;
}

export function closeDialogPublic() {
  closeDialog();
}
</script>

<!-- ===================== RESPONSIVE LAYOUT ===================== -->
{#if isDesktop.current}
  <!-- DESKTOP VERSION - Dialog -->
  <Dialog.Root bind:open>
    <Dialog.Content class="sm:max-w-[700px] max-h-[90vh] flex flex-col">
      <Dialog.Header>
        <Dialog.Title>Primetime Management</Dialog.Title>
        <Dialog.Description>
          Set special hours na need ng admin approval para sa reservations
        </Dialog.Description>
      </Dialog.Header>

      <ScrollArea class="flex-1 -mx-6 px-6">
        <div class="space-y-6 py-4">
          <!-- FORM SECTION -->
          <div class="border rounded-lg p-4 space-y-4">
            <h3 class="font-semibold text-sm">
              {editMode ? 'Edit Primetime Setting' : 'Add New Primetime Setting'}
            </h3>

            <div class="grid grid-cols-2 gap-4">
              <div class="grid gap-2">
                <Label for="weekday-{id}">Day of Week</Label>
                <Select.Root type="single" bind:value={selectedWeekday}>
                  <Select.Trigger id="weekday-{id}">
                    <span>{getWeekdayLabel(selectedWeekday)}</span>
                  </Select.Trigger>
                  <Select.Content>
                    {#each WEEKDAYS as day}
                      <Select.Item value={day.value}>{day.label}</Select.Item>
                    {/each}
                  </Select.Content>
                </Select.Root>
              </div>

              <div class="grid gap-2">
                <Label>Status</Label>
                <div class="flex items-center gap-2 h-10">
                  <input type="checkbox" id="active-{id}" bind:checked={isActive} class="h-4 w-4" />
                  <Label for="active-{id}" class="cursor-pointer">
                    {isActive ? 'Active' : 'Inactive'}
                  </Label>
                </div>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div class="grid gap-2">
                <Label for="start-time-{id}">Start Time</Label>
                <Input
                  id="start-time-{id}"
                  type="time"
                  bind:value={startTime}
                />
              </div>

              <div class="grid gap-2">
                <Label for="end-time-{id}">End Time</Label>
                <Input
                  id="end-time-{id}"
                  type="time"
                  bind:value={endTime}
                />
              </div>
            </div>

            <div class="flex gap-2">
              <Button onclick={handleSave} disabled={loading}>
                {editMode ? 'Update' : 'Add'} Setting
              </Button>
              {#if editMode}
                <Button variant="outline" onclick={resetForm}>
                  Cancel Edit
                </Button>
              {/if}
            </div>
          </div>

          <!-- EXISTING SETTINGS TABLE -->
          <div class="space-y-2">
            <h3 class="font-semibold text-sm">Existing Primetime Settings</h3>
            
            {#if loading && primeTimeSettings.length === 0}
              <div class="text-center py-8 text-muted-foreground">
                Loading settings...
              </div>
            {:else if primeTimeSettings.length === 0}
              <div class="text-center py-8 text-muted-foreground">
                No primetime settings yet. Add one above to get started.
              </div>
            {:else}
              <div class="border rounded-lg">
                <Table.Root>
                  <Table.Header>
                    <Table.Row>
                      <Table.Head>Day</Table.Head>
                      <Table.Head>Time Range</Table.Head>
                      <Table.Head>Status</Table.Head>
                      <Table.Head class="text-right">Actions</Table.Head>
                    </Table.Row>
                  </Table.Header>
                  <Table.Body>
                    {#each primeTimeSettings as setting}
                      <Table.Row>
                        <Table.Cell class="font-medium">
                          {setting.weekday_display || getWeekdayLabel(setting.weekday)}
                        </Table.Cell>
                        <Table.Cell>
                          {setting.start_time.substring(0, 5)} - {setting.end_time.substring(0, 5)}
                        </Table.Cell>
                        <Table.Cell>
                          <span class={
                            setting.is_active 
                              ? 'px-2 py-1 text-xs rounded-full bg-green-100 text-green-800' 
                              : 'px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800'
                          }>
                            {setting.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </Table.Cell>
                        <Table.Cell class="text-right">
                          <div class="flex justify-end gap-2">
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              onclick={() => startEdit(setting)}
                            >
                              <Edit class="h-4 w-4" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              onclick={() => showDeleteConfirmation(setting.id)}
                              class="text-destructive hover:text-destructive"
                            >
                              <Trash2 class="h-4 w-4" />
                            </Button>
                          </div>
                        </Table.Cell>
                      </Table.Row>
                    {/each}
                  </Table.Body>
                </Table.Root>
              </div>
            {/if}
          </div>
        </div>
      </ScrollArea>

      <div class="flex justify-end mt-4">
        <Button variant="outline" onclick={closeDialog}>Close</Button>
      </div>
    </Dialog.Content>
  </Dialog.Root>

{:else}
  <!-- MOBILE VERSION - Drawer -->
  <Drawer.Root bind:open>
    <Drawer.Content>
      <Drawer.Header class="text-left">
        <Drawer.Title>Primetime Management</Drawer.Title>
        <Drawer.Description>
          Manage special hours for reservations
        </Drawer.Description>
      </Drawer.Header>

      <ScrollArea class="max-h-[70vh] px-4">
        <div class="space-y-6 pb-4">
          <!-- FORM SECTION -->
          <div class="border rounded-lg p-3 space-y-3">
            <h3 class="font-semibold text-sm">
              {editMode ? 'Edit' : 'Add'} Setting
            </h3>

            <div class="grid gap-3">
              <div class="grid gap-2">
                <Label for="weekday-mobile-{id}">Day</Label>
                <Select.Root type="single" bind:value={selectedWeekday}>
                  <Select.Trigger id="weekday-mobile-{id}" class="w-full">
                    <span>{getWeekdayLabel(selectedWeekday)}</span>
                  </Select.Trigger>
                  <Select.Content>
                    {#each WEEKDAYS as day}
                      <Select.Item value={day.value}>{day.label}</Select.Item>
                    {/each}
                  </Select.Content>
                </Select.Root>
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div class="grid gap-2">
                  <Label for="start-mobile-{id}">Start</Label>
                  <Input
                    id="start-mobile-{id}"
                    type="time"
                    bind:value={startTime}
                  />
                </div>

                <div class="grid gap-2">
                  <Label for="end-mobile-{id}">End</Label>
                  <Input
                    id="end-mobile-{id}"
                    type="time"
                    bind:value={endTime}
                  />
                </div>
              </div>

              <div class="flex items-center gap-2">
                <input type="checkbox" id="active-mobile-{id}" bind:checked={isActive} class="h-4 w-4" />
                <Label for="active-mobile-{id}">
                  {isActive ? 'Active' : 'Inactive'}
                </Label>
              </div>

              <div class="flex gap-2">
                <Button onclick={handleSave} disabled={loading} class="flex-1">
                  {editMode ? 'Update' : 'Add'}
                </Button>
                {#if editMode}
                  <Button variant="outline" onclick={resetForm} class="flex-1">
                    Cancel
                  </Button>
                {/if}
              </div>
            </div>
          </div>

          <!-- EXISTING SETTINGS LIST -->
          <div class="space-y-2">
            <h3 class="font-semibold text-sm">Current Settings</h3>
            
            {#if loading && primeTimeSettings.length === 0}
              <div class="text-center py-6 text-muted-foreground text-sm">
                Loading...
              </div>
            {:else if primeTimeSettings.length === 0}
              <div class="text-center py-6 text-muted-foreground text-sm">
                No settings yet
              </div>
            {:else}
              <div class="space-y-2">
                {#each primeTimeSettings as setting}
                  <div class="border rounded-lg p-3 space-y-2">
                    <div class="flex justify-between items-start">
                      <div>
                        <div class="font-medium text-sm">
                          {setting.weekday_display || getWeekdayLabel(setting.weekday)}
                        </div>
                        <div class="text-sm text-muted-foreground">
                          {setting.start_time.substring(0, 5)} - {setting.end_time.substring(0, 5)}
                        </div>
                      </div>
                      <span class={
                        setting.is_active 
                          ? 'px-2 py-0.5 text-xs rounded-full bg-green-100 text-green-800' 
                          : 'px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-800'
                      }>
                        {setting.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                    <div class="flex gap-2">
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onclick={() => startEdit(setting)}
                        class="flex-1"
                      >
                        <Edit class="h-3 w-3 mr-1" />
                        Edit
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onclick={() => showDeleteConfirmation(setting.id)}
                        class="flex-1 text-destructive hover:text-destructive"
                      >
                        <Trash2 class="h-3 w-3 mr-1" />
                        Delete
                      </Button>
                    </div>
                  </div>
                {/each}
              </div>
            {/if}
          </div>
        </div>
      </ScrollArea>

      <Drawer.Footer class="pt-2">
        <Drawer.Close class={buttonVariants({ variant: "outline" })}>
          Close
        </Drawer.Close>
      </Drawer.Footer>
    </Drawer.Content>
  </Drawer.Root>
{/if}

<!-- Delete Confirmation Dialog -->
<AlertDialog.Root bind:open={showDeleteDialog}>
  <AlertDialog.Content>
    <AlertDialog.Header>
      <AlertDialog.Title>Delete Primetime Setting?</AlertDialog.Title>
      <AlertDialog.Description>
        This action cannot be undone. This will permanently delete the primetime setting.
      </AlertDialog.Description>
    </AlertDialog.Header>
    <AlertDialog.Footer>
      <AlertDialog.Cancel onclick={cancelDelete}>Cancel</AlertDialog.Cancel>
      <AlertDialog.Action onclick={confirmDelete} class="bg-destructive text-destructive-foreground hover:bg-destructive/90">
        Delete
      </AlertDialog.Action>
    </AlertDialog.Footer>
  </AlertDialog.Content>
</AlertDialog.Root>
