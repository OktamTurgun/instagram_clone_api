"""
posts/urls.py - URL Configuration for Posts API

This module defines all URL patterns for the posts app.
All URLs are prefixed with /api/posts/ in the main config.

URL Structure:
- /api/posts/ - Post CRUD
- /api/posts/feed/ - News feed
- /api/posts/explore/ - Discover posts
- /api/posts/saved/ - Saved posts
- /api/posts/{id}/ - Post detail
- /api/posts/{id}/like/ - Like toggle
- /api/posts/{id}/save/ - Save toggle
- /api/posts/{id}/comments/ - Comments
- /api/posts/comments/{id}/ - Comment detail
- /api/posts/users/{username}/ - User posts
"""
from django.urls import path
from .views import (
    # Post CRUD
    PostCreateView,
    PostDetailView,
    
    # Feeds
    FeedView,
    ExploreView,
    UserPostsView,
    
    # Likes
    LikeToggleView,
    PostLikesListView,
    
    # Comments
    CommentListCreateView,
    CommentDetailView,
    CommentLikeToggleView,
    
    # Saved Posts
    SavedPostsListView,
    SavePostToggleView,
)

app_name = 'posts'

urlpatterns = [
    # ============================================
    # POST CRUD
    # ============================================
    
    # Create new post
    path(
        '',
        PostCreateView.as_view(),
        name='post-create'
    ),
    
    # Get/Update/Delete specific post
    path(
        '<uuid:pk>/',
        PostDetailView.as_view(),
        name='post-detail'
    ),
    
    
    # ============================================
    # FEEDS
    # ============================================
    
    # News feed (following + own posts)
    path(
        'feed/',
        FeedView.as_view(),
        name='feed'
    ),
    
    # Explore (discover new posts)
    path(
        'explore/',
        ExploreView.as_view(),
        name='explore'
    ),
    
    # User's posts
    path(
        'users/<str:username>/',
        UserPostsView.as_view(),
        name='user-posts'
    ),
    
    
    # ============================================
    # SAVED POSTS
    # ============================================
    
    # Get saved posts list
    path(
        'saved/',
        SavedPostsListView.as_view(),
        name='saved-posts'
    ),
    
    # Toggle save on post
    path(
        '<uuid:post_id>/save/',
        SavePostToggleView.as_view(),
        name='save-toggle'
    ),
    
    
    # ============================================
    # LIKES
    # ============================================
    
    # Toggle like on post
    path(
        '<uuid:post_id>/like/',
        LikeToggleView.as_view(),
        name='like-toggle'
    ),
    
    # List users who liked post
    path(
        '<uuid:post_id>/likes/',
        PostLikesListView.as_view(),
        name='post-likes'
    ),
    
    
    # ============================================
    # COMMENTS
    # ============================================
    
    # List and create comments on post
    path(
        '<uuid:post_id>/comments/',
        CommentListCreateView.as_view(),
        name='post-comments'
    ),
    
    # Get/Update/Delete specific comment
    path(
        'comments/<uuid:pk>/',
        CommentDetailView.as_view(),
        name='comment-detail'
    ),
    
    # Toggle like on comment
    path(
        'comments/<uuid:comment_id>/like/',
        CommentLikeToggleView.as_view(),
        name='comment-like-toggle'
    ),
]