from django.utils.translation import gettext_lazy as _
from rest_framework import generics, permissions
from .models import ProgressItem, QuarterGrade
from .serializers import (
    ProgressItemSerializer,
    ProgressItemCreateSerializer,
    QuarterGradeSerializer,
    QuarterGradeCreateSerializer,
)


class ProgressListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProgressItemCreateSerializer
        return ProgressItemSerializer

    def get_queryset(self):
        return ProgressItem.objects.filter(user=self.request.user).select_related('lesson', 'lesson__course')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class QuarterGradeListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return QuarterGradeCreateSerializer
        return QuarterGradeSerializer

    def get_queryset(self):
        if self.request.user.role == 'teacher':
            return QuarterGrade.objects.filter(course__teacher=self.request.user).select_related('user', 'course')
        return QuarterGrade.objects.filter(user=self.request.user).select_related('user', 'course')

    def perform_create(self, serializer):
        if self.request.user.role != 'teacher':
            raise permissions.PermissionDenied(_('Только учитель может выставлять четвертные оценки'))
        serializer.save()
