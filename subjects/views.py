from rest_framework import generics, permissions
from .models import Subject
from .serializers import SubjectSerializer


class SubjectListView(generics.ListAPIView):
    queryset = Subject.objects.filter(is_active=True)
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
