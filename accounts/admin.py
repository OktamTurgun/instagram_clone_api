from django.contrib import admin
from .models import User, UserConfirmation

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
  list_display = ("id", "username", "email", "is_active", "is_staff", "created_at")
  search_fields = ("email",)
  list_filter = ("is_active", "is_staff", "created_at")

@admin.register(UserConfirmation)
class UserConfirmationAdmin(admin.ModelAdmin):
  list_display = ("id", "user", "confirmation_type", "expires_at", "created_at")
  search_fields = ("user__email", "confirmation_type")
  list_filter = ("expires_at", "confirmation_type", "created_at")