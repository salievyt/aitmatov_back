from django.urls import path
from .views import MeView, UserListView, UserDetailView, UserProfileDetailView

urlpatterns = [
    path('me/', MeView.as_view(), name='me'),
    path('profile/<int:id>/', UserProfileDetailView.as_view(), name='user-profile'),
    # Admin endpoints
    path('', UserListView.as_view(), name='user-list'),
    path('<int:id>/', UserDetailView.as_view(), name='user-detail'),
]
