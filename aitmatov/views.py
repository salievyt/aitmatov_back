from rest_framework import generics, permissions
from .models import AitmatovTheme
from .serializers import AitmatovThemeSerializer


class AitmatovThemeListView(generics.ListAPIView):
    queryset = AitmatovTheme.objects.filter(is_active=True)
    serializer_class = AitmatovThemeSerializer
    permission_classes = [permissions.IsAuthenticated]
