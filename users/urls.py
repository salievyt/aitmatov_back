from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LoginView, SignupView

urlpatterns = [
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('signup/', SignupView.as_view(), name='signup'),
]
