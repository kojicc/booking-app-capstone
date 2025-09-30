
# Comprehensive unit and API tests for the reservation system
# Each test includes a comment describing the scenario and how to test it via Postman or SvelteKit frontend

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, time, timedelta
from django.utils import timezone

from .models import (
    Reservation, 
    PrimeTimeSettings, 
    TradeRequest, 
    CalendarSettings,
    ReservationAuditLog
)

User = get_user_model()

# --- MODEL TESTS ---

class ReservationModelTests(TestCase):
    """
    Reservation model scenarios:
    - Free-for-all reservation creation
    - Primetime reservation creation
    - Past date validation
    - Invalid time range validation
    - Business hours validation
    - Overlapping reservations prevention
    - Reservation editability logic
    """
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
        self.primetime = PrimeTimeSettings.objects.create(
            weekday=0,  # Monday
            start_time=time(12, 0),
            end_time=time(14, 0),
            is_active=True
        )
        self.tomorrow = date.today() + timedelta(days=1)

    def test_create_free_for_all_reservation(self):
        """
        Scenario: User books a slot outside primetime (auto-confirmed)
        Postman/SvelteKit: POST /api/reservations/ with date/time outside primetime
        """
        reservation = Reservation.objects.create(
            user=self.user,
            date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0)
        )
        self.assertEqual(reservation.status, 'CONFIRMED')
        self.assertEqual(reservation.reservation_type, 'FREE_FOR_ALL')

    def test_create_primetime_reservation(self):
        """
        Scenario: User books a slot during primetime (pending approval)
        Postman/SvelteKit: POST /api/reservations/ with date/time in primetime
        """
        days_ahead = (0 - self.tomorrow.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        next_monday = self.tomorrow + timedelta(days=days_ahead)
        reservation = Reservation.objects.create(
            user=self.user,
            date=next_monday,
            start_time=time(12, 30),
            end_time=time(13, 30)
        )
        self.assertEqual(reservation.status, 'PENDING')
        self.assertEqual(reservation.reservation_type, 'PRIMETIME')

    def test_reservation_validation_past_date(self):
        """
        Scenario: User tries to book a slot in the past (should fail)
        Postman/SvelteKit: POST /api/reservations/ with a past date
        """
        yesterday = date.today() - timedelta(days=1)
        reservation = Reservation(
            user=self.user,
            date=yesterday,
            start_time=time(10, 0),
            end_time=time(11, 0)
        )
        with self.assertRaises(ValidationError):
            reservation.full_clean()

    def test_reservation_validation_invalid_time_range(self):
        """
        Scenario: End time before start time (should fail)
        Postman/SvelteKit: POST /api/reservations/ with end_time < start_time
        """
        reservation = Reservation(
            user=self.user,
            date=self.tomorrow,
            start_time=time(11, 0),
            end_time=time(10, 0)
        )
        with self.assertRaises(ValidationError):
            reservation.full_clean()

    def test_reservation_validation_outside_business_hours(self):
        """
        Scenario: Booking outside business hours (should fail)
        Postman/SvelteKit: POST /api/reservations/ with time outside allowed range
        """
        reservation = Reservation(
            user=self.user,
            date=self.tomorrow,
            start_time=time(6, 0),
            end_time=time(7, 0)
        )
        with self.assertRaises(ValidationError):
            reservation.full_clean()

    def test_overlapping_reservations(self):
        """
        Scenario: Two users try to book overlapping slots (should fail)
        Postman/SvelteKit: POST /api/reservations/ for overlapping times
        """
        Reservation.objects.create(
            user=self.user,
            date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0)
        )
        overlapping_reservation = Reservation(
            user=self.admin_user,
            date=self.tomorrow,
            start_time=time(10, 30),
            end_time=time(11, 30)
        )
        with self.assertRaises(ValidationError):
            overlapping_reservation.full_clean()

    def test_reservation_is_editable(self):
        """
        Scenario: User can edit future reservations, not past ones
        Postman/SvelteKit: PATCH /api/reservations/{id}/ for future/past
        """
        reservation = Reservation.objects.create(
            user=self.user,
            date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0)
        )
        self.assertTrue(reservation.is_editable())
        past_reservation = Reservation.objects.create(
            user=self.user,
            date=date.today() - timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0)
        )
        self.assertFalse(past_reservation.is_editable())

# --- PRIMETIME SETTINGS TESTS ---

