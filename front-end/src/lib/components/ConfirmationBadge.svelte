<script lang="ts">
  import { Badge } from "$lib/components/ui/badge";
  
  type ReservationStatus = 'confirmed' | 'pending' | 'rejected';
  
  interface Status {
    class: string;
    label: string;
  }
  let {status}: {status: ReservationStatus;} = $props();
  
  const statusConfig: Record<ReservationStatus, Status> = {
    confirmed: {
      class: "bg-green-500/10 text-green-200",
      label: "Confirmed"
    },
    pending: {
      class: "bg-yellow-500/10 text-yellow-200", 
      label: "Pending"
    },
    rejected: {
      class: "bg-red-500/10 text-red-200",
      label: "Rejected"
    }
  };
  
  let config = $state(statusConfig[status] || statusConfig.pending);
</script>

<Badge class={config.class}>
  {config.label}
</Badge>