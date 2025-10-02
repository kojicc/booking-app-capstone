<script lang="ts">
  import { Badge } from "$lib/components/ui/badge";
  
  type ReservationStatus = 'confirmed' | 'pending' | 'rejected' | 'cancelled' | 'completed';
  
  interface Status {
    class: string;
    label: string;
  }
  let {status}: {status: ReservationStatus;} = $props();
  
  const statusConfig: Record<ReservationStatus, Status> = {
    confirmed: {
      class: "bg-green-500/10 text-green-600",
      label: "Confirmed"
    },
    pending: {
      class: "bg-yellow-500/10 text-yellow-600", 
      label: "Pending"
    },
    rejected: {
      class: "bg-red-500/10 text-red-600",
      label: "Rejected"
    },
    cancelled: {
      class: "bg-gray-500/10 text-gray-600",
      label: "Cancelled"
    },
    completed: {
      class: "bg-blue-500/10 text-blue-600",
      label: "Completed"
    }
  };
  
  let config = $state(statusConfig[status] || statusConfig.pending);
</script>

<Badge class={config.class}>
  {config.label}
</Badge>