class PrimeTimeSettingsModelTests(TestCase):
    """
    Primetime settings scenarios:
    - Admin creates primetime settings
    - Invalid time range validation
    - Unique weekday constraint
    """
    def test_create_primetime_settings(self):
        """
        Scenario: Admin sets primetime for a weekday
        Postman/SvelteKit: POST /api/reservations/admin/primetime/
        """
        settings = PrimeTimeSettings.objects.create(
            weekday=1,
            start_time=time(12, 0),
            end_time=time(14, 0),
            is_active=True
        )
        self.assertEqual(settings.weekday, 1)
        self.assertEqual(settings.start_time, time(12, 0))
        self.assertEqual(settings.end_time, time(14, 0))
        self.assertTrue(settings.is_active)

    def test_primetime_validation_invalid_time_range(self):
        """
        Scenario: End time before start time (should fail)
        Postman/SvelteKit: POST /api/reservations/admin/primetime/ with invalid times
        """
        settings = PrimeTimeSettings(
            weekday=1,
            start_time=time(14, 0),
            end_time=time(12, 0)
        )
        with self.assertRaises(ValidationError):
            settings.full_clean()

    def test_unique_weekday_constraint(self):
        """
        Scenario: Only one primetime setting per weekday allowed
        Postman/SvelteKit: POST /api/reservations/admin/primetime/ for same weekday
        """
        PrimeTimeSettings.objects.create(
            weekday=1,
            start_time=time(12, 0),
            end_time=time(14, 0)
        )
        with self.assertRaises(IntegrityError):
            PrimeTimeSettings.objects.create(
                weekday=1,
                start_time=time(15, 0),
                end_time=time(17, 0)
            )

# --- TRADE REQUEST TESTS ---

class TradeRequestModelTests(TestCase):
    """
    Trade request scenarios:
    - Trade request creation
    - Self-trade prevention
    """
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        tomorrow = date.today() + timedelta(days=1)
        self.reservation1 = Reservation.objects.create(
            user=self.user1,
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            status='CONFIRMED'
        )
        self.reservation2 = Reservation.objects.create(
            user=self.user2,
            date=tomorrow,
            start_time=time(14, 0),
            end_time=time(15, 0),
            status='CONFIRMED'
        )

    def test_create_trade_request(self):
        """
        Scenario: User requests to trade slots
        Postman/SvelteKit: POST /api/reservations/trades/
        """
        trade = TradeRequest.objects.create(
            requester=self.user1,
            target_user=self.user2,
            requester_reservation=self.reservation1,
            target_reservation=self.reservation2,
            message="Would like to trade"
        )
        self.assertEqual(trade.status, 'PENDING')
        self.assertEqual(trade.requester, self.user1)
        self.assertEqual(trade.target_user, self.user2)

    def test_trade_validation_same_user(self):
        """
        Scenario: User tries to trade with themselves (should fail)
        Postman/SvelteKit: POST /api/reservations/trades/ with same user
        """
        trade = TradeRequest(
            requester=self.user1,
            target_user=self.user1,
            requester_reservation=self.reservation1,
            target_reservation=self.reservation2
        )
        with self.assertRaises(ValidationError):
            trade.full_clean()

# --- CALENDAR SETTINGS TESTS ---

class CalendarSettingsModelTests(TestCase):
    """
    Calendar settings scenarios:
    - Business hours configuration
    - Single instance constraint
    """
    def test_create_calendar_settings(self):
        """
        Scenario: Set business hours and slot duration
        Postman/SvelteKit: POST /api/reservations/admin/calendar-settings/
        """
        settings = CalendarSettings.objects.create(
            business_start_time=time(8, 0),
            business_end_time=time(18, 0),
            slot_duration_minutes=30
        )
        self.assertEqual(settings.business_start_time, time(8, 0))
        self.assertEqual(settings.business_end_time, time(18, 0))
        self.assertEqual(settings.slot_duration_minutes, 30)

    def test_single_instance_constraint(self):
        """
        Scenario: Only one calendar settings instance allowed
        Postman/SvelteKit: POST /api/reservations/admin/calendar-settings/ (second time should fail)
        """
        CalendarSettings.objects.create()
        with self.assertRaises(ValidationError):
            CalendarSettings.objects.create()

# --- API TESTS ---

