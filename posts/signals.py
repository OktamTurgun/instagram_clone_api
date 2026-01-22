"""
Django Signals for Posts

This module contains signal handlers that automatically update
denormalized counters when related objects are created or deleted.

Signals:
- increment_post_likes: Like created -> Post.likes_count + 1
- decrement_post_likes: Like deleted -> Post.likes_count - 1
- increment_post_comments: Comment created -> Post.comments_count + 1
- decrement_post_comments: Comment deleted -> Post.comments_count - 1
- increment_comment_likes: CommentLike created -> Comment.likes_count + 1
- decrement_comment_likes: CommentLike deleted -> Comment.likes_count - 1

Why use signals?
- Automatic counter updates
- No manual count queries needed
- Database consistency
- Performance optimization (cached counts)
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from .models import Like, Comment, CommentLike


# ============================================
# POST LIKE SIGNALS
# ============================================

@receiver(post_save, sender=Like)
def increment_post_likes(sender, instance, created, **kwargs):
    """
    Increment post likes_count when a new like is created.
    
    Triggered: When Like object is saved
    Condition: Only on creation (created=True)
    Action: Post.likes_count += 1
    
    Args:
        sender: Like model class
        instance: The Like instance being saved
        created: Boolean, True if new object
        kwargs: Additional arguments
    """
    if created:
        post = instance.post
        
        # Use F() expression for atomic update (thread-safe)
        from django.db.models import F
        post.likes_count = F('likes_count') + 1
        post.save(update_fields=['likes_count'])
        
        # Refresh to get actual value (F() returns expression)
        post.refresh_from_db(fields=['likes_count'])


@receiver(post_delete, sender=Like)
def decrement_post_likes(sender, instance, **kwargs):
    """
    Decrement post likes_count when a like is deleted.
    
    Triggered: When Like object is deleted
    Action: Post.likes_count -= 1 (minimum 0)
    
    Args:
        sender: Like model class
        instance: The Like instance being deleted
        kwargs: Additional arguments
    """
    post = instance.post
    
    # Ensure count doesn't go below 0
    if post.likes_count > 0:
        from django.db.models import F
        post.likes_count = F('likes_count') - 1
        post.save(update_fields=['likes_count'])
        post.refresh_from_db(fields=['likes_count'])


# ============================================
# POST COMMENT SIGNALS
# ============================================

@receiver(post_save, sender=Comment)
def increment_post_comments(sender, instance, created, **kwargs):
    """
    Increment post comments_count when a new comment is created.
    
    Triggered: When Comment object is saved
    Condition: Only on creation (created=True)
    Action: Post.comments_count += 1
    
    Note: Counts all comments including replies
    """
    if created:
        post = instance.post
        
        from django.db.models import F
        post.comments_count = F('comments_count') + 1
        post.save(update_fields=['comments_count'])
        post.refresh_from_db(fields=['comments_count'])


@receiver(post_delete, sender=Comment)
def decrement_post_comments(sender, instance, **kwargs):
    """
    Decrement post comments_count when a comment is deleted.
    
    Triggered: When Comment object is deleted
    Action: Post.comments_count -= 1 (minimum 0)
    
    Note: Also decrements when reply is deleted
    """
    post = instance.post
    
    if post.comments_count > 0:
        from django.db.models import F
        post.comments_count = F('comments_count') - 1
        post.save(update_fields=['comments_count'])
        post.refresh_from_db(fields=['comments_count'])


# ============================================
# COMMENT LIKE SIGNALS
# ============================================

@receiver(post_save, sender=CommentLike)
def increment_comment_likes(sender, instance, created, **kwargs):
    """
    Increment comment likes_count when a new comment like is created.
    
    Triggered: When CommentLike object is saved
    Condition: Only on creation (created=True)
    Action: Comment.likes_count += 1
    """
    if created:
        comment = instance.comment
        
        from django.db.models import F
        comment.likes_count = F('likes_count') + 1
        comment.save(update_fields=['likes_count'])
        comment.refresh_from_db(fields=['likes_count'])


@receiver(post_delete, sender=CommentLike)
def decrement_comment_likes(sender, instance, **kwargs):
    """
    Decrement comment likes_count when a comment like is deleted.
    
    Triggered: When CommentLike object is deleted
    Action: Comment.likes_count -= 1 (minimum 0)
    """
    comment = instance.comment
    
    if comment.likes_count > 0:
        from django.db.models import F
        comment.likes_count = F('likes_count') - 1
        comment.save(update_fields=['likes_count'])
        comment.refresh_from_db(fields=['likes_count'])


# ============================================
# UTILITY SIGNALS (OPTIONAL)
# ============================================

@receiver(post_delete, sender=Comment)
def cascade_delete_comment_likes(sender, instance, **kwargs):
    """
    Clean up comment likes when comment is deleted.
    
    Note: This is handled by CASCADE in the model,
    but we keep it here for explicit tracking.
    
    Triggered: When Comment is deleted
    Action: Delete all associated CommentLikes
    """
    # Django CASCADE handles this automatically
    # This is just for logging/tracking if needed
    pass


# ============================================
# LOGGING (OPTIONAL - FOR DEBUGGING)
# ============================================

import logging
logger = logging.getLogger(__name__)

@receiver(post_save, sender=Like)
def log_like_creation(sender, instance, created, **kwargs):
    """
    Log like creation for debugging/analytics.
    
    Disabled in production for performance.
    """
    if created and logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            f"Like created: User {instance.user.username} "
            f"liked post {instance.post.id}"
        )


@receiver(post_save, sender=Comment)
def log_comment_creation(sender, instance, created, **kwargs):
    """
    Log comment creation for debugging/analytics.
    """
    if created and logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            f"Comment created: User {instance.user.username} "
            f"commented on post {instance.post.id}"
        )