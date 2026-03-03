"""
API Views for Posts

This module contains all API views for the posts app:
- PostCreateView: Create new posts
- PostDetailView: Get/Update/Delete posts
- FeedView: News feed from followed users
- ExploreView: Discover posts from non-followed users
- UserPostsView: Get user's posts
- LikeToggleView: Like/Unlike posts
- PostLikesListView: Get list of users who liked a post
- CommentListCreateView: List and create comments
- CommentDetailView: Get/Update/Delete comments
- CommentLikeToggleView: Like/Unlike comments
- SavedPostsListView: Get saved posts
- SavePostToggleView: Save/Unsave posts
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import (
    CreateAPIView,
    RetrieveUpdateDestroyAPIView,
    ListAPIView,
    ListCreateAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Post, PostImage, Like, Comment, CommentLike, SavedPost
from .serializers import (
    PostCreateSerializer,
    PostListSerializer,
    PostDetailSerializer,
    PostUpdateSerializer,
    CommentSerializer,
    CommentCreateSerializer,
    LikeSerializer,
    SavedPostSerializer,
)
from social.models import Follow


# ============================================
# PAGINATION
# ============================================

class PostPagination(PageNumberPagination):
    """
    Pagination for posts.
    Default: 20 posts per page
    Max: 100 posts per page
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CommentPagination(PageNumberPagination):
    """
    Pagination for comments.
    Default: 30 comments per page
    """
    page_size = 30
    page_size_query_param = 'page_size'
    max_page_size = 100


# ============================================
# POST CRUD VIEWS
# ============================================

