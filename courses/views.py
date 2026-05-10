from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Course, Lesson
from .serializers import CourseListSerializer, CourseDetailSerializer, LessonSerializer


class CourseListView(generics.ListAPIView):
    queryset = Course.objects.filter(is_active=True).prefetch_related('subject', 'lessons')
    serializer_class = CourseListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['subject', 'is_aitmatov', 'aitmatov_theme', 'class_level']
    search_fields = ['title', 'description']


class CourseDetailView(generics.RetrieveAPIView):
    queryset = Course.objects.filter(is_active=True).prefetch_related('lessons', 'subject')
    serializer_class = CourseDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'


class LessonListView(generics.ListAPIView):
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        course_id = self.kwargs.get('course_id')
        return Lesson.objects.filter(course_id=course_id, is_active=True).order_by('order')
