from django.urls import path
from .views import (
    FollowView,
    UnfollowView,
    FollowersListView,
    FollowingListView,
    UserStatsView,
)

urlpatterns = [
    # Follow/Unfollow
    path('users/<uuid:user_id>/follow/', FollowView.as_view(), name='follow'),
    path('users/<uuid:user_id>/unfollow/', UnfollowView.as_view(), name='unfollow'),
    
    # Lists
    path('users/<uuid:user_id>/followers/', FollowersListView.as_view(), name='followers'),
    path('users/<uuid:user_id>/following/', FollowingListView.as_view(), name='following'),
    
    # Stats
    path('users/<uuid:user_id>/stats/', UserStatsView.as_view(), name='user-stats'),
]