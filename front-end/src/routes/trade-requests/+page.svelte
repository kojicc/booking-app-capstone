
<script lang="ts">
	import AppSidebar from "$lib/components/app-sidebar.svelte";
	import AuthGuard from "$lib/components/AuthGuard.svelte";
	import * as Breadcrumb from "$lib/components/ui/breadcrumb/index.js";
	import * as Alert from "$lib/components/ui/alert";
	import { Separator } from "$lib/components/ui/separator/index.js";
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import { page } from "$app/stores";
	import { Construction } from "lucide-svelte";
	
	// Map path to label for breadcrumb
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
</script>

<AuthGuard>
<Sidebar.Provider>
	<AppSidebar />
	<Sidebar.Inset>
				<header
					class="group-has-data-[collapsible=icon]/sidebar-wrapper:h-12 flex h-16 shrink-0 items-center justify-between gap-2 transition-[width,height] ease-linear px-4 border-b"
				>
					<div class="flex flex-col justify-center">
						<div class="flex items-center gap-2">
							<Sidebar.Trigger class="-ml-1" />
							<Separator orientation="vertical" class="mr-2 data-[orientation=vertical]:h-4" />
							<Breadcrumb.Root>
								<Breadcrumb.List>
									<Breadcrumb.Item>
										<Breadcrumb.Page class="text-xl font-light">{(pathToLabel as Record<string,string>)[$page.url.pathname] ?? 'Trade Requests'}</Breadcrumb.Page>
									</Breadcrumb.Item>
								</Breadcrumb.List>
							</Breadcrumb.Root>
						</div>
					</div>
				</header>
				<div class="flex flex-1 flex-col gap-4 p-4">
					<!-- Development Notice -->
					<Alert.Root class="border-amber-200 bg-amber-50">
						<Construction class="h-5 w-5 text-amber-600" />
						<Alert.Title class="text-amber-900">Feature In Development</Alert.Title>
						<Alert.Description class="text-amber-800">
							The Trade Requests feature is currently under development and will be available soon! 
							This feature will allow you to swap reservations with other users. Stay tuned!
						</Alert.Description>
					</Alert.Root>
					
					<!-- Placeholder content -->
					<div class="flex items-center justify-center min-h-[400px] border-2 border-dashed rounded-lg">
						<div class="text-center text-muted-foreground">
							<Construction class="h-16 w-16 mx-auto mb-4 opacity-50" />
							<h3 class="text-lg font-semibold mb-2">Coming Soon</h3>
							<p>Trade request management will be here shortly.</p>
						</div>
					</div>
				</div>
	</Sidebar.Inset>
</Sidebar.Provider>
</AuthGuard>
