# reservations/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import get_user_model
from django.conf import settings
from backend.utils.email import send_html_email
from django.db import transaction
from datetime import date, datetime, timedelta, time
from django.utils import timezone

from .models import (
    Reservation, 
    PrimeTimeSettings, 
    TradeRequest, 
    CalendarSettings,
    ReservationAuditLog
)
from .serializers import (
    ReservationSerializer, 
    ReservationCreateSerializer,
    PrimeTimeSettingsSerializer,
    TradeRequestSerializer,
    TradeRequestCreateSerializer,
    CalendarSettingsSerializer,
    CalendarDaySerializer,
    ReservationApprovalSerializer,
    ReservationAuditLogSerializer
)

User = get_user_model()

class IsAdminUser(permissions.BasePermission):
    """Custom permission for admin users"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

class IsOwnerOrAdmin(permissions.BasePermission):
    """Custom permission for owners or admin users"""
    def has_object_permission(self, request, view, obj):
        return (request.user.is_authenticated and 
                (obj.user == request.user or request.user.role == 'admin'))

# ===================== RESERVATION VIEWS =====================

class ReservationListView(APIView):
    """List all reservations with filtering options

    Permission handling is enforced inside the methods to ensure the view returns
    401 Unauthorized for unauthenticated POST requests when using the custom
    authentication backend (which otherwise caused DRF to return 403).
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        # Require authentication for listing user-specific reservations
        if not request.user or not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        queryset = Reservation.objects.all()

        # Filter by user role
        if request.user.role != 'admin':
            queryset = queryset.filter(user=request.user)
        
        # Apply filters
        date_filter = request.query_params.get('date')
        status_filter = request.query_params.get('status')
        user_filter = request.query_params.get('user')
        
        if date_filter:
            queryset = queryset.filter(date=date_filter)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if user_filter and request.user.role == 'admin':
            queryset = queryset.filter(user__email__icontains=user_filter)
        
        serializer = ReservationSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create a new reservation"""
        # Require authentication to create reservations
        if not request.user or not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = ReservationCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                reservation = serializer.save()
                
                # Log the creation
                ReservationAuditLog.objects.create(
                    reservation=reservation,
                    action='CREATED',
                    performed_by=request.user,
                    details={'initial_status': reservation.status}
                )
                
                # Send confirmation email
                self._send_confirmation_email(reservation)
                
                return Response(
                    ReservationSerializer(reservation).data, 
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _send_confirmation_email(self, reservation):
        """Send confirmation email"""
        try:
            calendar_settings = CalendarSettings.objects.first()
            if not calendar_settings or not calendar_settings.send_confirmation_emails:
                return
            subject = f"Reservation {'Confirmed' if reservation.status == 'CONFIRMED' else 'Pending Approval'}"
            preheader = 'Thank you for choosing our service.'
            content = (
                f"Dear {reservation.user.first_name or reservation.user.email},<br/><br/>"
                f"Your reservation has been <strong>{'confirmed' if reservation.status == 'CONFIRMED' else 'submitted and is pending approval'}</strong>.<br/><br/>"
                "Please find the reservation details below. If you have any questions, reply to this email."
            )
            details = (
                f"Date: {reservation.date}\n"
                f"Time: {reservation.start_time} - {reservation.end_time}\n"
                f"Type: {reservation.get_reservation_type_display()}\n"
                f"Status: {reservation.get_status_display()}\n"
            )

            send_html_email(
                subject=subject,
                to_email=reservation.user.email,
                content=content,
                details=details,
                preheader=preheader,
                from_email=settings.DEFAULT_FROM_EMAIL,
                fail_silently=True
            )
        except Exception:
            pass  # Don't fail the request if email fails

class ReservationDetailView(APIView):
    """Retrieve, update, or delete a specific reservation"""
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_object(self, pk):
        try:
            reservation = Reservation.objects.get(pk=pk)
            self.check_object_permissions(self.request, reservation)
            return reservation
        except Reservation.DoesNotExist:
            return None
    
    def get(self, request, pk):
        reservation = self.get_object(pk)
        if not reservation:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        serializer = ReservationSerializer(reservation)
        return Response(serializer.data)
    
    def put(self, request, pk):
        reservation = self.get_object(pk)
        if not reservation:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        if not reservation.is_editable():
            return Response(
                {'error': 'This reservation cannot be edited due to its status or date constraints.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ReservationCreateSerializer(
            reservation, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            old_data = ReservationSerializer(reservation).data
            updated_reservation = serializer.save()
            
            # Log the update
            ReservationAuditLog.objects.create(
                reservation=updated_reservation,
                action='UPDATED',
                performed_by=request.user,
                details={'old_data': old_data, 'new_data': ReservationSerializer(updated_reservation).data}
            )
            
            return Response(ReservationSerializer(updated_reservation).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        reservation = self.get_object(pk)
        if not reservation:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        if not reservation.is_editable():
            return Response(
                {'error': 'This reservation cannot be cancelled due to its status or date constraints.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Log the cancellation
        ReservationAuditLog.objects.create(
            reservation=reservation,
            action='CANCELLED',
            performed_by=request.user
        )
        
        reservation.status = 'CANCELLED'
        reservation.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)

# ===================== CALENDAR VIEWS =====================

class CalendarView(APIView):
    """Get calendar view with available and booked slots"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Get date range
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date:
            start_date = date.today()
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if not end_date:
            end_date = start_date + timedelta(days=7)  # Default to 1 week
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        calendar_data = []
        current_date = start_date
        
        while current_date <= end_date:
            day_data = self._get_day_data(current_date)
            calendar_data.append(day_data)
            current_date += timedelta(days=1)
        
        return Response({
            'start_date': start_date,
            'end_date': end_date,
            'calendar': calendar_data
        })
    
    def _get_day_data(self, target_date):
        """Get data for a specific day"""
        # Get calendar settings
        calendar_settings = CalendarSettings.objects.first()
        business_start = calendar_settings.business_start_time if calendar_settings else time(7, 0)
        business_end = calendar_settings.business_end_time if calendar_settings else time(19, 0)
        slot_duration = calendar_settings.slot_duration_minutes if calendar_settings else 60
        
        # Get primetime settings for this day
        weekday = target_date.weekday()
        primetime_settings = None
        is_primetime_day = False
        
        try:
            primetime_settings = PrimeTimeSettings.objects.get(weekday=weekday, is_active=True)
            is_primetime_day = True
        except PrimeTimeSettings.DoesNotExist:
            pass
        
        # Get existing reservations for this day
        reservations = Reservation.objects.filter(
            date=target_date,
            status__in=['CONFIRMED', 'PENDING']
        ).order_by('start_time')
        
        # Generate available time slots
        available_slots = self._generate_available_slots(
            target_date, business_start, business_end, slot_duration, reservations
        )
        
        return {
            'date': target_date.isoformat(),
            'is_primetime': is_primetime_day,
            'primetime_hours': {
                'start_time': primetime_settings.start_time.isoformat() if primetime_settings else None,
                'end_time': primetime_settings.end_time.isoformat() if primetime_settings else None
            } if primetime_settings else None,
            'business_hours': {
                'start_time': business_start.isoformat(),
                'end_time': business_end.isoformat()
            },
            'available_slots': available_slots,
            'reserved_slots': ReservationSerializer(reservations, many=True).data
        }
    
    def _generate_available_slots(self, target_date, start_time, end_time, duration_minutes, existing_reservations):
        """Generate available time slots for a day"""
        slots = []
        current_time = datetime.combine(target_date, start_time)
        end_datetime = datetime.combine(target_date, end_time)
        
        while current_time < end_datetime:
            slot_end = current_time + timedelta(minutes=duration_minutes)
            
            if slot_end.time() <= end_time:
                # Check if slot conflicts with existing reservations
                is_available = True
                slot_type = 'FREE_FOR_ALL'
                
                # Check primetime
                try:
                    weekday = target_date.weekday()
                    primetime = PrimeTimeSettings.objects.get(weekday=weekday, is_active=True)
                    if (current_time.time() >= primetime.start_time and 
                        slot_end.time() <= primetime.end_time):
                        slot_type = 'PRIMETIME'
                except PrimeTimeSettings.DoesNotExist:
                    pass
                
                # Check conflicts
                for reservation in existing_reservations:
                    res_start = datetime.combine(target_date, reservation.start_time)
                    res_end = datetime.combine(target_date, reservation.end_time)
                    
                    if (current_time < res_end and slot_end > res_start):
                        is_available = False
                        break
                
                if is_available:
                    slots.append({
                        'start_time': current_time.time().isoformat(),
                        'end_time': slot_end.time().isoformat(),
                        'type': slot_type,
                        'available': True
                    })
            
            current_time += timedelta(minutes=duration_minutes)
        
        return slots

