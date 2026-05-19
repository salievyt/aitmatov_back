from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import DailySchedule
from .serializers import DailyScheduleSerializer


class DailyScheduleListCreateView(generics.ListCreateAPIView):
    queryset = DailySchedule.objects.filter(is_active=True)
    serializer_class = DailyScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['day', 'subject', 'teacher']
    ordering_fields = ['day', 'start_time']
    search_fields = ['title', 'description']


class DailyScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = DailySchedule.objects.filter(is_active=True)
    serializer_class = DailyScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
