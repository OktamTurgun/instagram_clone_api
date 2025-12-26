from django.shortcuts import render

from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from rest_framework.pagination import PageNumberPagination

from .models import Follow
from .serializers import (
    FollowActionSerializer,
    SearchResultsSerializer,
    SuggestedUsersSerializer,
    UserBasicSerializer,
    FollowersListSerializer,
    FollowingListSerializer,
    UserSearchSerializer,
)

User = get_user_model()


class FollowView(APIView):
    """
    Follow a user
    
    POST /api/social/users/{user_id}/follow/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, user_id):
        # Validate user
        serializer = FollowActionSerializer(
            data={'user_id': user_id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # Get users
        follower = request.user
        following = get_object_or_404(User, id=user_id)
        
        # Check if already following
        if Follow.is_following(follower, following):
            return Response(
                {
                    "success": False,
                    "message": f"Already following @{following.username}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create follow
        follow = Follow.objects.create(
            follower=follower,
            following=following
        )
        
        # Return response
        response_serializer = FollowActionSerializer(
            follow,
            context={'request': request}
        )
        
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )


class UnfollowView(APIView):
    """
    Unfollow a user
    
    POST /api/social/users/{user_id}/unfollow/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, user_id):
        # Validate user
        serializer = FollowActionSerializer(
            data={'user_id': user_id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # Get users
        follower = request.user
        following = get_object_or_404(User, id=user_id)
        
        # Check if following
        try:
            follow = Follow.objects.get(
                follower=follower,
                following=following
            )
        except Follow.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": f"Not following @{following.username}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Delete follow
        follow.delete()
        
        # Return response
        response_serializer = FollowActionSerializer(
            following,
            context={'request': request}
        )
        
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK
        )


class FollowersListView(generics.ListAPIView):
    """
    Get user's followers
    
    GET /api/social/users/{user_id}/followers/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserBasicSerializer
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        user = get_object_or_404(User, id=user_id)
        
        # Get followers (users who follow this user)
        follower_ids = Follow.objects.filter(
            following=user
        ).values_list('follower_id', flat=True)
        
        return User.objects.filter(id__in=follower_ids)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = FollowersListSerializer(
            queryset,
            context={'request': request}
        )
        return Response(serializer.data)


class FollowingListView(generics.ListAPIView):
    """
    Get users that this user follows
    
    GET /api/social/users/{user_id}/following/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserBasicSerializer
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        user = get_object_or_404(User, id=user_id)
        
        # Get following (users this user follows)
        following_ids = Follow.objects.filter(
            follower=user
        ).values_list('following_id', flat=True)
        
        return User.objects.filter(id__in=following_ids)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = FollowingListSerializer(
            queryset,
            context={'request': request}
        )
        return Response(serializer.data)


class UserStatsView(APIView):
    """
    Get user's follow stats
    
    GET /api/social/users/{user_id}/stats/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        
        followers_count = Follow.objects.filter(following=user).count()
        following_count = Follow.objects.filter(follower=user).count()
        
        # Check relationship with current user
        is_following = False
        follows_you = False
        
        if request.user.is_authenticated and request.user != user:
            is_following = Follow.is_following(request.user, user)
            follows_you = Follow.is_following(user, request.user)
        
        return Response({
            "success": True,
            "data": {
                "user_id": str(user.id),
                "username": user.username,
                "followers_count": followers_count,
                "following_count": following_count,
                "is_following": is_following,
                "follows_you": follows_you,
            }
        })

# Existing imports...


# ... existing views ...


class UserSearchPagination(PageNumberPagination):
    """Custom pagination for user search"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserSearchView(generics.ListAPIView):
    """
    Search users by username or name
    
    GET /api/social/users/search/?q=john
    GET /api/social/users/search/?q=john&page=2
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSearchSerializer
    pagination_class = UserSearchPagination
    
    def get_queryset(self):
        query = self.request.query_params.get('q', '').strip()
        
        if not query:
            return User.objects.none()
        
        # Search in username, first_name, last_name
        queryset = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).exclude(
            id=self.request.user.id  # Exclude current user
        ).select_related('profile').distinct()
        
        # Order by relevance (exact matches first)
        queryset = queryset.annotate(
            exact_match=Count('id', filter=Q(username__iexact=query))
        ).order_by('-exact_match', 'username')
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Custom response format"""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = SearchResultsSerializer(
                page,
                context={
                    'request': request,
                    'query': request.query_params.get('q', '')
                }
            )
            return self.get_paginated_response(serializer.data)
        
        serializer = SearchResultsSerializer(
            queryset,
            context={
                'request': request,
                'query': request.query_params.get('q', '')
            }
        )
        return Response(serializer.data)


class SuggestedUsersView(generics.ListAPIView):
    """
    Get suggested users (users not following)
    
    GET /api/social/users/suggested/
    GET /api/social/users/suggested/?limit=10
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSearchSerializer
    
    def get_queryset(self):
        user = self.request.user
        limit = int(self.request.query_params.get('limit', 10))
        
        # Get users current user is already following
        following_ids = Follow.objects.filter(
            follower=user
        ).values_list('following_id', flat=True)
        
        # Get users NOT following, exclude self
        suggested = User.objects.exclude(
            Q(id=user.id) | Q(id__in=following_ids)
        ).select_related('profile')
        
        # Order by followers count (popular users first)
        suggested = suggested.annotate(
            followers=Count('followers_set')
        ).order_by('-followers')[:limit]
        
        return suggested
    
    def list(self, request, *args, **kwargs):
        """Custom response format"""
        queryset = self.get_queryset()
        serializer = SuggestedUsersSerializer(
            queryset,
            context={'request': request}
        )
        return Response(serializer.data)


class PopularUsersView(generics.ListAPIView):
    """
    Get popular users (most followers)
    
    GET /api/social/users/popular/
    GET /api/social/users/popular/?limit=20
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSearchSerializer
    
    def get_queryset(self):
        limit = int(self.request.query_params.get('limit', 20))
        
        # Get users with most followers
        popular = User.objects.exclude(
            id=self.request.user.id
        ).select_related('profile').annotate(
            followers_count_db=Count('followers_set')
        ).order_by('-followers_count_db')[:limit]
        
        return popular
    
    def list(self, request, *args, **kwargs):
        """Custom response format"""
        queryset = self.get_queryset()
        serializer = SuggestedUsersSerializer(
            queryset,
            context={'request': request}
        )
        
        return Response({
            "success": True,
            "data": {
                "popular_users": serializer.data['data']['suggested_users'],
                "count": serializer.data['data']['count']
            }
        })