# ===================== ADMIN VIEWS =====================

class ReservationApprovalView(APIView):
    """Admin view to approve/reject reservations"""
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def post(self, request, pk):
        try:
            reservation = Reservation.objects.get(pk=pk)
        except Reservation.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        serializer = ReservationApprovalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        action = serializer.validated_data['action']
        
        with transaction.atomic():
            if action == 'approve':
                reservation.status = 'CONFIRMED'
                reservation.approved_by = request.user
                reservation.approved_at = timezone.now()
                log_action = 'APPROVED'
                
            else:  # reject
                reservation.status = 'REJECTED'
                reservation.rejection_reason = serializer.validated_data.get('rejection_reason', '')
                log_action = 'REJECTED'
            
            reservation.save()
            
            ReservationAuditLog.objects.create(
                reservation=reservation,
                action=log_action,
                performed_by=request.user,
                details=serializer.validated_data
            )
        
        # Send notification email
        self._send_approval_email(reservation, action)
        
        return Response(ReservationSerializer(reservation).data)
    
    def _send_approval_email(self, reservation, action):
        """Send approval/rejection email"""
        try:
            subject = f"Reservation {action.title()}"
            preheader = 'Update on your reservation request.'
            content = (
                f"Dear {reservation.user.first_name or reservation.user.email},<br/><br/>"
                f"Your reservation has been <strong>{'approved' if action == 'approve' else 'rejected'}</strong>."
            )
            details = (
                f"Date: {reservation.date}\n"
                f"Time: {reservation.start_time} - {reservation.end_time}\n"
                f"Status: {reservation.get_status_display()}\n"
                + (f"Reason: {reservation.rejection_reason}\n" if action == 'reject' and reservation.rejection_reason else '')
            )

            send_html_email(
                subject=subject,
                to_email=reservation.user.email,
                content=content,
                details=details,
                preheader=preheader,
                from_email=settings.DEFAULT_FROM_EMAIL,
                fail_silently=True
            )
        except Exception:
            pass

