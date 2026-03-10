from django.urls import path
from .views import (
    FollowView,
    UnfollowView,
    FollowersListView,
    FollowingListView,
    UserStatsView,
    UserSearchView,       
    SuggestedUsersView,   
    PopularUsersView,      
)

app_name = 'social'

urlpatterns = [
    # Follow/Unfollow
    path('users/<uuid:user_id>/follow/', FollowView.as_view(), name='follow'),
    path('users/<uuid:user_id>/unfollow/', UnfollowView.as_view(), name='unfollow'),
    
    # Lists
    path('users/<uuid:user_id>/followers/', FollowersListView.as_view(), name='followers'),
    path('users/<uuid:user_id>/following/', FollowingListView.as_view(), name='following'),
    
    # Stats
    path('users/<uuid:user_id>/stats/', UserStatsView.as_view(), name='user-stats'),
    
    # NEW - Search & Suggestions
    path('users/search/', UserSearchView.as_view(), name='user-search'),
    path('users/suggested/', SuggestedUsersView.as_view(), name='suggested-users'),
    path('users/popular/', PopularUsersView.as_view(), name='popular-users'),
]