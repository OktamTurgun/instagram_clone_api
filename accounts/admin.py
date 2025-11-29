from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
  list_display = ("id", "username", "email", "is_active", "is_staff", "created_at")
  search_fields = ("email",)
  list_filter = ("is_active", "is_staff", "created_at")
