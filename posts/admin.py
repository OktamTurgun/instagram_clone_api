"""
Django Admin Configuration for Posts

This module configures the Django admin interface for Posts app.
Provides a powerful interface for managing posts, comments, and likes.

Features:
- Post management with inline images
- Image preview in admin
- Comment moderation
- Like tracking
- Bulk actions
- Custom filters and search
- Read-only fields for system data
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Count
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import Post, PostImage, Like, Comment, CommentLike, SavedPost


# ============================================
# INLINE ADMINS
# ============================================

class PostImageInline(admin.TabularInline):
    """
    Inline admin for post images.
    
    Allows adding/editing images directly in the post form.
    Shows image preview for easy identification.
    """
    model = PostImage
    extra = 1  # Show 1 empty form by default
    max_num = 10  # Maximum 10 images per post
    fields = ['image', 'order', 'image_preview', 'created_at']
    readonly_fields = ['image_preview', 'created_at']
    ordering = ['order']
    
    def image_preview(self, obj):
        """
        Display image preview in admin.
        
        Args:
            obj: PostImage instance
            
        Returns:
            HTML img tag or placeholder text
        """
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 150px; '
                'object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return mark_safe('<span style="color: #999;">No image</span>')
    
    image_preview.short_description = 'Preview'


# ============================================
# POST ADMIN
# ============================================

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """
    Admin interface for Post model.
    
    Features:
    - Inline image management
    - Image preview in list
    - Search by user, caption, location
    - Filter by date, archived status
    - Bulk actions (archive, unarchive)
    - Read-only system fields
    """
    list_display = [
        'id_short',
        'user_link',
        'caption_preview',
        'first_image_preview',
        'image_count_display',
        'likes_count',
        'comments_count',
        'is_archived',
        'created_at_display'
    ]
    
    list_filter = [
        'is_archived',
        'created_at',
        ('user', admin.RelatedFieldListFilter),
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'caption',
        'location',
    ]
    
    readonly_fields = [
        'id',
        'likes_count',
        'comments_count',
        'created_at',
        'updated_at',
        'all_images_preview'
    ]
    
    fieldsets = (
        ('Post Information', {
            'fields': ('id', 'user', 'caption', 'location')
        }),
        ('Images', {
            'fields': ('all_images_preview',),
            'description': 'Post images are managed below'
        }),
        ('Statistics', {
            'fields': ('likes_count', 'comments_count'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_archived',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [PostImageInline]
    
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 25
    
    actions = ['archive_posts', 'unarchive_posts']
    
    # ============================================
    # CUSTOM DISPLAY METHODS
    # ============================================
    
    def id_short(self, obj):
        """Display shortened UUID"""
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'ID'
    
    def user_link(self, obj):
        """Display user with link to their admin page"""
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html(
            '<a href="{}" style="text-decoration: none;">'
            '<strong>@{}</strong></a>',
            url, obj.user.username
        )
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'
    
    def caption_preview(self, obj):
        """Display truncated caption"""
        if obj.caption:
            max_length = 50
            caption = obj.caption[:max_length]
            if len(obj.caption) > max_length:
                caption += '...'
            return caption
        return mark_safe('<span style="color: #999;">No caption</span>')
    caption_preview.short_description = 'Caption'
    
    def first_image_preview(self, obj):
        """Display first image thumbnail"""
        first_image = obj.images.first()
        if first_image and first_image.image:
            return format_html(
                '<img src="{}" style="height: 60px; width: 60px; '
                'object-fit: cover; border-radius: 4px;" />',
                first_image.image.url
            )
        return mark_safe('<span style="color: #999;">No images</span>')
    first_image_preview.short_description = 'Thumbnail'
    
    def image_count_display(self, obj):
        """Display number of images with icon"""
        count = obj.images.count()
        color = '#28a745' if count > 0 else '#999'
        return format_html(
            '<span style="color: {}; font-weight: bold;">📷 {}</span>',
            color, count
        )
    image_count_display.short_description = 'Images'
    
    def created_at_display(self, obj):
        """Display formatted creation date"""
        return obj.created_at.strftime('%d %b %Y, %H:%M')
    created_at_display.short_description = 'Created'
    created_at_display.admin_order_field = 'created_at'
    
    def all_images_preview(self, obj):
        """Display all images in detail view"""
        images = obj.images.all()
        if not images:
            return mark_safe('<p style="color: #999;">No images uploaded yet</p>')
        
        html = '<div style="display: flex; flex-wrap: wrap; gap: 10px;">'
        for img in images:
            html += format_html(
                '<div style="text-align: center;">'
                '<img src="{}" style="max-height: 150px; max-width: 150px; '
                'object-fit: cover; border-radius: 4px; border: 1px solid #ddd;" />'
                '<p style="margin: 5px 0; font-size: 12px; color: #666;">Order: {}</p>'
                '</div>',
                img.image.url, img.order
            )
        html += '</div>'
        return mark_safe(html)
    all_images_preview.short_description = 'All Images'
    
    # ============================================
    # BULK ACTIONS
    # ============================================
    
    @admin.action(description='Archive selected posts')
    def archive_posts(self, request, queryset):
        """Archive multiple posts at once"""
        updated = queryset.update(is_archived=True)
        self.message_user(
            request,
            f'{updated} post(s) archived successfully.',
            level='success'
        )
    
    @admin.action(description='Unarchive selected posts')
    def unarchive_posts(self, request, queryset):
        """Unarchive multiple posts at once"""
        updated = queryset.update(is_archived=False)
        self.message_user(
            request,
            f'{updated} post(s) unarchived successfully.',
            level='success'
        )


# ============================================
# POST IMAGE ADMIN
# ============================================

@admin.register(PostImage)
class PostImageAdmin(admin.ModelAdmin):
    """
    Admin interface for PostImage model.
    
    Standalone management of post images.
    """
    list_display = [
        'id_short',
        'post_link',
        'image_preview',
        'order',
        'created_at'
    ]
    
    list_filter = [
        'created_at',
        ('post', admin.RelatedFieldListFilter),
    ]
    
    search_fields = [
        'post__user__username',
        'post__caption',
    ]
    
    readonly_fields = ['id', 'created_at', 'updated_at', 'large_preview']
    
    fields = [
        'id',
        'post',
        'image',
        'large_preview',
        'order',
        'created_at',
        'updated_at'
    ]
    
    ordering = ['-created_at']
    
    def id_short(self, obj):
        """Shortened UUID"""
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'ID'
    
    def post_link(self, obj):
        """Link to post"""
        url = reverse('admin:posts_post_change', args=[obj.post.id])
        return format_html(
            '<a href="{}">Post by @{}</a>',
            url, obj.post.user.username
        )
    post_link.short_description = 'Post'
    
    def image_preview(self, obj):
        """Thumbnail preview"""
        if obj.image:
            return format_html(
                '<img src="{}" style="height: 60px; width: 60px; '
                'object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return 'No image'
    image_preview.short_description = 'Preview'
    
    def large_preview(self, obj):
        """Large preview in detail view"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 500px; border-radius: 8px; '
                'box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
                obj.image.url
            )
        return 'No image'
    large_preview.short_description = 'Image Preview'


