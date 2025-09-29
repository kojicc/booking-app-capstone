from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        username = extra_fields.get('username') or email.split('@')[0]
        extra_fields['username'] = username
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    google_id = models.CharField(max_length=100, unique=True, null=True, blank=True,
                                help_text="Google OAuth sub claim")
    role = models.CharField(
        max_length=20,
        choices=[("admin", "Admin"), ("user", "User"), ("external", "External")],
        default="user"
    )
    email = models.EmailField(unique=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # username is still required, but not for login

    objects = CustomUserManager()
    
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
