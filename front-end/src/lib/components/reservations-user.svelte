<script lang="ts">
// Tester or sample content for reservation card
	import ReservationDetailCard from "$lib/components/ReservationDetailCard.svelte";
  const sampleReservation = {
      bookingName: 'Birthday ni Anne', 
      userWhoBooked: 'Vice Ganda', 
      bookingStatus: 'rejected', 
      bookingNumber: 'CLD09738PL', 
      date: 'October 5, 2025', 
      space: 'Recording Room', 
      startTime: '13:00', 
      endTime: '15:00', 
      addons: ['Water', 'Internet'],
      rejectionMessage: 'Please select another date'
    };
</script>

<div class="p-6">
  <h2 class="text-2xl font-bold mb-4">My Reservations</h2>
  <p class="text-sm text-gray-600 mb-6">View your confirmed and pending reservations here.</p>
  <!-- Tester reservation card -->
	<ReservationDetailCard {...sampleReservation}/>
</div>
