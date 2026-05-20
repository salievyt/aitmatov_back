from django.db import connections
from django.db.utils import OperationalError
from rest_framework import generics, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from .models import AuditLog
from .serializers import AuditLogSerializer
from users.views import IsAdmin


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({'status': 'ok'})


class ReadinessCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        db_ok = True
        try:
            connections['default'].cursor()
        except OperationalError:
            db_ok = False

        status_code = 200 if db_ok else 503
        return Response({'status': 'ready' if db_ok else 'not_ready', 'database': db_ok}, status=status_code)


class AuditLogListView(generics.ListAPIView):
    queryset = AuditLog.objects.select_related('user').all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action', 'target_type', 'user__id']
    search_fields = ['target_name', 'user__email', 'user__phone', 'user__username']
    ordering_fields = ['created_at', 'action', 'user__email']
    ordering = ['-created_at']
