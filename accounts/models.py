from django.db import models
from django.contrib.auth.models import AbstractUser
from shared.models import BaseModel
from django.conf import settings
import uuid
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User

# === USER ROLE ===
class UserRole(models.TextChoices):
    BASIC = 'basic', 'Basic User'
    MANAGER = 'manager', 'Manager'
    ADMIN = 'admin', 'Admin'

# === AUTH TYPE ===
class AuthType(models.TextChoices):
    EMAIL = 'email', 'Email'
    PHONE = 'phone', 'Phone'
    SOCIAL = 'social', 'Social'

# === AUTH STATUS / REGISTRATION STEP ===
class AuthStatus(models.TextChoices):
    NEW = 'new', 'New'
    CODE_VERIFIED = 'code_verified', 'Code Verified'
    PROFILE_COMPLETED = 'completed', 'Profile Completed'
    PHOTO_UPLOADED = 'photo_uploaded', 'Photo Uploaded'


class User(AbstractUser, BaseModel):
    # --- ROLE ---
    user_role = models.CharField(
        max_length=31,
        choices=UserRole.choices,
        default=UserRole.BASIC
    )

    # --- AUTH TYPE ---
    auth_type = models.CharField(
        max_length=31,
        choices=AuthType.choices,
        default=AuthType.EMAIL
    )

    # --- AUTH STATUS ---
    auth_status = models.CharField(
        max_length=31,
        choices=AuthStatus.choices,
        default=AuthStatus.NEW
    )

    # --- CONTACTS ---
    email = models.EmailField(null=True, blank=True, unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True, unique=True)

    def __str__(self):
        return self.username


class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)

    followers_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}"

class UserConfirmation(BaseModel):
    TYPE_CHOICES = (
        ('email_verification', 'Email Verification'),
        ('phone_verification', 'Phone Verification'),
        ('password_reset', 'Password Reset'),   
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='confirmations')
    confirmation_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    code = models.CharField(max_length=6, null=True, blank=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):

        # expires_at belgilanmagan bo‘lsa — default 5 minut
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=5)

        # agar code bo‘lmasa — random 6 xonali 6-digit code
        if not self.code:
            self.code = str(uuid.uuid4().int)[:6].zfill(6)
        
        super().save(*args, **kwargs)

    def is_expired(self):
        """Kod muddati tugagan-tugamaganligini qaytaradi."""
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"Confirmation for {self.user.email} - {self.confirmation_type}"
    