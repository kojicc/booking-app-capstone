from django.contrib import admin
from .models import (
    Reservation, 
    PrimeTimeSettings, 
    TradeRequest, 
    CalendarSettings,
    ReservationAuditLog
)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'start_time', 'end_time', 'status', 'reservation_type', 'created_at']
    list_filter = ['status', 'reservation_type', 'date', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(PrimeTimeSettings)
class PrimeTimeSettingsAdmin(admin.ModelAdmin):
    list_display = ['weekday', 'get_weekday_display', 'start_time', 'end_time', 'is_active']
    list_filter = ['weekday', 'is_active']
    ordering = ['weekday']

@admin.register(TradeRequest)
class TradeRequestAdmin(admin.ModelAdmin):
    list_display = ['requester', 'target_user', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['requester__email', 'target_user__email']
    ordering = ['-created_at']

@admin.register(CalendarSettings)
class CalendarSettingsAdmin(admin.ModelAdmin):
    list_display = ['business_start_time', 'business_end_time', 'slot_duration_minutes', 'admin_email']
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not CalendarSettings.objects.exists()

@admin.register(ReservationAuditLog)
class ReservationAuditLogAdmin(admin.ModelAdmin):
    list_display = ['reservation', 'action', 'performed_by', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['reservation__user__email', 'performed_by__email']
    ordering = ['-timestamp']
    readonly_fields = ['reservation', 'action', 'performed_by', 'details', 'timestamp']
