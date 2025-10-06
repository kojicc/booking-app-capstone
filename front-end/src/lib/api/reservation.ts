import { apiFetch } from '.';

export interface Reservation {
	id: number;
	user:
		| string
		| {
				id: number;
				email: string;
				first_name: string;
				last_name: string;
				role: string;
		  };
	booking_name: string;
	status?: string;
	status_display?: string;
	start_time: string;
	end_time: string;
	reservation_type: string;
	reservation_type_display?: string;
	notes?: string;
	date: Date | string;
	is_editable?: boolean;
	can_be_traded?: boolean;

	// admin stuff
	approved_by?: number;
	approved_at?: Date | string;
	rejection_reason?: string;
	created_at: Date | string;
	updated_at: Date | string;
}

export interface CreateReservationPayload {
	user: string; // user ID or email
	booking_name: string; // name/title for the booking
	start_time: string; // hh:mm
	end_time: string; // hh:mm
	reservation_type: string; // e.g., "meeting", "event"
	date: string; // ISO date or yyyy-mm-dd string
	notes?: string;
}

export async function createReservation(payload: CreateReservationPayload): Promise<Reservation> {
	try {
		// apiFetch returns parsed JSON when the response content-type is application/json
		const result = await apiFetch('/api/reservations/', {
			method: 'POST',
			body: JSON.stringify(payload)
		});

		return result as Reservation;
	} catch (error) {
		console.error('Error creating reservation:', error);
		throw error;
	}
}

export async function getReservations(): Promise<Reservation[]> {
	try {
		const result = await apiFetch('/api/reservations/', {
			method: 'GET'
		});
		return result as Reservation[];
	} catch (error) {
		console.error('Error fetching reservations:', error);
		throw error;
	}
}

export async function updateReservation(
	id: number,
	data: Partial<CreateReservationPayload>
): Promise<Reservation> {
	try {
		const result = await apiFetch(`/api/reservations/${id}/`, {
			method: 'PUT',
			body: JSON.stringify(data)
		});
		return result as Reservation;
	} catch (error) {
		console.error('Error updating reservation:', error);
		throw error;
	}
}

export async function deleteReservation(id: number): Promise<void> {
	try {
		await apiFetch(`/api/reservations/${id}/`, {
			method: 'DELETE'
		});
	} catch (error) {
		console.error('Error deleting reservation:', error);
		throw error;
	}
}

// Additional admin functions
export async function approveReservation(id: number): Promise<Reservation> {
	try {
		const response = await apiFetch(`/api/reservations/${id}/approve/`, {
			method: 'POST',
			body: JSON.stringify({ action: 'approve' })
		});
		return response;
	} catch (error) {
		console.error('Error approving reservation:', error);
		throw error;
	}
}

export async function rejectReservation(id: number, reason: string): Promise<Reservation> {
	try {
		const response = await apiFetch(`/api/reservations/${id}/approve/`, {
			method: 'POST',
			body: JSON.stringify({
				action: 'reject',
				rejection_reason: reason
			})
		});
		return response;
	} catch (error) {
		console.error('Error rejecting reservation:', error);
		throw error;
	}
}

// Calendar and availability functions
export interface TimeSlot {
	start_time: string;
	end_time: string;
	type: 'FREE_FOR_ALL' | 'PRIMETIME';
	available: boolean;
}

export interface CalendarDay {
	date: string;
	is_primetime: boolean;
	primetime_hours?: {
		start_time: string;
		end_time: string;
	} | null;
	business_hours: {
		start_time: string;
		end_time: string;
	};
	available_slots: TimeSlot[];
	reserved_slots: Reservation[];
}

export interface CalendarResponse {
	start_date: string;
	end_date: string;
	calendar: CalendarDay[];
}

export async function getCalendar(startDate?: string, endDate?: string): Promise<CalendarResponse> {
	try {
		const params = new URLSearchParams();
		if (startDate) params.append('start_date', startDate);
		if (endDate) params.append('end_date', endDate);

		const response = await apiFetch(`/api/reservations/calendar/?${params.toString()}`);
		return response;
	} catch (error) {
		console.error('Error fetching calendar:', error);
		throw error;
	}
}

// ------------------ CACHING HELPERS ------------------
// Simple in-memory month cache to avoid refetching the same month repeatedly.
// Keyed by YYYY-MM -> { fetchedAt, response }
const monthCache: Map<string, { fetchedAt: number; response: CalendarResponse }> = new Map();

