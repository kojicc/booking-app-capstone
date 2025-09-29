# users/views.py
import jwt
import os
import uuid
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import models
from .models import User, RefreshTokenBlacklist
from .serializers import UserSerializer
from reservations.views import IsAdminUser
from rest_framework import permissions

import os

class RegisterUser(APIView):
    permission_classes = []  # Allow unauthenticated access
    
    def post(self, request):
        try:
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)   

class UserList(APIView):
    # Only admins may list users. We return minimal/aggregated info to avoid leaking
    # personal data in bulk responses.
    # Use AllowAny here and perform explicit checks inside get() so we can
    # return 401 for unauthenticated requests (DRF permission checks run before
    # the view and may return 403 instead of 401 depending on auth backend).
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            # Explicitly return 401 when not authenticated to avoid returning 403 for anonymous
            if not request.user or not request.user.is_authenticated:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

            # If authenticated but not admin, return 403
            if request.user.role != 'admin':
                return Response(status=status.HTTP_403_FORBIDDEN)
            
            total = User.objects.count()
            by_role = (
                User.objects.values('role')
                .order_by()
                .annotate(count=models.Count('id'))
            )
            # Convert to a simple dict: { role: count }
            role_counts = {item['role']: item['count'] for item in by_role}
            return Response({'total_users': total, 'by_role': role_counts})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        try:
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserDetail(APIView):
    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
    def put(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        # Accept partial updates via PUT (tests expect this behavior)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class LoginUser(APIView):
    permission_classes = []  # Allow unauthenticated access

    def post(self, request):
        """Authenticate user, return access token and set HttpOnly refresh cookie.

        Frontend should store access token in memory and include it in Authorization
        headers. The refresh token is stored as an HttpOnly cookie and should be
        sent automatically by the browser when calling the refresh endpoint.
        """
        try:
            email = request.data.get("email")
            password = request.data.get("password")

            if not email or not password:
                return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.get(email=email)
            if not user.check_password(password):
                return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

            access_secret = getattr(settings, 'JWT_ACCESS_SECRET', os.getenv('JWT_ACCESS_SECRET', 'your-access-secret-key'))
            refresh_secret = getattr(settings, 'JWT_REFRESH_SECRET', os.getenv('JWT_REFRESH_SECRET', 'your-refresh-secret-key'))

            now = datetime.utcnow()
            access_payload = {
                "user_id": user.id,
                "email": user.email,
                # tests expect a 1-hour access token
                "exp": now + timedelta(hours=1),
                "iat": now,
                "type": "access"
            }

            refresh_jti = str(uuid.uuid4())
            refresh_payload = {
                "user_id": user.id,
                "exp": now + timedelta(days=7),
                "iat": now,
                "type": "refresh",
                "jti": refresh_jti
            }

            access_token = jwt.encode(access_payload, access_secret, algorithm="HS256")
            refresh_token = jwt.encode(refresh_payload, refresh_secret, algorithm="HS256")

            # Set refresh token as HttpOnly cookie
            # Tests expect a 'tokens' object; include both access and refresh there
            response = Response({
                "message": "Login successful",
                "tokens": {
                    "access": access_token,
                    "refresh": refresh_token
                },
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": getattr(user, 'first_name', ''),
                    "last_name": getattr(user, 'last_name', '')
                }
            }, status=status.HTTP_200_OK)

            cookie_max_age = 7 * 24 * 60 * 60  # 7 days in seconds
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                max_age=cookie_max_age,
                httponly=True,
                secure=True,  
                samesite='Lax'
            )

            return response

        except User.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({"error": "An error occurred during login"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RefreshTokenView(APIView):
    permission_classes = []

    def post(self, request):
        """Read refresh token from HttpOnly cookie, validate it, rotate tokens and set new refresh cookie.

        Return new access token in JSON. Frontend must call this endpoint with
        credentials included (fetch option `credentials: 'include'`).
        """
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            if not refresh_token:
                return Response({"error": "No refresh token provided"}, status=status.HTTP_401_UNAUTHORIZED)

            refresh_secret = getattr(settings, 'JWT_REFRESH_SECRET', os.getenv('JWT_REFRESH_SECRET', 'your-refresh-secret-key'))
            access_secret = getattr(settings, 'JWT_ACCESS_SECRET', os.getenv('JWT_ACCESS_SECRET', 'your-access-secret-key'))

            try:
                payload = jwt.decode(refresh_token, refresh_secret, algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                return Response({"error": "Refresh token expired"}, status=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                return Response({"error": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED)

            if payload.get('type') != 'refresh':
                return Response({"error": "Invalid token type"}, status=status.HTTP_401_UNAUTHORIZED)

            # Check blacklist
            token_jti = payload.get('jti')
            if token_jti and RefreshTokenBlacklist.objects.filter(jti=token_jti).exists():
                return Response({"error": "Refresh token has been revoked"}, status=status.HTTP_401_UNAUTHORIZED)

            user_id = payload.get('user_id')
            user = User.objects.filter(id=user_id).first()
            if not user:
                return Response({"error": "User not found"}, status=status.HTTP_401_UNAUTHORIZED)

            now = datetime.utcnow()
            access_payload = {
                "user_id": user.id,
                "email": user.email,
                "exp": now + timedelta(hours=1),
                "iat": now,
                "type": "access"
            }
            new_access = jwt.encode(access_payload, access_secret, algorithm="HS256")

            # Optionally rotate refresh token
            new_jti = str(uuid.uuid4())
            refresh_payload = {
                "user_id": user.id,
                "exp": now + timedelta(days=7),
                "iat": now,
                "type": "refresh",
                "jti": new_jti
            }
            new_refresh = jwt.encode(refresh_payload, refresh_secret, algorithm="HS256")

            # Blacklist the old refresh token jti (if present) to prevent reuse
            if token_jti:
                try:
                    exp_ts = payload.get('exp')
                    expires_at = datetime.utcfromtimestamp(exp_ts) if exp_ts else None
                    # make timezone-aware in UTC to avoid Django warnings
                    if expires_at is not None:
                        expires_at = timezone.make_aware(expires_at, timezone.utc)
                except Exception:
                    expires_at = None
                RefreshTokenBlacklist.objects.get_or_create(jti=token_jti, defaults={
                    'user': user,
                    'expires_at': expires_at
                })

            response = Response({"access": new_access}, status=status.HTTP_200_OK)
            cookie_max_age = 7 * 24 * 60 * 60
            response.set_cookie(
                key='refresh_token',
                value=new_refresh,
                max_age=cookie_max_age,
                httponly=True,
                secure=False,
                samesite='Lax'
            )

            return response

        except Exception as e:
            return Response({"error": "Could not refresh token"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogoutView(APIView):
    permission_classes = []

    def post(self, request):
        # Blacklist the refresh token if present so it can't be reused
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                refresh_secret = getattr(settings, 'JWT_REFRESH_SECRET', os.getenv('JWT_REFRESH_SECRET', 'your-refresh-secret-key'))
                payload = jwt.decode(refresh_token, refresh_secret, algorithms=["HS256"], options={"verify_exp": False})
                token_jti = payload.get('jti')
                user_id = payload.get('user_id')
                user = User.objects.filter(id=user_id).first() if user_id else None
                if token_jti:
                    expires_at = None
                    try:
                        exp_ts = payload.get('exp')
                        expires_at = datetime.utcfromtimestamp(exp_ts) if exp_ts else None
                        if expires_at is not None:
                            expires_at = timezone.make_aware(expires_at, timezone.utc)
                    except Exception:
                        expires_at = None
                    RefreshTokenBlacklist.objects.get_or_create(jti=token_jti, defaults={'user': user, 'expires_at': expires_at})
            except Exception:
                # If anything goes wrong decoding, proceed to delete cookie anyway
                pass

        response = Response({"message": "Logged out"}, status=status.HTTP_200_OK)
        response.delete_cookie('refresh_token')
        return response
                
        