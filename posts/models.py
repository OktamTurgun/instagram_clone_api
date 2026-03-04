from django.db import models
"""
posts/models.py - Posts, Images, Likes, Comments
"""
from django.db import models
from django.core.validators import FileExtensionValidator
from accounts.models import User
from shared.models import BaseModel
from shared.utils import optimize_image

class Post(BaseModel):
    """
    Post modeli - Foydalanuvchi yuklagan post
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    caption = models.TextField(max_length=2200, blank=True)
    location = models.CharField(max_length=100, blank=True)
    
    # Hisoblagichlar
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    
    # Yashirish
    is_archived = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"Post by @{self.user.username} - {self.created_at.strftime('%Y-%m-%d')}"


class PostImage(BaseModel):
    """
    Post rasmlari - bir postda 1-10 ta rasm
    """
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        upload_to='posts/%Y/%m/%d/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'webp']
            )
        ]
    )
    order = models.PositiveSmallIntegerField(default=0)
    
    # 2. Save metodini optimallashtirish uchun qo'shamiz
    def save(self, *args, **kwargs):
        if self.image:
            # Rasmni siqish va WebP ga o'tkazish
            self.image = optimize_image(self.image)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['post', 'order']),
        ]
    
    def __str__(self):
        return f"Image {self.order} for Post {self.post.id}"


class Like(BaseModel):
    """
    Like modeli - postga like
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    
    class Meta:
        unique_together = ('user', 'post')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"@{self.user.username} liked post {self.post.id}"


class Comment(BaseModel):
    """
    Comment modeli - postga komment
    """
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField(max_length=500)
    
    # Reply uchun
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    
    likes_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['parent', '-created_at']),
        ]
    
    def __str__(self):
        return f"@{self.user.username}: {self.text[:50]}..."
    
    @property
    def is_reply(self):
        return self.parent is not None


class CommentLike(BaseModel):
    """
    CommentLike - kommentga like
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comment_likes'
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='comment_likes'
    )
    
    class Meta:
        unique_together = ('user', 'comment')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"@{self.user.username} liked comment"


class SavedPost(BaseModel):
    """
    SavedPost - saqlangan postlar
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_posts'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='saved_by'
    )
    
    class Meta:
        unique_together = ('user', 'post')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"@{self.user.username} saved post {self.post.id}"
