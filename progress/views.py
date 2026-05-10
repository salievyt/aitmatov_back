from rest_framework import generics, permissions
from .models import ProgressItem
from .serializers import ProgressItemSerializer, ProgressItemCreateSerializer


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
