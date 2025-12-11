from django.shortcuts import render

from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Follow
from .serializers import (
    FollowActionSerializer,
    UserBasicSerializer,
    FollowersListSerializer,
    FollowingListSerializer,
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