# ============================================
# LIKE ADMIN
# ============================================

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    """
    Admin interface for Like model.
    
    Track and manage post likes.
    """
    list_display = [
        'id_short',
        'user_link',
        'post_link',
        'created_at'
    ]
    
    list_filter = [
        'created_at',
        ('user', admin.RelatedFieldListFilter),
    ]
    
    search_fields = [
        'user__username',
        'post__caption',
    ]
    
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fields = ['id', 'user', 'post', 'created_at', 'updated_at']
    
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 50
    
    def id_short(self, obj):
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'ID'
    
    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">@{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'
    
    def post_link(self, obj):
        url = reverse('admin:posts_post_change', args=[obj.post.id])
        caption = obj.post.caption[:30] if obj.post.caption else 'No caption'
        return format_html('<a href="{}">{}</a>', url, caption)
    post_link.short_description = 'Post'


# ============================================
# COMMENT ADMIN
# ============================================

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Admin interface for Comment model.
    
    Moderate comments with reply support.
    """
    list_display = [
        'id_short',
        'user_link',
        'post_link',
        'text_preview',
        'is_reply',
        'likes_count',
        'created_at'
    ]
    
    list_filter = [
        'created_at',
        ('user', admin.RelatedFieldListFilter),
        ('parent', admin.EmptyFieldListFilter),
    ]
    
    search_fields = [
        'user__username',
        'text',
        'post__caption',
    ]
    
    readonly_fields = [
        'id',
        'likes_count',
        'created_at',
        'updated_at'
    ]
    
    fields = [
        'id',
        'post',
        'user',
        'text',
        'parent',
        'likes_count',
        'created_at',
        'updated_at'
    ]
    
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 50
    
    actions = ['delete_selected_comments']
    
    def id_short(self, obj):
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'ID'
    
    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">@{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'
    
    def post_link(self, obj):
        url = reverse('admin:posts_post_change', args=[obj.post.id])
        caption = obj.post.caption[:20] if obj.post.caption else 'No caption'
        return format_html('<a href="{}">{}</a>', url, caption)
    post_link.short_description = 'Post'
    
    def text_preview(self, obj):
        """Display truncated comment text"""
        max_length = 50
        text = obj.text[:max_length]
        if len(obj.text) > max_length:
            text += '...'
        return text
    text_preview.short_description = 'Comment'
    
    @admin.action(description='Delete selected comments')
    def delete_selected_comments(self, request, queryset):
        """Bulk delete comments with confirmation"""
        count = queryset.count()
        queryset.delete()
        self.message_user(
            request,
            f'{count} comment(s) deleted successfully.',
            level='success'
        )


# ============================================
# COMMENT LIKE ADMIN
# ============================================

@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    """
    Admin interface for CommentLike model.
    """
    list_display = [
        'id_short',
        'user_link',
        'comment_preview',
        'created_at'
    ]
    
    list_filter = [
        'created_at',
        ('user', admin.RelatedFieldListFilter),
    ]
    
    search_fields = [
        'user__username',
        'comment__text',
    ]
    
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fields = ['id', 'user', 'comment', 'created_at', 'updated_at']
    
    ordering = ['-created_at']
    list_per_page = 50
    
    def id_short(self, obj):
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'ID'
    
    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">@{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    
    def comment_preview(self, obj):
        text = obj.comment.text[:40]
        if len(obj.comment.text) > 40:
            text += '...'
        return text
    comment_preview.short_description = 'Comment'


# ============================================
# SAVED POST ADMIN
# ============================================

@admin.register(SavedPost)
class SavedPostAdmin(admin.ModelAdmin):
    """
    Admin interface for SavedPost model.
    """
    list_display = [
        'id_short',
        'user_link',
        'post_link',
        'created_at'
    ]
    
    list_filter = [
        'created_at',
        ('user', admin.RelatedFieldListFilter),
    ]
    
    search_fields = [
        'user__username',
        'post__caption',
    ]
    
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fields = ['id', 'user', 'post', 'created_at', 'updated_at']
    
    ordering = ['-created_at']
    list_per_page = 50
    
    def id_short(self, obj):
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'ID'
    
    def user_link(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html('<a href="{}">@{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    
    def post_link(self, obj):
        url = reverse('admin:posts_post_change', args=[obj.post.id])
        caption = obj.post.caption[:30] if obj.post.caption else 'No caption'
        return format_html('<a href="{}">{}</a>', url, caption)
    post_link.short_description = 'Post'


# ============================================
# CUSTOM ADMIN SITE (OPTIONAL)
# ============================================

# Customize admin site header
admin.site.site_header = "Instagram Clone Admin"
admin.site.site_title = "Instagram Clone"
admin.site.index_title = "Welcome to Instagram Clone Administration"