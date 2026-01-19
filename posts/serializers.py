"""
API Serializers for Posts

This module contains all serializers for the posts app:
- UserMinimalSerializer: Compact user info for post lists
- PostImageSerializer: Image data with URLs
- PostCreateSerializer: Creating new posts with validation
- PostListSerializer: List view with computed fields
- PostDetailSerializer: Detailed view with comments
- CommentSerializer: Comment data with permissions
- LikeSerializer: Like information
- SavedPostSerializer: Saved posts data
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Post, PostImage, Like, Comment, CommentLike, SavedPost

User = get_user_model()


# ============================================
# USER SERIALIZERS
# ============================================

class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal user information for efficient data transfer.
    Used in post lists, comments, likes to avoid over-fetching.
    """
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'avatar']
        read_only_fields = fields
    
    def get_avatar(self, obj):
        """Return full URL for avatar image"""
        if hasattr(obj, 'profile') and obj.profile.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile.avatar.url)
        return None


# ============================================
# POST IMAGE SERIALIZERS
# ============================================

class PostImageSerializer(serializers.ModelSerializer):
    """
    Post image serializer with full URL.
    Handles image ordering and display.
    """
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PostImage
        fields = ['id', 'image', 'image_url', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_image_url(self, obj):
        """Return absolute URL for the image"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None


# ============================================
# POST SERIALIZERS
# ============================================

class PostCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new posts.
    
    Handles:
    - Multiple image uploads (1-10 images)
    - Caption and location
    - Automatic user assignment from request
    - Image validation
    """
    images = serializers.ListField(
        child=serializers.ImageField(
            max_length=100000,
            allow_empty_file=False,
            use_url=False
        ),
        write_only=True,
        min_length=1,
        max_length=10,
        help_text="Upload 1-10 images"
    )
    
    class Meta:
        model = Post
        fields = ['caption', 'location', 'images']
    
    def validate_images(self, value):
        """
        Validate uploaded images:
        - Check file size (max 10MB per image)
        - Validate image format
        """
        max_size = 10 * 1024 * 1024  # 10MB
        
        for image in value:
            if image.size > max_size:
                raise serializers.ValidationError(
                    f"Image {image.name} is too large. Max size is 10MB."
                )
        
        return value
    
    def create(self, validated_data):
        """
        Create post with images.
        
        Process:
        1. Extract images from validated data
        2. Get user from request context
        3. Create Post instance
        4. Create PostImage instances for each image
        """
        images_data = validated_data.pop('images')
        request = self.context.get('request')
        
        if not request or not request.user:
            raise serializers.ValidationError("Authentication required")
        
        # Create post
        post = Post.objects.create(
            user=request.user,
            caption=validated_data.get('caption', ''),
            location=validated_data.get('location', '')
        )
        
        # Create images
        for idx, image in enumerate(images_data):
            PostImage.objects.create(
                post=post,
                image=image,
                order=idx
            )
        
        return post


class PostListSerializer(serializers.ModelSerializer):
    """
    Serializer for post lists (feed, explore, user posts).
    
    Includes:
    - User info
    - Images
    - Interaction flags (is_liked, is_saved, can_edit)
    - Counters (likes_count, comments_count)
    """
    user = UserMinimalSerializer(read_only=True)
    images = PostImageSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'user', 'caption', 'location',
            'images', 'likes_count', 'comments_count',
            'is_liked', 'is_saved', 'can_edit',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_is_liked(self, obj):
        """Check if current user liked this post"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(
                user=request.user,
                post=obj
            ).exists()
        return False
    
    def get_is_saved(self, obj):
        """Check if current user saved this post"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return SavedPost.objects.filter(
                user=request.user,
                post=obj
            ).exists()
        return False
    
    def get_can_edit(self, obj):
        """Check if current user can edit this post"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False


class PostDetailSerializer(PostListSerializer):
    """
    Detailed post serializer with comments and recent likes.
    
    Extends PostListSerializer with:
    - Recent comments (top 3)
    - Recent likes (top 5 users)
    """
    recent_comments = serializers.SerializerMethodField()
    recent_likes = serializers.SerializerMethodField()
    
    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + [
            'recent_comments',
            'recent_likes'
        ]
    
    def get_recent_comments(self, obj):
        """Get top 3 recent comments (excluding replies)"""
        comments = obj.comments.filter(parent=None).select_related('user')[:3]
        return CommentSerializer(
            comments,
            many=True,
            context=self.context
        ).data
    
    def get_recent_likes(self, obj):
        """Get users who recently liked (top 5)"""
        recent_likes = obj.likes.select_related('user').order_by('-created_at')[:5]
        return UserMinimalSerializer(
            [like.user for like in recent_likes],
            many=True,
            context=self.context
        ).data


class PostUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating posts.
    Only caption and location can be updated.
    """
    class Meta:
        model = Post
        fields = ['caption', 'location']
    
    def validate(self, data):
        """Ensure only owner can update"""
        request = self.context.get('request')
        if request and self.instance:
            if self.instance.user != request.user:
                raise serializers.ValidationError(
                    "You can only edit your own posts"
                )
        return data


# ============================================
# COMMENT SERIALIZERS
# ============================================

class CommentSerializer(serializers.ModelSerializer):
    """
    Comment serializer with nested replies support.
    
    Features:
    - User info
    - Reply support (parent comment)
    - Like status
    - Permission checks (can_delete)
    """
    user = UserMinimalSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'text', 'parent',
            'likes_count', 'is_liked', 'is_reply',
            'replies', 'can_delete', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'likes_count', 'is_reply']
    
    def get_replies(self, obj):
        """
        Get nested replies (limited to 3).
        Only show replies for top-level comments.
        """
        if obj.is_reply:
            return None  # Don't show nested replies of replies
        
        replies = obj.replies.select_related('user')[:3]
        # Prevent infinite recursion by not including 'replies' in nested serialization
        return CommentSerializer(
            replies,
            many=True,
            context=self.context
        ).data
    
    def get_is_liked(self, obj):
        """Check if current user liked this comment"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CommentLike.objects.filter(
                user=request.user,
                comment=obj
            ).exists()
        return False
    
    def get_can_delete(self, obj):
        """
        Check if current user can delete this comment.
        Owner or post owner can delete.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return (
                obj.user == request.user or 
                obj.post.user == request.user
            )
        return False
    
    def create(self, validated_data):
        """Create comment with user from request"""
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Authentication required")
        
        validated_data['user'] = request.user
        return super().create(validated_data)


class CommentCreateSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for creating comments.
    """
    class Meta:
        model = Comment
        fields = ['text', 'parent']
    
    def validate_parent(self, value):
        """
        Validate parent comment:
        - Must exist
        - Must belong to same post
        """
        if value:
            post_id = self.context.get('post_id')
            if value.post.id != post_id:
                raise serializers.ValidationError(
                    "Parent comment must belong to the same post"
                )
        return value


# ============================================
# LIKE SERIALIZERS
# ============================================

class LikeSerializer(serializers.ModelSerializer):
    """
    Like information with user details.
    """
    user = UserMinimalSerializer(read_only=True)
    
    class Meta:
        model = Like
        fields = ['id', 'user', 'created_at']
        read_only_fields = fields


# ============================================
# SAVED POST SERIALIZERS
# ============================================

class SavedPostSerializer(serializers.ModelSerializer):
    """
    Saved post with full post details.
    """
    post = PostListSerializer(read_only=True)
    
    class Meta:
        model = SavedPost
        fields = ['id', 'post', 'created_at']
        read_only_fields = fields