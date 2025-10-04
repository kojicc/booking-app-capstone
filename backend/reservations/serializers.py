# reservations/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Reservation, 
    PrimeTimeSettings, 
    TradeRequest, 
    CalendarSettings,
    ReservationAuditLog
)
from datetime import date, datetime, timedelta

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for reservations"""
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role']

class PrimeTimeSettingsSerializer(serializers.ModelSerializer):
    weekday_display = serializers.CharField(source='get_weekday_display', read_only=True)
    
    class Meta:
        model = PrimeTimeSettings
        fields = ['id', 'weekday', 'weekday_display', 'start_time', 'end_time', 'is_active']

class ReservationSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    approved_by = UserBasicSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reservation_type_display = serializers.CharField(source='get_reservation_type_display', read_only=True)
    is_editable = serializers.SerializerMethodField()
    can_be_traded = serializers.SerializerMethodField()
    
    class Meta:
        model = Reservation
        fields = [
            'id', 'user', 'booking_name', 'date', 'start_time', 'end_time', 
            'status', 'status_display', 'reservation_type', 'reservation_type_display',
            'notes', 'approved_by', 'approved_at', 'rejection_reason',
            'is_editable', 'can_be_traded', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'approved_by', 'approved_at', 'reservation_type']
    
    def get_is_editable(self, obj):
        return obj.is_editable()
    
    def get_can_be_traded(self, obj):
        return obj.can_be_traded()
    
    def validate_date(self, value):
        if value < date.today():
            raise serializers.ValidationError("Cannot book dates in the past")
        return value

    def validate(self, data):
        """Ensure the requested slot doesn't overlap with existing reservations
        that are CONFIRMED or PENDING for the same date.
        """
        # Ensure required fields are present for overlap checking
        date_val = data.get('date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        if date_val and start_time and end_time:
            overlapping = Reservation.objects.filter(
                date=date_val,
                status__in=['CONFIRMED', 'PENDING']
            )

            # If serializer is used for update, exclude the instance
            instance = getattr(self, 'instance', None)
            if instance:
                overlapping = overlapping.exclude(pk=instance.pk)

            for res in overlapping:
                # overlapping if start < existing_end and end > existing_start
                if (start_time < res.end_time and end_time > res.start_time):
                    raise serializers.ValidationError("This time slot overlaps with an existing reservation")

        return data
    
    def validate(self, data):
        # Additional validation can be added here
        return data

class ReservationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reservations"""
    class Meta:
        model = Reservation
        fields = ['booking_name', 'date', 'start_time', 'end_time', 'notes']
    
    def validate_date(self, value):
        if value < date.today():
            raise serializers.ValidationError("Cannot book dates in the past")
        
        # Check max advance booking
        try:
            settings = CalendarSettings.objects.first()
            if settings and settings.max_advance_booking_days:
                max_date = date.today() + timedelta(days=settings.max_advance_booking_days)
                if value > max_date:
                    raise serializers.ValidationError(
                        f"Cannot book more than {settings.max_advance_booking_days} days in advance"
                    )
        except:
            pass
        
        return value
    
    def create(self, validated_data):
        from django.db import transaction

        request = self.context.get('request')
        user = request.user if request else None
        validated_data['user'] = user

        # Protect against race conditions by running overlap check and create inside
        # a database transaction with a row-level lock on existing reservations
        # for the same date. This uses select_for_update to serialize concurrent
        # attempts that target the same date window.
        date_val = validated_data.get('date')
        start_time = validated_data.get('start_time')
        end_time = validated_data.get('end_time')

        with transaction.atomic():
            if date_val and start_time and end_time:
                overlapping_qs = Reservation.objects.select_for_update().filter(
                    date=date_val,
                    status__in=['CONFIRMED', 'PENDING']
                )

                # No need to exclude instance because this is creation
                for res in overlapping_qs:
                    if (start_time < res.end_time and end_time > res.start_time):
                        raise serializers.ValidationError("This time slot overlaps with an existing reservation")

            return super().create(validated_data)

class TradeRequestSerializer(serializers.ModelSerializer):
    requester = UserBasicSerializer(read_only=True)
    target_user = UserBasicSerializer(read_only=True)
    requester_reservation = ReservationSerializer(read_only=True)
    target_reservation = ReservationSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = TradeRequest
        fields = [
            'id', 'requester', 'target_user', 'requester_reservation', 'target_reservation',
            'status', 'status_display', 'message', 'response_message',
            'created_at', 'updated_at', 'responded_at'
        ]
        read_only_fields = ['requester', 'target_user', 'responded_at']

class TradeRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating trade requests"""
    target_reservation_id = serializers.IntegerField(write_only=True)
    requester_reservation_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = TradeRequest
        fields = ['target_reservation_id', 'requester_reservation_id', 'message']
    
    def validate(self, data):
        user = self.context['request'].user
        
        # Validate requester reservation
        try:
            requester_reservation = Reservation.objects.get(
                id=data['requester_reservation_id'],
                user=user
            )
        except Reservation.DoesNotExist:
            raise serializers.ValidationError("Invalid requester reservation")
        
        # Validate target reservation
        try:
            target_reservation = Reservation.objects.get(id=data['target_reservation_id'])
        except Reservation.DoesNotExist:
            raise serializers.ValidationError("Invalid target reservation")
        
        # Validate trade feasibility
        if not requester_reservation.can_be_traded():
            raise serializers.ValidationError("Your reservation cannot be traded")
        
        if not target_reservation.can_be_traded():
            raise serializers.ValidationError("Target reservation cannot be traded")
        
        data['requester_reservation'] = requester_reservation
        data['target_reservation'] = target_reservation
        data['target_user'] = target_reservation.user
        
        return data
    
    def create(self, validated_data):
        validated_data['requester'] = self.context['request'].user
        return super().create(validated_data)

class CalendarSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarSettings
        fields = [
            'business_start_time', 'business_end_time', 'slot_duration_minutes',
            'max_advance_booking_days', 'allow_same_day_booking',
            'admin_email', 'send_confirmation_emails'
        ]

class ReservationAuditLogSerializer(serializers.ModelSerializer):
    performed_by = UserBasicSerializer(read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = ReservationAuditLog
        fields = ['id', 'action', 'action_display', 'performed_by', 'details', 'timestamp']

class CalendarDaySerializer(serializers.Serializer):
    """Serializer for calendar day view"""
    date = serializers.DateField()
    is_primetime = serializers.BooleanField()
    primetime_hours = serializers.DictField(required=False)
    available_slots = serializers.ListField(child=serializers.DictField())
    reserved_slots = serializers.ListField(child=ReservationSerializer())
    business_hours = serializers.DictField()

class ReservationApprovalSerializer(serializers.Serializer):
    """Serializer for approving/rejecting reservations"""
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        if data['action'] == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError("Rejection reason is required when rejecting")
        return data