class PrimeTimeSettingsView(APIView):
    """Admin view to manage primetime settings"""
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get(self, request):
        settings = PrimeTimeSettings.objects.all()
        serializer = PrimeTimeSettingsSerializer(settings, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = PrimeTimeSettingsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PrimeTimeSettingsDetailView(APIView):
    """Admin view to manage individual primetime settings"""
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get_object(self, pk):
        try:
            return PrimeTimeSettings.objects.get(pk=pk)
        except PrimeTimeSettings.DoesNotExist:
            return None
    
    def get(self, request, pk):
        settings = self.get_object(pk)
        if not settings:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        serializer = PrimeTimeSettingsSerializer(settings)
        return Response(serializer.data)
    
    def put(self, request, pk):
        settings = self.get_object(pk)
        if not settings:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        serializer = PrimeTimeSettingsSerializer(settings, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        settings = self.get_object(pk)
        if not settings:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        settings.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# ===================== TRADE VIEWS =====================

class TradeRequestListView(APIView):
    """List and create trade requests"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Get trade requests where user is involved
        sent_requests = TradeRequest.objects.filter(requester=request.user)
        received_requests = TradeRequest.objects.filter(target_user=request.user)
        
        sent_serializer = TradeRequestSerializer(sent_requests, many=True)
        received_serializer = TradeRequestSerializer(received_requests, many=True)
        
        return Response({
            'sent_requests': sent_serializer.data,
            'received_requests': received_serializer.data
        })
    
    def post(self, request):
        serializer = TradeRequestCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            trade_request = serializer.save()
            return Response(
                TradeRequestSerializer(trade_request).data, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TradeRequestDetailView(APIView):
    """Handle individual trade requests"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self, pk, user):
        try:
            return TradeRequest.objects.get(
                pk=pk,
                target_user=user,
                status='PENDING'
            )
        except TradeRequest.DoesNotExist:
            return None
    
    def get(self, request, pk):
        trade_request = TradeRequest.objects.filter(
            pk=pk,
            requester=request.user
        ).first() or TradeRequest.objects.filter(
            pk=pk,
            target_user=request.user
        ).first()
        
        if not trade_request:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        serializer = TradeRequestSerializer(trade_request)
        return Response(serializer.data)
    
    def post(self, request, pk):
        """Accept or reject a trade request"""
        trade_request = self.get_object(pk, request.user)
        if not trade_request:
            return Response(
                {'error': 'Trade request not found or already processed'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        action = request.data.get('action')  # 'accept' or 'reject'
        response_message = request.data.get('response_message', '')
        
        if action not in ['accept', 'reject']:
            return Response(
                {'error': 'Action must be either "accept" or "reject"'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            if action == 'accept':
                # Swap the reservations
                req_reservation = trade_request.requester_reservation
                target_reservation = trade_request.target_reservation
                
                # Swap users
                original_req_user = req_reservation.user
                original_target_user = target_reservation.user
                
                req_reservation.user = original_target_user
                target_reservation.user = original_req_user
                
                req_reservation.save()
                target_reservation.save()
                
                trade_request.status = 'ACCEPTED'
                
                # Log the trades
                ReservationAuditLog.objects.create(
                    reservation=req_reservation,
                    action='TRADED',
                    performed_by=request.user,
                    details={'traded_with': original_target_user.email, 'trade_id': trade_request.id}
                )
                
                ReservationAuditLog.objects.create(
                    reservation=target_reservation,
                    action='TRADED',
                    performed_by=request.user,
                    details={'traded_with': original_req_user.email, 'trade_id': trade_request.id}
                )
                
            else:  # reject
                trade_request.status = 'REJECTED'
            
            trade_request.response_message = response_message
            trade_request.responded_at = timezone.now()
            trade_request.save()
        
        return Response(TradeRequestSerializer(trade_request).data)

# ===================== SETTINGS VIEWS =====================

class CalendarSettingsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        settings = CalendarSettings.objects.first()
        if not settings:
            # Create default settings
            settings = CalendarSettings.objects.create()
        
        serializer = CalendarSettingsSerializer(settings)
        return Response(serializer.data)
    
    def put(self, request):
        settings = CalendarSettings.objects.first()
        if not settings:
            settings = CalendarSettings()
        
        serializer = CalendarSettingsSerializer(settings, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ===================== UTILITY VIEWS =====================


# Converted user_dashboard to APIView
class UserDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        today = date.today()

        # Get user's upcoming reservations
        upcoming_reservations = Reservation.objects.filter(
            user=user,
            date__gte=today,
            status__in=['CONFIRMED', 'PENDING']
        ).order_by('date', 'start_time')[:5]

        # Get pending trade requests
        pending_trades_sent = TradeRequest.objects.filter(
            requester=user,
            status='PENDING'
        ).count()

        pending_trades_received = TradeRequest.objects.filter(
            target_user=user,
            status='PENDING'
        ).count()

        # Get recent activity
        recent_logs = ReservationAuditLog.objects.filter(
            reservation__user=user
        ).order_by('-timestamp')[:10]

        return Response({
            'upcoming_reservations': ReservationSerializer(upcoming_reservations, many=True).data,
            'pending_trades': {
                'sent': pending_trades_sent,
                'received': pending_trades_received
            },
            'recent_activity': ReservationAuditLogSerializer(recent_logs, many=True).data
        })


# Converted admin_dashboard to APIView
class AdminDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def get(self, request):
        today = date.today()

        # Pending approvals
        pending_approvals = Reservation.objects.filter(
            status='PENDING',
            reservation_type='PRIMETIME'
        ).count()

        # Today's reservations
        todays_reservations = Reservation.objects.filter(
            date=today,
            status='CONFIRMED'
        ).count()

        # Recent activity
        recent_logs = ReservationAuditLog.objects.all().order_by('-timestamp')[:20]

        return Response({
            'pending_approvals': pending_approvals,
            'todays_reservations': todays_reservations,
            'recent_activity': ReservationAuditLogSerializer(recent_logs, many=True).data
        })
