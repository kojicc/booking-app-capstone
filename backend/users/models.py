from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class User(AbstractUser):
    google_id = models.CharField(max_length=100, unique=True, null=True, blank=True,
                                help_text="Google OAuth sub claim")
    role = models.CharField(
        max_length=20,
        choices=[("admin", "Admin"), ("user", "User"), ("external", "External")],
        default="user"
    )
    # make username optional to support email-only signups
    username = models.CharField(max_length=150, null=True, blank=True)
    email = models.EmailField(unique=True)
    
    USERNAME_FIELD = 'email'
    # No required fields beyond email for createsuperuser/management tasks
    REQUIRED_FIELDS = []

    # Use Django's default manager (no custom manager)
    objects = UserManager()
    
    # Add related_name to avoid conflicts with default User model
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )

    def __str__(self):
        return self.username or self.email


class RefreshTokenBlacklist(models.Model):
    """Store blacklisted refresh tokens by their jti (unique id).
    """
    jti = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey('User', null=True, blank=True, on_delete=models.CASCADE)
    revoked_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Blacklisted refresh token {self.jti} (user={self.user_id})"
