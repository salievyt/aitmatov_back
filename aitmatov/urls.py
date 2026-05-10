from django.urls import path
from .views import AitmatovThemeListView

urlpatterns = [
    path('themes/', AitmatovThemeListView.as_view(), name='aitmatov-theme-list'),
]
