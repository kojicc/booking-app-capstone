<script lang="ts">
	// ===================== IMPORTS =====================
	import AppSidebar from "$lib/components/app-sidebar.svelte";
	import AuthGuard from "$lib/components/AuthGuard.svelte";
	import * as Breadcrumb from "$lib/components/ui/breadcrumb/index.js";
	import * as Card from "$lib/components/ui/card/index.js";
	import { Separator } from "$lib/components/ui/separator/index.js";
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import { Button } from "$lib/components/ui/button/index.js";
	import { Badge } from "$lib/components/ui/badge/index.js";
	import { page } from "$app/stores";
	import { user } from "$lib/stores/user";
	import { onMount } from "svelte";
	import { getUserDashboard, getAdminDashboard, type DashboardData, type Reservation } from "$lib/api/reservation";
	import { Calendar, Clock, CheckCircle, XCircle, AlertCircle, TrendingUp } from "lucide-svelte";
	
	// ===================== BREADCRUMB CONFIG =====================
	const pathToLabel = {
		"/dashboard": "Dashboard",
		"/calendar": "Calendar",
		"/reservations": "Reservations",
		"/reservations/all": "All Reservations",
		"/reservations/requests": "Reservation Requests",
		"/trade-requests": "Trade Requests",
		"/settings": "Settings",
		"/help": "Get Help",
		"/search": "Search",
	};
	
	let pageLabel = $state('Dashboard');

	$effect(() => {
		pageLabel = (pathToLabel as Record<string, string>)[$page.url.pathname] ?? 'Dashboard';
	});

	// ===================== DASHBOARD STATE =====================
	let dashboardData = $state<DashboardData | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Check kung admin ba or user - with debug logging
	let isAdmin = $derived($user?.role === 'admin');
	;

	// ===================== DATA LOADING =====================
	// I-load ang dashboard data based sa role (admin or user)
	onMount(async () => {
		await new Promise(resolve => setTimeout(resolve, 100));
		await loadDashboardData();
	});

	async function loadDashboardData() {
		loading = true;
		error = null;
		
		try {
			console.log('📊 Loading dashboard for role:', $user?.role, 'isAdmin:', isAdmin);
			
			if (isAdmin) {
				console.log('✅ Fetching admin dashboard...');
				dashboardData = await getAdminDashboard();
			} else {
				console.log('✅ Fetching user dashboard...');
				dashboardData = await getUserDashboard();
			}
			
			console.log('📦 Dashboard data loaded:', dashboardData);
		} catch (err: any) {
			console.error('❌ Error loading dashboard:', err);
			error = err?.message || 'Failed to load dashboard data';
		} finally {
			loading = false;
		}
	}

	// ===================== HELPER FUNCTIONS =====================
	function getStatusColor(status: string): string {
		switch (status?.toUpperCase()) {
			case 'CONFIRMED':
				return 'bg-green-100 text-green-800 border-green-200';
			case 'PENDING':
				return 'bg-yellow-100 text-yellow-800 border-yellow-200';
			case 'REJECTED':
				return 'bg-red-100 text-red-800 border-red-200';
			case 'CANCELLED':
				return 'bg-gray-100 text-gray-800 border-gray-200';
			default:
				return 'bg-blue-100 text-blue-800 border-blue-200';
		}
	}

	function formatDate(dateString: string | Date): string {
		const date = new Date(dateString);
		return date.toLocaleDateString('en-US', { 
			month: 'short', 
			day: 'numeric',
			year: 'numeric' 
		});
	}

	function formatActivityDetails(activity: any): string {
		// Format activity.details into a human-readable string
		if (!activity.details) return '';
		
		const details = activity.details;
		
		// Handle CREATED actions with initial_status
		if (activity.action === 'CREATED' && details.initial_status) {
			const status = details.initial_status === 'CONFIRMED' ? 'Confirmed' : 'Pending approval';
			return `New ${details.reservation_type || 'reservation'} - ${status}`;
		}
		
		// Handle REJECTED actions
		if (activity.action === 'REJECTED' || activity.action === 'reject') {
			if (details.rejection_reason) {
				return `Reason: ${details.rejection_reason}`;
			}
			return 'Reservation was rejected';
		}
		
		// Handle CANCELLED actions
		if (activity.action === 'CANCELLED' || activity.action === 'cancel') {
			return 'Reservation was cancelled by user';
		}
		
		// If details has new_data and old_data, format the changes
		if (details.new_data && details.old_data) {
			const newData = details.new_data;
			const oldData = details.old_data;
			const changes: string[] = [];
			
			// Compare key fields and show what changed
			if (newData.status !== oldData.status) {
				changes.push(`${oldData.status_display || oldData.status} → ${newData.status_display || newData.status}`);
			}
			if (newData.start_time !== oldData.start_time) {
				changes.push(`Time: ${oldData.start_time.substring(0, 5)} → ${newData.start_time.substring(0, 5)}`);
			}
			if (newData.end_time !== oldData.end_time) {
				changes.push(`Ends: ${oldData.end_time.substring(0, 5)} → ${newData.end_time.substring(0, 5)}`);
			}
			if (newData.date !== oldData.date) {
				changes.push(`Date changed`);
			}
			if (newData.notes !== oldData.notes) {
				changes.push(`Notes updated`);
			}
			
			if (changes.length > 0) {
				const userName = newData.user?.email || newData.user?.first_name || '';
				const userPart = userName ? ` by ${userName}` : '';
				return `Reservation #${newData.id}${userPart}: ${changes.join(' • ')}`;
			}
			
			return `Reservation #${newData.id} modified`;
		}
		
		// If there's a reservation_id or id, use it
		if (details.reservation_id || details.id) {
			const id = details.reservation_id || details.id;
			const userName = details.user?.email || details.user || '';
			const userPart = userName ? ` by ${userName}` : '';
			return `Reservation #${id}${userPart}`;
		}
		
		// Don't show raw JSON - return empty string if we can't parse it nicely
		return '';
	}

	function getActivityActionLabel(action: string): string {
		// Convert backend action codes to user-friendly labels
		switch (action?.toUpperCase()) {
			case 'CREATED':
				return 'New Reservation';
			case 'UPDATED':
				return 'Reservation Updated';
			case 'DELETED':
			case 'CANCELLED':
			case 'CANCEL':
				return 'Reservation Cancelled';
			case 'APPROVED':
				return 'Reservation Approved';
			case 'REJECTED':
			case 'REJECT':
				return 'Reservation Rejected';
			default:
				// Capitalize first letter
				return action ? action.charAt(0).toUpperCase() + action.slice(1).toLowerCase() : 'Activity';
		}
	}
	
	function getActivityIcon(action: string) {
		switch (action?.toUpperCase()) {
			case 'CREATED':
				return CheckCircle;
			case 'UPDATED':
				return Clock;
			case 'APPROVED':
				return CheckCircle;
			case 'REJECTED':
			case 'REJECT':
				return XCircle;
			case 'CANCELLED':
			case 'CANCEL':
			case 'DELETED':
				return XCircle;
			default:
				return AlertCircle;
		}
	}
	
	function getActivityColor(action: string): string {
		switch (action?.toUpperCase()) {
			case 'CREATED':
				return 'text-green-600 bg-green-50 border-green-200';
			case 'APPROVED':
				return 'text-green-600 bg-green-50 border-green-200';
			case 'UPDATED':
				return 'text-blue-600 bg-blue-50 border-blue-200';
			case 'REJECTED':
			case 'REJECT':
				return 'text-red-600 bg-red-50 border-red-200';
			case 'CANCELLED':
			case 'CANCEL':
			case 'DELETED':
				return 'text-gray-600 bg-gray-50 border-gray-200';
			default:
				return 'text-gray-600 bg-gray-50 border-gray-200';
		}
	}

	function formatTime(timeString: string): string {
		// Remove seconds kung meron
		return timeString.substring(0, 5);
	}
