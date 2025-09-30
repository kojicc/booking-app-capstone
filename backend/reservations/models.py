from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from datetime import datetime, time, date

User = get_user_model()

class PrimeTimeSettings(models.Model):
    """Admin-configurable primetime hours for each day of the week"""
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES, unique=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['weekday']
    
    def __str__(self):
        return f"{self.get_weekday_display()}: {self.start_time} - {self.end_time}"
    
    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")

class Reservation(models.Model):
    """Main reservation model"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('CONFIRMED', 'Confirmed'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]
    
    RESERVATION_TYPE_CHOICES = [
        ('FREE_FOR_ALL', 'Free for All'),
        ('PRIMETIME', 'Primetime'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reservation_type = models.CharField(max_length=20, choices=RESERVATION_TYPE_CHOICES)
    notes = models.TextField(blank=True)
    
    # Admin fields
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_reservations')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['date', 'start_time', 'end_time']
    
    def __str__(self):
        return f"{self.user.email} - {self.date} {self.start_time}-{self.end_time}"
    
    def clean(self):
        # Validate time range
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")
        
        # Validate business hours (7 AM - 7 PM)
        business_start = time(7, 0)
        business_end = time(19, 0)
        
        if self.start_time < business_start or self.end_time > business_end:
            raise ValidationError("Reservations must be between 7 AM and 7 PM")
        
        # Check for overlapping reservations
        overlapping = Reservation.objects.filter(
            date=self.date,
            status__in=['CONFIRMED', 'PENDING']
        ).exclude(pk=self.pk)
        
        for reservation in overlapping:
            if (self.start_time < reservation.end_time and 
                self.end_time > reservation.start_time):
                raise ValidationError("This time slot overlaps with an existing reservation")
    
    def save(self, *args, **kwargs):
        # Auto-determine reservation type and status
        if not self.reservation_type:
            self.reservation_type = self.get_reservation_type()
        
        if not self.status or self.status == 'PENDING':
            if self.reservation_type == 'FREE_FOR_ALL':
                self.status = 'CONFIRMED'
            else:
                self.status = 'PENDING'
        
        super().save(*args, **kwargs)
    
    def get_reservation_type(self):
        """Determine if this reservation is in primetime hours"""
        try:
            weekday = self.date.weekday()
            primetime = PrimeTimeSettings.objects.get(weekday=weekday, is_active=True)
            
            if (self.start_time >= primetime.start_time and 
                self.end_time <= primetime.end_time):
                return 'PRIMETIME'
        except PrimeTimeSettings.DoesNotExist:
            pass
        
        return 'FREE_FOR_ALL'
    
    def is_editable(self):
        """Check if reservation can be edited"""
        return self.status in ['PENDING', 'CONFIRMED'] and self.date >= date.today()
    
    def can_be_traded(self):
        """Check if reservation can be traded"""
        return (self.status == 'CONFIRMED' and 
                self.date >= date.today() and 
                self.user.role == 'user')

class TradeRequest(models.Model):
    """Model for handling slot trades between users"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trade_requests_sent')
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trade_requests_received')
    
    # Reservations being traded
    requester_reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='trades_as_requester')
    target_reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='trades_as_target')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    message = models.TextField(blank=True, help_text="Optional message from requester")
    response_message = models.TextField(blank=True, help_text="Optional response from target user")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Trade: {self.requester.email} <-> {self.target_user.email}"
    
    def clean(self):
        # Validate that users can't trade with themselves
        if self.requester == self.target_user:
            raise ValidationError("Cannot trade with yourself")
        
        # Validate that both reservations can be traded
        if not self.requester_reservation.can_be_traded():
            raise ValidationError("Your reservation cannot be traded")
        
        if not self.target_reservation.can_be_traded():
            raise ValidationError("Target reservation cannot be traded")
        
        # Validate that requester owns their reservation
        if self.requester_reservation.user != self.requester:
            raise ValidationError("You can only trade your own reservations")
        
        # Validate that target user owns their reservation
        if self.target_reservation.user != self.target_user:
            raise ValidationError("Invalid target reservation")

class CalendarSettings(models.Model):
    """Global calendar settings"""
    business_start_time = models.TimeField(default=time(7, 0))
    business_end_time = models.TimeField(default=time(19, 0))
    slot_duration_minutes = models.IntegerField(default=60, help_text="Duration of each booking slot in minutes")
    max_advance_booking_days = models.IntegerField(default=30, help_text="Maximum days in advance users can book")
    allow_same_day_booking = models.BooleanField(default=True)
    
    # Email settings
    admin_email = models.EmailField(default="fjdreyes@gmail.com", help_text="Admin email for notifications")
    send_confirmation_emails = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Calendar Settings"
        verbose_name_plural = "Calendar Settings"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and CalendarSettings.objects.exists():
            raise ValidationError("Only one CalendarSettings instance is allowed")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Calendar Settings: {self.business_start_time} - {self.business_end_time}"

class ReservationAuditLog(models.Model):
    """Audit log for reservation changes"""
    ACTION_CHOICES = [
        ('CREATED', 'Created'),
        ('UPDATED', 'Updated'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
        ('TRADED', 'Traded'),
    ]
    
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.action} - {self.reservation} by {self.performed_by.email}"
