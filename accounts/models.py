from django.db import models
from django.contrib.auth.models import AbstractUser
from shared.models import BaseModel

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

