from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Follow


@receiver(post_save, sender=Follow)
def update_counts_on_follow(sender, instance, created, **kwargs):
    """
    Update followers/following counts when follow is created
    """
    if created:
        # Update follower's following_count
        if hasattr(instance.follower, 'profile'):
            instance.follower.profile.following_count += 1
            instance.follower.profile.save()
        
        # Update following's followers_count
        if hasattr(instance.following, 'profile'):
            instance.following.profile.followers_count += 1
            instance.following.profile.save()


@receiver(post_delete, sender=Follow)
def update_counts_on_unfollow(sender, instance, **kwargs):
    """
    Update followers/following counts when follow is deleted
    """
    # Update follower's following_count
    if hasattr(instance.follower, 'profile'):
        instance.follower.profile.following_count = max(
            0,
            instance.follower.profile.following_count - 1
        )
        instance.follower.profile.save()
    
    # Update following's followers_count
    if hasattr(instance.following, 'profile'):
        instance.following.profile.followers_count = max(
            0,
            instance.following.profile.followers_count - 1
        )
        instance.following.profile.save()