class ReservationAPITests(APITestCase):
    """
    Reservation API scenarios:
    - Authenticated reservation creation
    - Unauthenticated access prevention
    - User-specific data access
    - Admin all-access
    - Admin approval workflow
    - Reservation rejection
    """
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
        self.tomorrow = date.today() + timedelta(days=1)

    def test_create_reservation_authenticated(self):
        """
        Scenario: Authenticated user creates reservation
        Postman/SvelteKit: POST /api/reservations/ with JWT token
        """
        self.client.force_authenticate(user=self.user)
        data = {
            'date': self.tomorrow.isoformat(),
            'start_time': '10:00:00',
            'end_time': '11:00:00',
            'notes': 'Test reservation'
        }
        response = self.client.post('/api/reservations/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_create_reservation_unauthenticated(self):
        """
        Scenario: Unauthenticated user tries to create reservation (should fail)
        Postman/SvelteKit: POST /api/reservations/ without JWT token
        """
        data = {
            'date': self.tomorrow.isoformat(),
            'start_time': '10:00:00',
            'end_time': '11:00:00'
        }
        response = self.client.post('/api/reservations/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_user_reservations(self):
        """
        Scenario: User lists their own reservations
        Postman/SvelteKit: GET /api/reservations/ with JWT token
        """
        self.client.force_authenticate(user=self.user)
        Reservation.objects.create(
            user=self.user,
            date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0)
        )
        Reservation.objects.create(
            user=self.admin_user,
            date=self.tomorrow,
            start_time=time(14, 0),
            end_time=time(15, 0)
        )
        response = self.client.get('/api/reservations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_admin_list_all_reservations(self):
        """
        Scenario: Admin lists all reservations
        Postman/SvelteKit: GET /api/reservations/ as admin
        """
        self.client.force_authenticate(user=self.admin_user)
        Reservation.objects.create(
            user=self.user,
            date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0)
        )
        Reservation.objects.create(
            user=self.admin_user,
            date=self.tomorrow,
            start_time=time(14, 0),
            end_time=time(15, 0)
        )
        response = self.client.get('/api/reservations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_approve_reservation(self):
        """
        Scenario: Admin approves a primetime reservation
        Postman/SvelteKit: POST /api/reservations/{id}/approve/ as admin
        """
        self.client.force_authenticate(user=self.admin_user)
        PrimeTimeSettings.objects.create(
            weekday=self.tomorrow.weekday(),
            start_time=time(12, 0),
            end_time=time(14, 0),
            is_active=True
        )
        reservation = Reservation.objects.create(
            user=self.user,
            date=self.tomorrow,
            start_time=time(12, 30),
            end_time=time(13, 30)
        )
        data = {'action': 'approve'}
        response = self.client.post(f'/api/reservations/{reservation.id}/approve/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, 'CONFIRMED')

    def test_reject_reservation(self):
        """
        Scenario: Admin rejects a reservation
        Postman/SvelteKit: POST /api/reservations/{id}/approve/ with rejection reason
        """
        self.client.force_authenticate(user=self.admin_user)
        reservation = Reservation.objects.create(
            user=self.user,
            date=self.tomorrow,
            start_time=time(12, 30),
            end_time=time(13, 30),
            status='PENDING'
        )
        data = {
            'action': 'reject',
            'rejection_reason': 'Not available'
        }
        response = self.client.post(f'/api/reservations/{reservation.id}/approve/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, 'REJECTED')
        self.assertEqual(reservation.rejection_reason, 'Not available')

# --- CALENDAR API TESTS ---

class CalendarAPITests(APITestCase):
    """
    Calendar API scenarios:
    - Calendar view generation
    - Date range filtering
    - Slot availability logic
    - Primetime indication
    """
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.tomorrow = date.today() + timedelta(days=1)
        CalendarSettings.objects.create(
            business_start_time=time(9, 0),
            business_end_time=time(17, 0),
            slot_duration_minutes=60
        )
        PrimeTimeSettings.objects.create(
            weekday=self.tomorrow.weekday(),
            start_time=time(12, 0),
            end_time=time(14, 0),
            is_active=True
        )

    def test_get_calendar_view(self):
        """
        Scenario: User views calendar for a date range
        Postman/SvelteKit: GET /api/reservations/calendar/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
        """
        self.client.force_authenticate(user=self.user)
        Reservation.objects.create(
            user=self.user,
            date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0)
        )
        response = self.client.get(f'/api/reservations/calendar/?start_date={self.tomorrow}&end_date={self.tomorrow}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertIn('calendar', data)
        self.assertEqual(len(data['calendar']), 1)
        day_data = data['calendar'][0]
        self.assertEqual(day_data['date'], self.tomorrow.isoformat())
        self.assertIn('available_slots', day_data)
        self.assertIn('reserved_slots', day_data)

# --- TRADE API TESTS ---

class TradeAPITests(APITestCase):
    """
    Trade API scenarios:
    - Trade request creation
    - Trade acceptance
    - Trade rejection
    """
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        tomorrow = date.today() + timedelta(days=1)
        self.reservation1 = Reservation.objects.create(
            user=self.user1,
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            status='CONFIRMED'
        )
        self.reservation2 = Reservation.objects.create(
            user=self.user2,
            date=tomorrow,
            start_time=time(14, 0),
            end_time=time(15, 0),
            status='CONFIRMED'
        )

    def test_create_trade_request(self):
        """
        Scenario: User requests a trade
        Postman/SvelteKit: POST /api/reservations/trades/
        """
        self.client.force_authenticate(user=self.user1)
        data = {
            'requester_reservation_id': self.reservation1.id,
            'target_reservation_id': self.reservation2.id,
            'message': 'Would like to trade'
        }
        response = self.client.post('/api/reservations/trades/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TradeRequest.objects.count(), 1)

    def test_accept_trade_request(self):
        """
        Scenario: Target user accepts trade (reservations swapped)
        Postman/SvelteKit: POST /api/reservations/trades/{id}/ with action=accept
        """
        trade = TradeRequest.objects.create(
            requester=self.user1,
            target_user=self.user2,
            requester_reservation=self.reservation1,
            target_reservation=self.reservation2
        )
        self.client.force_authenticate(user=self.user2)
        data = {'action': 'accept'}
        response = self.client.post(f'/api/reservations/trades/{trade.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reservation1.refresh_from_db()
        self.reservation2.refresh_from_db()
        self.assertEqual(self.reservation1.user, self.user2)
        self.assertEqual(self.reservation2.user, self.user1)

    def test_reject_trade_request(self):
        """
        Scenario: Target user rejects trade
        Postman/SvelteKit: POST /api/reservations/trades/{id}/ with action=reject
        """
        trade = TradeRequest.objects.create(
            requester=self.user1,
            target_user=self.user2,
            requester_reservation=self.reservation1,
            target_reservation=self.reservation2
        )
        self.client.force_authenticate(user=self.user2)
        data = {
            'action': 'reject',
            'response_message': 'Not interested'
        }
        response = self.client.post(f'/api/reservations/trades/{trade.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        trade.refresh_from_db()
        self.assertEqual(trade.status, 'REJECTED')

# --- PRIMETIME API TESTS ---

class PrimeTimeAPITests(APITestCase):
    """
    Primetime API scenarios:
    - Admin creates primetime settings
    - Regular user cannot create primetime
    - Admin lists primetime settings
    """
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpass123'
        )

    def test_admin_create_primetime_settings(self):
        """
        Scenario: Admin creates primetime settings
        Postman/SvelteKit: POST /api/reservations/admin/primetime/ as admin
        """
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'weekday': 1,
            'start_time': '12:00:00',
            'end_time': '14:00:00',
            'is_active': True
        }
        response = self.client.post('/api/reservations/admin/primetime/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PrimeTimeSettings.objects.count(), 1)

    def test_regular_user_cannot_create_primetime(self):
        """
        Scenario: Regular user tries to create primetime (should fail)
        Postman/SvelteKit: POST /api/reservations/admin/primetime/ as regular user
        """
        self.client.force_authenticate(user=self.regular_user)
        data = {
            'weekday': 1,
            'start_time': '12:00:00',
            'end_time': '14:00:00',
            'is_active': True
        }
        response = self.client.post('/api/reservations/admin/primetime/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_list_primetime_settings(self):
        """
        Scenario: Admin lists primetime settings
        Postman/SvelteKit: GET /api/reservations/admin/primetime/ as admin
        """
        self.client.force_authenticate(user=self.admin_user)
        PrimeTimeSettings.objects.create(
            weekday=1,
            start_time=time(12, 0),
            end_time=time(14, 0),
            is_active=True
        )
        response = self.client.get('/api/reservations/admin/primetime/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

# --- DASHBOARD API TESTS ---

class DashboardAPITests(APITestCase):
    """
    Dashboard API scenarios:
    - User dashboard data
    - Admin dashboard data
    - Regular user cannot access admin dashboard
    """
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
        tomorrow = date.today() + timedelta(days=1)
        self.reservation = Reservation.objects.create(
            user=self.user,
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(11, 0),
            status='CONFIRMED'
        )

    def test_user_dashboard(self):
        """
        Scenario: User views their dashboard
        Postman/SvelteKit: GET /api/reservations/dashboard/ as user
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/reservations/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertIn('upcoming_reservations', data)
        self.assertIn('pending_trades', data)
        self.assertIn('recent_activity', data)

    def test_admin_dashboard(self):
        """
        Scenario: Admin views their dashboard
        Postman/SvelteKit: GET /api/reservations/admin/dashboard/ as admin
        """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/reservations/admin/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertIn('pending_approvals', data)
        self.assertIn('todays_reservations', data)
        self.assertIn('recent_activity', data)

    def test_regular_user_cannot_access_admin_dashboard(self):
        """
        Scenario: Regular user tries to access admin dashboard (should fail)
        Postman/SvelteKit: GET /api/reservations/admin/dashboard/ as regular user
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/reservations/admin/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