</script>

<AuthGuard>
<Sidebar.Provider>
	<AppSidebar />
	<Sidebar.Inset>
		<header
			class="group-has-data-[collapsible=icon]/sidebar-wrapper:h-12 flex h-16 shrink-0 items-center justify-between gap-2 transition-[width,height] ease-linear px-4 border-b"
		>
			<div class="flex items-center gap-2 px-4">
				<Sidebar.Trigger class="-ml-1" />
				<Separator orientation="vertical" class="mr-2 data-[orientation=vertical]:h-4" />
				<Breadcrumb.Root>
					<Breadcrumb.List>
						<Breadcrumb.Item>
							<Breadcrumb.Page class="text-lg">{pageLabel}</Breadcrumb.Page>
						</Breadcrumb.Item>
					</Breadcrumb.List>
				</Breadcrumb.Root>
			</div>
		</header>

		<!-- ===================== MAIN DASHBOARD CONTENT ===================== -->
		<div class="flex flex-1 flex-col gap-6 p-6">
			{#if loading}
				<!-- Loading state -->
				<div class="flex items-center justify-center py-12">
					<div class="flex flex-col items-center gap-3">
						<div class="animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
						<p class="text-sm text-muted-foreground">Loading dashboard...</p>
					</div>
				</div>

			{:else if error}
				<!-- Error state -->
				<div class="rounded-lg border border-destructive/20 bg-destructive/10 p-6 text-center">
					<AlertCircle class="h-12 w-12 mx-auto text-destructive mb-3" />
					<p class="text-destructive font-medium">{error}</p>
					<Button variant="outline" class="mt-4" onclick={loadDashboardData}>
						Try Again
					</Button>
				</div>

			{:else if isAdmin}
				<!-- ===================== ADMIN DASHBOARD ===================== -->
				<div>
					<h2 class="text-2xl font-bold mb-2">Admin Dashboard</h2>
					<p class="text-muted-foreground">Overview ng lahat ng reservations at pending requests</p>
				</div>

				<!-- Admin Stats Cards -->
				<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
					<!-- Pending Approvals Card -->
					<Card.Root class="border-yellow-200 bg-yellow-50/50">
						<Card.Header class="flex flex-row items-center justify-between space-y-0 pb-2">
							<Card.Title class="text-sm font-medium">Pending Approvals</Card.Title>
							<AlertCircle class="h-4 w-4 text-yellow-600" />
						</Card.Header>
						<Card.Content>
							<div class="text-3xl font-bold text-yellow-700">
								{dashboardData?.pending_approvals ?? 0}
							</div>
							<p class="text-xs text-muted-foreground mt-1">
								Primetime reservations waiting for approval
							</p>
							<Button variant="link" class="px-0 mt-2" href="/reservations">
								Review Now →
							</Button>
						</Card.Content>
					</Card.Root>

					<!-- Today's Reservations Card -->
					<Card.Root class="border-blue-200 bg-blue-50/50">
						<Card.Header class="flex flex-row items-center justify-between space-y-0 pb-2">
							<Card.Title class="text-sm font-medium">Today's Reservations</Card.Title>
							<Calendar class="h-4 w-4 text-blue-600" />
						</Card.Header>
						<Card.Content>
							<div class="text-3xl font-bold text-blue-700">
								{dashboardData?.todays_reservations ?? 0}
							</div>
							<p class="text-xs text-muted-foreground mt-1">
								Confirmed bookings for today
							</p>
							<Button variant="link" class="px-0 mt-2" href="/calendar">
								View Calendar →
							</Button>
						</Card.Content>
					</Card.Root>

					<!-- Activity Card -->
					<Card.Root class="border-green-200 bg-green-50/50">
						<Card.Header class="flex flex-row items-center justify-between space-y-0 pb-2">
							<Card.Title class="text-sm font-medium">Recent Activity</Card.Title>
							<TrendingUp class="h-4 w-4 text-green-600" />
						</Card.Header>
						<Card.Content>
							<div class="text-3xl font-bold text-green-700">
								{dashboardData?.recent_activity?.length ?? 0}
							</div>
							<p class="text-xs text-muted-foreground mt-1">
								Actions in the last 24 hours
							</p>
						</Card.Content>
					</Card.Root>
				</div>

				<!-- Recent Activity Log -->
				{#if dashboardData?.recent_activity && dashboardData.recent_activity.length > 0}
					<Card.Root>
						<Card.Header>
							<Card.Title>Recent Activity</Card.Title>
							<Card.Description>Latest actions and updates sa system</Card.Description>
						</Card.Header>
						<Card.Content>
							<div class="space-y-3">
								{#each dashboardData.recent_activity.slice(0, 10) as activity}
									<div class="flex items-start gap-3 p-3 rounded-lg bg-muted/30 border">
										<div class="flex-1">
											<p class="text-sm font-medium">{getActivityActionLabel(activity.action)}</p>
											<p class="text-xs text-muted-foreground mt-1">
												{formatActivityDetails(activity)}
											</p>
											<p class="text-xs text-muted-foreground mt-1">
												{activity.timestamp ? formatDate(activity.timestamp) : ''}
											</p>
										</div>
									</div>
								{/each}
							</div>
						</Card.Content>
					</Card.Root>
				{/if}

			{:else}
				<!-- ===================== USER DASHBOARD ===================== -->
				<div>
					<h2 class="text-2xl font-bold mb-2">Welcome, {$user?.email || 'User'}!</h2>
					<p class="text-muted-foreground">Here's your reservation overview</p>
				</div>

				<!-- User Stats Cards -->
				<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
					<!-- Upcoming Reservations Card -->
					<Card.Root class="border-blue-200 bg-blue-50/50">
						<Card.Header class="flex flex-row items-center justify-between space-y-0 pb-2">
							<Card.Title class="text-sm font-medium">Upcoming Reservations</Card.Title>
							<Calendar class="h-4 w-4 text-blue-600" />
						</Card.Header>
						<Card.Content>
							<div class="text-3xl font-bold text-blue-700">
								{dashboardData?.upcoming_reservations?.length ?? 0}
							</div>
							<p class="text-xs text-muted-foreground mt-1">
								Bookings scheduled ahead
							</p>
							<Button variant="link" class="px-0 mt-2" href="/reservations">
								View All →
							</Button>
						</Card.Content>
					</Card.Root>

					<!-- Pending Trades Card -->
					<Card.Root class="border-purple-200 bg-purple-50/50">
						<Card.Header class="flex flex-row items-center justify-between space-y-0 pb-2">
							<Card.Title class="text-sm font-medium">Trade Requests</Card.Title>
							<Clock class="h-4 w-4 text-purple-600" />
						</Card.Header>
						<Card.Content>
							<div class="flex items-baseline gap-2">
								<div class="text-2xl font-bold text-purple-700">
									{dashboardData?.pending_trades?.received ?? 0}
								</div>
								<span class="text-sm text-muted-foreground">received</span>
							</div>
							<div class="flex items-baseline gap-2 mt-1">
								<div class="text-2xl font-bold text-purple-700">
									{dashboardData?.pending_trades?.sent ?? 0}
								</div>
								<span class="text-sm text-muted-foreground">sent</span>
							</div>
							<Button variant="link" class="px-0 mt-2" href="/trade-requests">
								Manage Trades →
							</Button>
						</Card.Content>
					</Card.Root>

					<!-- Quick Action Card -->
					<Card.Root class="border-green-200 bg-green-50/50">
						<Card.Header>
							<Card.Title class="text-sm font-medium">Quick Actions</Card.Title>
						</Card.Header>
						<Card.Content class="space-y-2">
							<Button variant="default" class="w-full" href="/calendar">
								<Calendar class="mr-2 h-4 w-4" />
								Book a Space
							</Button>
							<Button variant="outline" class="w-full" href="/trade-requests">
								<Clock class="mr-2 h-4 w-4" />
								Request Trade
							</Button>
						</Card.Content>
					</Card.Root>
				</div>

				<!-- Upcoming Reservations List -->
				{#if dashboardData?.upcoming_reservations && dashboardData.upcoming_reservations.length > 0}
					<Card.Root>
						<Card.Header>
							<Card.Title>Upcoming Reservations</Card.Title>
							<Card.Description>Your scheduled bookings na malapit na</Card.Description>
						</Card.Header>
						<Card.Content>
							<div class="space-y-3">
								{#each dashboardData.upcoming_reservations as reservation}
									<div class="flex items-start gap-4 p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors">
										<div class="flex-shrink-0 pt-1">
											{#if reservation.status === 'CONFIRMED'}
												<CheckCircle class="h-5 w-5 text-green-600" />
											{:else if reservation.status === 'PENDING'}
												<Clock class="h-5 w-5 text-yellow-600" />
											{:else}
												<XCircle class="h-5 w-5 text-red-600" />
											{/if}
										</div>
										<div class="flex-1 min-w-0">
											<div class="flex items-center gap-2 mb-1">
												<h4 class="font-medium text-sm">
													{reservation.booking_name || reservation.reservation_type_display || reservation.reservation_type}
												</h4>
												<Badge class={getStatusColor(reservation.status || '')} variant="outline">
													{reservation.status_display || reservation.status}
												</Badge>
											</div>
											<div class="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
												<span class="flex items-center gap-1">
													<Calendar class="h-3 w-3" />
													{formatDate(reservation.date)}
												</span>
												<span class="flex items-center gap-1">
													<Clock class="h-3 w-3" />
													{formatTime(reservation.start_time)} - {formatTime(reservation.end_time)}
												</span>
											</div>
											{#if reservation.notes}
												<p class="text-xs text-muted-foreground mt-2">
													{reservation.notes}
												</p>
											{/if}
										</div>
										<Button variant="ghost" size="sm" href={`/reservations?open=${reservation.id}`}>
											View
										</Button>
									</div>
								{/each}
							</div>
						</Card.Content>
					</Card.Root>
				{:else}
					<!-- No reservations state -->
					<Card.Root>
						<Card.Content class="py-12">
							<div class="text-center">
								<Calendar class="h-12 w-12 mx-auto text-muted-foreground mb-3" />
								<h3 class="font-medium mb-2">No Upcoming Reservations</h3>
								<p class="text-sm text-muted-foreground mb-4">
									Wala pang naka-book na reservations. Start by booking a space!
								</p>
								<Button href="/calendar">
									<Calendar class="mr-2 h-4 w-4" />
									Book Now
								</Button>
							</div>
						</Card.Content>
					</Card.Root>
				{/if}
			{/if}
		</div>
	</Sidebar.Inset>
</Sidebar.Provider>
</AuthGuard>