function monthKeyFromDateStr(dateStr: string) {
	const d = new Date(dateStr);
	return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

/**
 * Fetch calendar for a given month from cache or server.
 * If force=true, always fetch from server and update cache.
 */
export async function getCalendarMonthCached(
	year: number,
	monthZeroBased: number,
	force = false
): Promise<CalendarResponse> {
	const key = `${year}-${String(monthZeroBased + 1).padStart(2, '0')}`;
	if (!force && monthCache.has(key)) {
		return monthCache.get(key)!.response;
	}

	const startOfMonth = new Date(year, monthZeroBased, 1).toISOString().split('T')[0];
	const endOfMonth = new Date(year, monthZeroBased + 1, 0).toISOString().split('T')[0];
	const response = await getCalendar(startOfMonth, endOfMonth);
	monthCache.set(key, { fetchedAt: Date.now(), response });
	return response;
}

/**
 * Get calendar data for a specific date (YYYY-MM-DD) using the month cache.
 * Returns the CalendarDay for that date or null if not found.
 * If force=true, re-fetches the month from the server to ensure freshness.
 */
export async function getCalendarForDate(
	dateStr: string,
	force = false
): Promise<CalendarDay | null> {
	try {
		const d = new Date(dateStr);
		const year = d.getFullYear();
		const month = d.getMonth();
		const monthResp = await getCalendarMonthCached(year, month, force);
		const day = (monthResp.calendar || []).find((c: CalendarDay) => c.date === dateStr);
		return day ?? null;
	} catch (e) {
		console.error('Error getCalendarForDate:', e);
		return null;
	}
}

// ===================== PRIMETIME MANAGEMENT (ADMIN) =====================
// Para sa admin na mag-manage ng primetime settings - yung special hours na need ng approval

export interface PrimeTimeSettings {
	id: number;
	weekday: number; // 0=Monday, 6=Sunday
	weekday_display?: string;
	start_time: string; // HH:MM:SS format
	end_time: string;
	is_active: boolean;
	created_at?: string;
	updated_at?: string;
}

export interface CreatePrimeTimePayload {
	weekday: number;
	start_time: string;
	end_time: string;
	is_active?: boolean;
}

// Kunin lahat ng primetime settings - para makita ng admin kung anong days at hours ang primetime
export async function getPrimeTimeSettings(): Promise<PrimeTimeSettings[]> {
	try {
		const response = await apiFetch('/api/reservations/admin/primetime/');
		return response as PrimeTimeSettings[];
	} catch (error) {
		console.error('Error fetching primetime settings:', error);
		throw error;
	}
}

// Gumawa ng bagong primetime setting - halimbawa set Wednesday 6pm-9pm as primetime
export async function createPrimeTime(payload: CreatePrimeTimePayload): Promise<PrimeTimeSettings> {
	try {
		const response = await apiFetch('/api/reservations/admin/primetime/', {
			method: 'POST',
			body: JSON.stringify(payload)
		});
		return response as PrimeTimeSettings;
	} catch (error) {
		console.error('Error creating primetime setting:', error);
		throw error;
	}
}

// I-update ang existing primetime - kung gusto palitan yung oras o i-deactivate
export async function updatePrimeTime(
	id: number,
	payload: Partial<CreatePrimeTimePayload>
): Promise<PrimeTimeSettings> {
	try {
		const response = await apiFetch(`/api/reservations/admin/primetime/${id}/`, {
			method: 'PUT',
			body: JSON.stringify(payload)
		});
		return response as PrimeTimeSettings;
	} catch (error) {
		console.error('Error updating primetime setting:', error);
		throw error;
	}
}

// Tanggalin ang primetime setting - pag hindi na kailangan yung specific day/time
export async function deletePrimeTime(id: number): Promise<void> {
	try {
		await apiFetch(`/api/reservations/admin/primetime/${id}/`, {
			method: 'DELETE'
		});
	} catch (error) {
		console.error('Error deleting primetime setting:', error);
		throw error;
	}
}

// ===================== DASHBOARD DATA =====================
// Para sa dashboard - showing yung user/admin overview ng reservations

export interface DashboardData {
	upcoming_reservations?: Reservation[];
	pending_trades?: {
		sent: number;
		received: number;
	};
	recent_activity?: any[];
	pending_approvals?: number; // admin only
	todays_reservations?: number; // admin only
}

// Kunin ang user dashboard data - showing upcoming bookings at trade requests
export async function getUserDashboard(): Promise<DashboardData> {
	try {
		const response = await apiFetch('/api/reservations/dashboard/user/');
		return response as DashboardData;
	} catch (error) {
		console.error('Error fetching user dashboard:', error);
		throw error;
	}
}

// Kunin ang admin dashboard data - showing pending approvals at today's reservations
export async function getAdminDashboard(): Promise<DashboardData> {
	try {
		const response = await apiFetch('/api/reservations/dashboard/admin/');
		return response as DashboardData;
	} catch (error) {
		console.error('Error fetching admin dashboard:', error);
		throw error;
	}
}
