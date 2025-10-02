<script lang="ts">
	import * as Collapsible from "$lib/components/ui/collapsible/index.js";
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import ChevronRightIcon from "@lucide/svelte/icons/chevron-right";

	let {
		items,
		currentPath
	}: {
		items: {
			title: string;
			url: string;
			icon?: any;
			isActive?: boolean;
			items?: {
				title: string;
				url: string;
			}[];
		}[];
		currentPath: string;
	} = $props();
</script>

<Sidebar.Group class="mt-2">
	<Sidebar.GroupLabel>
		<img src="/bhive.png" alt="bhive logo" class="h-10 w-auto ml-0" />
	</Sidebar.GroupLabel>
	<Sidebar.Menu class="mt-5">
		   {#each items as item (item.title)}
			   {#if item.title === "Reservations" && item.items && item.items.length}
				   <Collapsible.Root open={item.isActive} class="group/collapsible">
					   {#snippet child({ props })}
						   <Sidebar.MenuItem {...props}>
							   <Collapsible.Trigger>
								   {#snippet child({ props })}
									   <Sidebar.MenuButton {...props} tooltipContent={item.title}>
										   {#if item.icon}
											   <item.icon />
										   {/if}
										   <span>{item.title}</span>
										   <ChevronRightIcon
											   class="ml-auto transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90"
										   />
									   </Sidebar.MenuButton>
								   {/snippet}
							   </Collapsible.Trigger>
							   <Collapsible.Content>
								   <Sidebar.MenuSub>
									   {#each item.items ?? [] as subItem (subItem.title)}
										   <Sidebar.MenuSubItem>
											   <Sidebar.MenuSubButton>
												   {#snippet child({ props })}
													   <a href={subItem.url} {...props}>
														   <span>{subItem.title}</span>
													   </a>
												   {/snippet}
											   </Sidebar.MenuSubButton>
										   </Sidebar.MenuSubItem>
									   {/each}
								   </Sidebar.MenuSub>
							   </Collapsible.Content>
						   </Sidebar.MenuItem>
					   {/snippet}
				   </Collapsible.Root>
			   {:else}
				   <Sidebar.MenuItem>
					   <a
						   href={item.url}
						   class="block w-full rounded-lg"
						   style={currentPath === item.url ? 'background-color: var(--primary-200); color: white;' : ''}
					   >
						   <Sidebar.MenuButton tooltipContent={item.title}>
							   {#if item.icon}
								   <item.icon />
							   {/if}
							   <span>{item.title}</span>
						   </Sidebar.MenuButton>
					   </a>
				   </Sidebar.MenuItem>
			   {/if}
		   {/each}
	</Sidebar.Menu>
</Sidebar.Group>
