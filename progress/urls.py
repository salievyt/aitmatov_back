from django.urls import path
from .views import ProgressListCreateView

urlpatterns = [
    path('', ProgressListCreateView.as_view(), name='progress-list-create'),
]
