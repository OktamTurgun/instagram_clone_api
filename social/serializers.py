from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Follow

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """
    Basic user info for follow lists
    """
    avatar = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    follows_you = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_following',
            'follows_you',
        )
    
    def get_avatar(self, obj):
        """Get avatar URL"""
        if hasattr(obj, 'profile') and obj.profile.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile.avatar.url)
        return None
    
    def get_is_following(self, obj):
        """Check if current user follows this user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.is_following(request.user, obj)
        return False
    
    def get_follows_you(self, obj):
        """Check if this user follows current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.is_following(obj, request.user)
        return False


class FollowSerializer(serializers.ModelSerializer):
    """
    Follow relationship serializer
    """
    follower = UserBasicSerializer(read_only=True)
    following = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = Follow
        fields = ('id', 'follower', 'following', 'created_at')
        read_only_fields = ('id', 'created_at')


class FollowActionSerializer(serializers.Serializer):
    """
    Serializer for follow/unfollow actions
    """
    user_id = serializers.UUIDField()
    
    def validate_user_id(self, value):
        """Validate user exists"""
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        
        # Check not self
        request = self.context.get('request')
        if request and request.user.id == value:
            raise serializers.ValidationError("Cannot follow yourself")
        
        return value
    
    def to_representation(self, instance):
        """Return user info after follow/unfollow"""
        if isinstance(instance, Follow):
            # Follow action - return following user
            user = instance.following
        else:
            # Unfollow action - instance is the user
            user = instance
        
        request = self.context.get('request')
        serializer = UserBasicSerializer(user, context={'request': request})
        
        return {
            "success": True,
            "message": f"Successfully {'followed' if isinstance(instance, Follow) else 'unfollowed'} @{user.username}",
            "data": {
                "user": serializer.data,
                "followers_count": user.profile.followers_count if hasattr(user, 'profile') else 0,
                "following_count": user.profile.following_count if hasattr(user, 'profile') else 0,
            }
        }


class FollowersListSerializer(serializers.Serializer):
    """
    Paginated followers list response
    """
    def to_representation(self, instance):
        """Format followers list response"""
        request = self.context.get('request')
        
        # instance is paginated queryset
        followers = UserBasicSerializer(
            instance,
            many=True,
            context={'request': request}
        ).data
        
        return {
            "success": True,
            "data": {
                "followers": followers,
                "count": len(followers)
            }
        }


class FollowingListSerializer(serializers.Serializer):
    """
    Paginated following list response
    """
    def to_representation(self, instance):
        """Format following list response"""
        request = self.context.get('request')
        
        following = UserBasicSerializer(
            instance,
            many=True,
            context={'request': request}
        ).data
        
        return {
            "success": True,
            "data": {
                "following": following,
                "count": len(following)
            }
        }