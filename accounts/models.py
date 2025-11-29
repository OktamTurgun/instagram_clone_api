from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import uuid
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models.signals import post_save
from django.dispatch import receiver

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


# ====== USER MODEL ======
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user_role = models.CharField(max_length=31, choices=UserRole.choices, default=UserRole.BASIC)
    auth_type = models.CharField(max_length=31, choices=AuthType.choices, default=AuthType.EMAIL)
    auth_status = models.CharField(max_length=31, choices=AuthStatus.choices, default=AuthStatus.NEW)

    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def check_username(self):
        if not self.username:
            raise ValidationError("Username bo'sh bo'lishi mumkin emas.")
        if len(self.username) < 3:
            raise ValidationError("Username kamida 3 ta belgidan iborat bo'lishi kerak.")
        if " " in self.username:
            raise ValidationError("Username ichida bo'sh joy bo'lmasligi kerak.")

    def hashing_password(self):
        if self.password and not self.password.startswith("pbkdf2_"):
            self.password = make_password(self.password)

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower()
        self.hashing_password()
        super().save(*args, **kwargs)

    def token(self):
        refresh = RefreshToken.for_user(self)
        return {"access": str(refresh.access_token), "refresh": str(refresh)}

    def __str__(self):
        return self.username or str(self.id)

# ====== PROFILE ======
class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)

    followers_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{getattr(self.user, 'username', self.user.id)}'s profile"

# ====== USER CONFIRMATION ======
class UserConfirmation(models.Model):
    TYPE_CHOICES = (
        ('email_verification', 'Email Verification'),
        ('phone_verification', 'Phone Verification'),
        ('password_reset', 'Password Reset'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='confirmations')
    confirmation_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    code = models.CharField(max_length=6, null=True, blank=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Confirmation for {self.user.email or self.user.phone_number} - {self.confirmation_type}"