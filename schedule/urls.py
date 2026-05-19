from django.urls import path
from .views import DailyScheduleListCreateView, DailyScheduleDetailView

urlpatterns = [
    path('', DailyScheduleListCreateView.as_view(), name='daily-schedule-list-create'),
    path('<int:pk>/', DailyScheduleDetailView.as_view(), name='daily-schedule-detail'),
]
