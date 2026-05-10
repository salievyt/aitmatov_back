from django.urls import path
from .views import CourseListView, CourseDetailView, LessonListView

urlpatterns = [
    path('', CourseListView.as_view(), name='course-list'),
    path('<int:pk>/', CourseDetailView.as_view(), name='course-detail'),
    path('<int:course_id>/lessons/', LessonListView.as_view(), name='lesson-list'),
]
