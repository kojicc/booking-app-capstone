import { apiFetch } from '.';

export interface Reservation {
	id: number;
	user: string;
	status?: string;
	start_time: string;
	end_time: string;
	reservation_type: string;
	notes?: string;
	date: Date;

	// admin stuff
	approved_by?: number;
    approved_at?: Date;
    rejection_reason?: string;
    created_at: Date;
    updated_at: Date;
}

export interface CreateReservationPayload {
    user: string; // user ID or email
    start_time: string; // hh:mm
    end_time: string; // hh:mm
    reservation_type: string; // e.g., "meeting", "event"
    date: string; // ISO date or yyyy-mm-dd string
    notes?: string;
}

export async function createReservation(data: CreateReservationPayload): Promise<Reservation> {

    try {
        const response = await apiFetch('/api/reservations/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        return response;
    } catch (error) {
        console.error('Error creating reservation:', error);
        throw error;
    }
}

export async function getReservations(): Promise<Reservation[]> {
    try {
        const response = await apiFetch('/api/reservations/', {
            method: 'GET'
        });
        return response;
    } catch (error) {
        console.error('Error fetching reservations:', error);
        throw error;
    }
}

export async function getReservationById(id: number): Promise<Reservation> {
    try {
        const response = await apiFetch(`/api/reservations/${id}/`, {
            method: 'GET'
        });
        return response;
    } catch (error) {
        console.error('Error fetching reservation by ID:', error);
        throw error;
    }
}

export async function updateReservation(id: number, data: Partial<CreateReservationPayload>): Promise<Reservation> {
    try {
        const response = await apiFetch(`/api/reservations/${id}/`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
        return response;
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
export async function approveReservation(id: number, approvedBy: number): Promise<Reservation> {
    try {
        const response = await apiFetch(`/api/reservations/${id}/approve/`, {
            method: 'POST',
            body: JSON.stringify({ approved_by: approvedBy })
        });
        return response;
    } catch (error) {
        console.error('Error approving reservation:', error);
        throw error;
    }
}

export async function rejectReservation(id: number, reason: string): Promise<Reservation> {
    try {
        const response = await apiFetch(`/api/reservations/${id}/reject/`, {
            method: 'POST',
            body: JSON.stringify({ rejection_reason: reason })
        });
        return response;
    } catch (error) {
        console.error('Error rejecting reservation:', error);
        throw error;
    }
}


