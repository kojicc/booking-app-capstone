<script lang="ts" module>
	import BookOpenIcon from "@lucide/svelte/icons/book-open";
	import CalendarDays from "@lucide/svelte/icons/calendar-days";
	import Settings2Icon from "@lucide/svelte/icons/settings-2";
	import SquareTerminalIcon from "@lucide/svelte/icons/square-terminal";

	// This is sample data.
	const data = {
		user: {
			name: "castlms",
			email: "m@castlms.com",
			avatar: "",
			role: "", // change to "user" to test non-admin view
		},
		   navMain: [
			   {
				   title: "Dashboard",
				   url: "/dashboard",
				   icon: SquareTerminalIcon,
				   isActive: true,
			   },
			   {
				   title: "Calendar",
				   url: "/calendar",
				   icon: CalendarDays,
			   },
			   {
				   title: "Reservations",
				   url: "/reservations",
				   icon: BookOpenIcon,
			   },
			   {
				   title: "Trade Requests",
				   url: "/trade-requests",
				   icon: Settings2Icon,
			   },
		   ],
	
	};
</script>


<script lang="ts">
	import NavMain from "./nav-main.svelte";
	import NavUser from "./nav-user.svelte";
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import type { ComponentProps } from "svelte";
	import { page } from "$app/stores";
	import { user } from "$lib/stores/user";

	let {
		ref = $bindable(null),
		collapsible = "icon",
		...restProps
	}: ComponentProps<typeof Sidebar.Root> = $props();

	// Filter navMain for role-based access
	// compute navMainFiltered and update via $effect (runes-friendly)
	let navMainFiltered = $state(data.navMain);

	// ensure NavUser always receives required fields
	let sidebarUser = $state({ name: data.user.name, email: data.user.email, avatar: data.user.avatar });
	$effect(() => {
		const u = $user ?? data.user;
		sidebarUser = { name: u.name ?? data.user.name, email: u.email ?? data.user.email, avatar: u.avatar ?? data.user.avatar ?? '' };
	});
</script>

<Sidebar.Root {collapsible} {...restProps}>
	<!-- Sidebar.Header removed: no teams -->
	<Sidebar.Content >
		<NavMain items={navMainFiltered} currentPath={$page.url.pathname} />
	</Sidebar.Content>
	<Sidebar.Footer>
		<NavUser user={sidebarUser} />
	</Sidebar.Footer>
	<Sidebar.Rail />
</Sidebar.Root>
