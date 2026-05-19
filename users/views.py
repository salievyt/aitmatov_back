from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from .serializers import UserSerializer, UserProfileSerializer, SignupSerializer, UserAdminUpdateSerializer

User = get_user_model()


class IsAdmin(permissions.BasePermission):
    """
    Разрешение для администраторов
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == User.Role.ADMIN


class SignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user, context={'request': request})
        return Response({
            'status': 'success',
            'data': serializer.data,
        })

    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'data': serializer.data,
            })
        return Response({
            'status': 'error',
            'errors': [{'field': k, 'message': v[0]} for k, v in serializer.errors.items()],
        }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return User.objects.filter(is_active=True)


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ['role', 'is_active', 'is_staff']
    search_fields = ['email', 'phone', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'first_name', 'last_name', 'role']
    ordering = ['-date_joined']


class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            # Для обновления используем специальный serializer
            return UserAdminUpdateSerializer
        return UserSerializer