class PostCreateView(CreateAPIView):
    """
    POST /api/posts/
    
    Create a new post with 1-10 images.
    
    Request:
        - caption (optional): Post caption
        - location (optional): Location string
        - images (required): List of 1-10 image files
    
    Response:
        - success: True
        - message: "Post created successfully"
        - data: Full post object with images
    """
    serializer_class = PostCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data.setlist('images', request.FILES.getlist('images'))
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        post = serializer.save()
        
        # Return full post details
        response_serializer = PostDetailSerializer(
            post,
            context={'request': request}
        )
        
        return Response({
            'success': True,
            'message': 'Post created successfully',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)


class PostDetailView(RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/DELETE /api/posts/{id}/
    
    Get, update, or delete a specific post.
    Only the post owner can update or delete.
    
    GET: Returns full post details
    PUT: Update caption and location only
    DELETE: Soft delete (or hard delete based on settings)
    """
    queryset = Post.objects.select_related('user').prefetch_related(
        'images',
        'likes',
        'comments'
    )
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PostDetailSerializer
        return PostUpdateSerializer
    
    def update(self, request, *args, **kwargs):
        """Only owner can update"""
        post = self.get_object()
        if post.user != request.user:
            return Response({
                'success': False,
                'message': 'You can only edit your own posts'
            }, status=status.HTTP_403_FORBIDDEN)
        
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(post, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return updated post with full details
        response_serializer = PostDetailSerializer(
            post,
            context={'request': request}
        )
        
        return Response({
            'success': True,
            'message': 'Post updated successfully',
            'data': response_serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Only owner can delete"""
        post = self.get_object()
        if post.user != request.user:
            return Response({
                'success': False,
                'message': 'You can only delete your own posts'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Hard delete (or set is_archived=True for soft delete)
        post.delete()
        
        return Response({
            'success': True,
            'message': 'Post deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)


# ============================================
# FEED VIEWS
# ============================================

class FeedView(ListAPIView):
    """
    GET /api/posts/feed/
    
    News feed - posts from users you follow + your own posts.
    Sorted by creation date (newest first).
    
    Query Parameters:
        - page: Page number (default: 1)
        - page_size: Posts per page (default: 20, max: 100)
    
    Returns:
        Paginated list of posts
    """
    serializer_class = PostListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PostPagination
    
    def get_queryset(self):
        user = self.request.user
        
        # Get users that current user follows
        following_users = Follow.objects.filter(
            follower=user
        ).values_list('following_id', flat=True)
        
        # Posts from followed users + own posts
        return Post.objects.filter(
            Q(user__in=following_users) | Q(user=user),
            is_archived=False
        ).select_related('user').prefetch_related(
            'images',
            'likes',
            'comments'
        ).order_by('-created_at')


class ExploreView(ListAPIView):
    """
    GET /api/posts/explore/
    
    Explore page - posts from users you DON'T follow.
    Discover new content.
    
    Query Parameters:
        - page: Page number
        - page_size: Posts per page
    
    Returns:
        Paginated list of posts
    """
    serializer_class = PostListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PostPagination
    
    def get_queryset(self):
        user = self.request.user
        
        # Get users that current user follows
        following_users = Follow.objects.filter(
            follower=user
        ).values_list('following_id', flat=True)
        
        # Posts from users NOT followed (excluding own posts)
        return Post.objects.filter(
            is_archived=False
        ).exclude(
            Q(user__in=following_users) | Q(user=user)
        ).select_related('user').prefetch_related(
            'images',
            'likes'
        ).order_by('-created_at')


class UserPostsView(ListAPIView):
    """
    GET /api/posts/users/{username}/
    
    Get all posts from a specific user.
    Public view - can see any user's posts.
    
    Path Parameters:
        - username: User's username
    
    Returns:
        Paginated list of user's posts
    """
    serializer_class = PostListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PostPagination
    
    def get_queryset(self):
        username = self.kwargs.get('username')
        return Post.objects.filter(
            user__username=username,
            is_archived=False
        ).select_related('user').prefetch_related(
            'images',
            'likes'
        ).order_by('-created_at')


# ============================================
# LIKE VIEWS
# ============================================

class LikeToggleView(APIView):
    """
    POST /api/posts/{post_id}/like/
    
    Toggle like on a post.
    If already liked -> unlike
    If not liked -> like
    
    Response:
        - success: True
        - message: "Post liked" or "Post unliked"
        - data:
            - liked: Boolean
            - likes_count: Updated count
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        user = request.user
        
        # Check if like exists
        like = Like.objects.filter(user=user, post=post)
        
        if like.exists():
            # Unlike
            like.delete()
            liked = False
            message = 'Post unliked'
        else:
            # Like
            Like.objects.create(user=user, post=post)
            liked = True
            message = 'Post liked'
        
        # Get updated count
        post.refresh_from_db()
        
        return Response({
            'success': True,
            'message': message,
            'data': {
                'liked': liked,
                'likes_count': post.likes_count
            }
        })


class PostLikesListView(ListAPIView):
    """
    GET /api/posts/{post_id}/likes/
    
    Get list of users who liked a post.
    Sorted by most recent first.
    
    Returns:
        Paginated list of likes with user info
    """
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PostPagination
    
    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        return Like.objects.filter(
            post_id=post_id
        ).select_related('user').order_by('-created_at')


# ============================================
# COMMENT VIEWS
# ============================================

class CommentListCreateView(ListCreateAPIView):
    """
    GET/POST /api/posts/{post_id}/comments/
    
    List comments on a post or create a new comment.
    
    GET: Returns top-level comments (no replies)
    POST: Create a new comment (or reply if parent is provided)
    
    Request (POST):
        - text (required): Comment text
        - parent (optional): Parent comment ID for replies
    """
    permission_classes = [IsAuthenticated]
    pagination_class = CommentPagination
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommentCreateSerializer
        return CommentSerializer
    
    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        # Only top-level comments (replies are nested in serializer)
        return Comment.objects.filter(
            post_id=post_id,
            parent=None
        ).select_related('user').prefetch_related('replies').order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, id=post_id)
        
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request, 'post_id': post_id}
        )
        serializer.is_valid(raise_exception=True)
        
        # Create comment
        comment = Comment.objects.create(
            post=post,
            user=request.user,
            text=serializer.validated_data['text'],
            parent=serializer.validated_data.get('parent')
        )
        
        # Return full comment data
        response_serializer = CommentSerializer(
            comment,
            context={'request': request}
        )
        
        return Response({
            'success': True,
            'message': 'Comment added successfully',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)


class CommentDetailView(RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/DELETE /api/posts/comments/{id}/
    
    Get, update, or delete a specific comment.
    
    DELETE: Owner or post owner can delete
    PUT: Only owner can update
    """
    queryset = Comment.objects.select_related('user', 'post')
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        """Only comment owner can update"""
        comment = self.get_object()
        if comment.user != request.user:
            return Response({
                'success': False,
                'message': 'You can only edit your own comments'
            }, status=status.HTTP_403_FORBIDDEN)
        
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(comment, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'success': True,
            'message': 'Comment updated successfully',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Owner or post owner can delete"""
        comment = self.get_object()
        
        # Check permissions
        if comment.user != request.user and comment.post.user != request.user:
            return Response({
                'success': False,
                'message': 'You can only delete your own comments or comments on your posts'
            }, status=status.HTTP_403_FORBIDDEN)
        
        comment.delete()
        
        return Response({
            'success': True,
            'message': 'Comment deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)


class CommentLikeToggleView(APIView):
    """
    POST /api/posts/comments/{comment_id}/like/
    
    Toggle like on a comment.
    Similar to post like toggle.
    
    Response:
        - success: True
        - message: "Comment liked" or "Comment unliked"
        - data:
            - liked: Boolean
            - likes_count: Updated count
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)
        user = request.user
        
        # Check if like exists
        like = CommentLike.objects.filter(user=user, comment=comment)
        
        if like.exists():
            # Unlike
            like.delete()
            liked = False
            message = 'Comment unliked'
        else:
            # Like
            CommentLike.objects.create(user=user, comment=comment)
            liked = True
            message = 'Comment liked'
        
        # Get updated count
        comment.refresh_from_db()
        
        return Response({
            'success': True,
            'message': message,
            'data': {
                'liked': liked,
                'likes_count': comment.likes_count
            }
        })


# ============================================
# SAVED POSTS VIEWS
# ============================================

class SavedPostsListView(ListAPIView):
    """
    GET /api/posts/saved/
    
    Get user's saved posts.
    Only returns current user's saved posts.
    
    Returns:
        Paginated list of saved posts with full post data
    """
    serializer_class = SavedPostSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PostPagination
    
    def get_queryset(self):
        return SavedPost.objects.filter(
            user=self.request.user
        ).select_related('post__user').prefetch_related(
            'post__images'
        ).order_by('-created_at')


class SavePostToggleView(APIView):
    """
    POST /api/posts/{post_id}/save/
    
    Toggle save on a post.
    If already saved -> unsave
    If not saved -> save
    
    Response:
        - success: True
        - message: "Post saved" or "Post removed from saved"
        - data:
            - is_saved: Boolean
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        user = request.user
        
        # Check if already saved
        saved = SavedPost.objects.filter(user=user, post=post)
        
        if saved.exists():
            # Unsave
            saved.delete()
            is_saved = False
            message = 'Post removed from saved'
        else:
            # Save
            SavedPost.objects.create(user=user, post=post)
            is_saved = True
            message = 'Post saved successfully'
        
        return Response({
            'success': True,
            'message': message,
            'data': {
                'is_saved': is_saved
            }
        })
