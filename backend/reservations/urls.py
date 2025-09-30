from django.urls import path, include
from .views import (
    # Reservation views
    ReservationListView,
    ReservationDetailView,
    ReservationApprovalView,
    
    # Calendar views
    CalendarView,
    
    # Admin views
    PrimeTimeSettingsView,
    PrimeTimeSettingsDetailView,
    
    # Trade views
    TradeRequestListView,
    TradeRequestDetailView,
    
    # Settings views
    CalendarSettingsView,
    
    # Dashboard views
    UserDashboardView,
    AdminDashboardView,
)

urlpatterns = [
    # ===================== RESERVATION ENDPOINTS =====================
    # GET /api/reservations/ - List user's reservations (or all for admin)
    # POST /api/reservations/ - Create new reservation
    path('', ReservationListView.as_view(), name='reservation-list'),
    
    # GET /api/reservations/{id}/ - Get specific reservation
    # PUT /api/reservations/{id}/ - Update reservation
    # DELETE /api/reservations/{id}/ - Cancel reservation
    path('<int:pk>/', ReservationDetailView.as_view(), name='reservation-detail'),
    
    # POST /api/reservations/{id}/approve/ - Admin approve/reject reservation
    path('<int:pk>/approve/', ReservationApprovalView.as_view(), name='reservation-approval'),
    
    # ===================== CALENDAR ENDPOINTS =====================
    # GET /api/reservations/calendar/ - Get calendar view with available/booked slots
    path('calendar/', CalendarView.as_view(), name='calendar-view'),
    
    # ===================== TRADE ENDPOINTS =====================
    # GET /api/reservations/trades/ - List user's trade requests (sent/received)
    # POST /api/reservations/trades/ - Create new trade request
    path('trades/', TradeRequestListView.as_view(), name='trade-list'),
    
    # GET /api/reservations/trades/{id}/ - Get specific trade request
    # POST /api/reservations/trades/{id}/ - Accept/reject trade request
    path('trades/<int:pk>/', TradeRequestDetailView.as_view(), name='trade-detail'),
    
    # ===================== ADMIN ENDPOINTS =====================
    # GET /api/reservations/admin/primetime/ - List primetime settings
    # POST /api/reservations/admin/primetime/ - Create primetime setting
    path('admin/primetime/', PrimeTimeSettingsView.as_view(), name='primetime-list'),
    
    # GET /api/reservations/admin/primetime/{id}/ - Get specific primetime setting
    # PUT /api/reservations/admin/primetime/{id}/ - Update primetime setting
    # DELETE /api/reservations/admin/primetime/{id}/ - Delete primetime setting
    path('admin/primetime/<int:pk>/', PrimeTimeSettingsDetailView.as_view(), name='primetime-detail'),
    
    # GET /api/reservations/admin/settings/ - Get calendar settings
    # PUT /api/reservations/admin/settings/ - Update calendar settings
    path('admin/settings/', CalendarSettingsView.as_view(), name='calendar-settings'),
    
    # ===================== DASHBOARD ENDPOINTS =====================
    # GET /api/reservations/dashboard/ - User dashboard
    path('dashboard/', UserDashboardView.as_view(), name='user-dashboard'),

    
    # GET /api/reservations/admin/dashboard/ - Admin dashboard
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
]