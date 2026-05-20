from django.urls import path
from .views import ProgressListCreateView, QuarterGradeListCreateView

urlpatterns = [
    path('', ProgressListCreateView.as_view(), name='progress-list-create'),
    path('grades/', QuarterGradeListCreateView.as_view(), name='quarter-grade-list-create'),
]
