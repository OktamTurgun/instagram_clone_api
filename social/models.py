from django.db import models
from django.conf import settings
from shared.models import BaseModel
from django.db.models import Q


class Follow(BaseModel):
    """
    Follow relationship between users.
    
    follower: User who follows
    following: User being followed
    """
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following_set',  # user.following_set.all() → users I follow
        help_text="User who is following"
    )
    
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='followers_set',  # user.followers_set.all() → my followers
        help_text="User being followed"
    )
    
    class Meta:
        # Ensure unique follow relationship
        unique_together = ('follower', 'following')
        
        # Database indexes for performance
        indexes = [
            models.Index(fields=['follower', 'following']),
            models.Index(fields=['following', 'follower']),
        ]
        
        # Ordering
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"
    
    def save(self, *args, **kwargs):
        """Prevent self-follow"""
        if self.follower == self.following:
            from django.core.exceptions import ValidationError
            raise ValidationError("Users cannot follow themselves")
        
        super().save(*args, **kwargs)
    
    @classmethod
    def is_following(cls, follower, following):
        """Check if follower follows following"""
        return cls.objects.filter(
            follower=follower,
            following=following
        ).exists()
    
    @classmethod
    def get_mutual_followers(cls, user1, user2):
        """Get users who both user1 and user2 follow"""
        user1_following = set(
            cls.objects.filter(follower=user1).values_list('following_id', flat=True)
        )
        user2_following = set(
            cls.objects.filter(follower=user2).values_list('following_id', flat=True)
        )
        
        mutual_ids = user1_following & user2_following
        from accounts.models import User
        return User.objects.filter(id__in=mutual_ids)
