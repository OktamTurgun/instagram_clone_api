from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    User yaratilganda Profile yaratadi.
    User yangilanganda Profile update qiladi (agar mavjud bo'lsa).
    """
    if created:
        # Yangi user yaratilgan - Profile yaratamiz
        Profile.objects.get_or_create(user=instance)
    else:
        # User yangilangan - Profile ni sync qilamiz (agar mavjud bo'lsa)
        if hasattr(instance, 'profile'):
            instance.profile.save()