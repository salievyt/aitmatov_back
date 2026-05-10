from django.urls import path
from .views import SubjectListView

urlpatterns = [
    path('', SubjectListView.as_view(), name='subject-list'),
]
