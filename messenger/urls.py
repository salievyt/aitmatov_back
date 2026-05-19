from django.urls import path

from .views import (
    ChatGroupDetailView,
    ChatGroupListCreateView,
    GroupLeaderAssignView,
    GroupMembershipListCreateView,
    MessageListCreateView,
)

urlpatterns = [
    path('groups/', ChatGroupListCreateView.as_view(), name='messenger-group-list'),
    path('groups/<int:pk>/', ChatGroupDetailView.as_view(), name='messenger-group-detail'),
    path('groups/<int:group_id>/members/', GroupMembershipListCreateView.as_view(), name='messenger-group-members'),
    path('groups/<int:group_id>/assign-leader/', GroupLeaderAssignView.as_view(), name='messenger-assign-leader'),
    path('groups/<int:group_id>/messages/', MessageListCreateView.as_view(), name='messenger-group-messages'),
]
