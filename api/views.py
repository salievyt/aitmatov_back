from django.db import connections
from django.db.utils import OperationalError
from rest_framework.response import Response
from rest_framework.views import APIView


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
