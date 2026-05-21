from django.urls import path

from .views import (
    ChatGroupDetailView,
    ChatGroupListCreateView,
    GroupLeaderAssignView,
    GroupMembershipListCreateView,
    MessageListView,
    ChannelListCreateView,
    ChannelDetailView,
    ChannelMessageListView,
)

urlpatterns = [
    # Chat Groups
    path('groups/', ChatGroupListCreateView.as_view(), name='messenger-group-list'),
    path('groups/<int:pk>/', ChatGroupDetailView.as_view(), name='messenger-group-detail'),
    path('groups/<int:group_id>/members/', GroupMembershipListCreateView.as_view(), name='messenger-group-members'),
    path('groups/<int:group_id>/assign-leader/', GroupLeaderAssignView.as_view(), name='messenger-assign-leader'),
    path('groups/<int:group_id>/messages/', MessageListView.as_view(), name='messenger-group-messages'),
    
    # Channels
    path('channels/', ChannelListCreateView.as_view(), name='messenger-channel-list'),
    path('channels/<int:pk>/', ChannelDetailView.as_view(), name='messenger-channel-detail'),
    path('channels/<int:channel_id>/messages/', ChannelMessageListView.as_view(), name='messenger-channel-messages'),
]
