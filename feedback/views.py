from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from users.views import IsAdmin
from .models import FeedbackSubmission, Survey, SurveyResponse
from .serializers import (
    FeedbackSubmissionSerializer,
    FeedbackSubmissionAdminSerializer,
    SurveySerializer,
    SurveyCreateSerializer,
    SurveySubmitSerializer,
    SurveyResponseSerializer,
)


class FeedbackSubmissionListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if IsAdmin().has_permission(self.request, self):
            return FeedbackSubmission.objects.select_related('user').all()
        return FeedbackSubmission.objects.select_related('user').filter(user=self.request.user)

    def get_serializer_class(self):
        if IsAdmin().has_permission(self.request, self):
            return FeedbackSubmissionAdminSerializer
        return FeedbackSubmissionSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FeedbackSubmissionDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = FeedbackSubmission.objects.select_related('user').all()

    def get_serializer_class(self):
        if IsAdmin().has_permission(self.request, self):
            return FeedbackSubmissionAdminSerializer
        return FeedbackSubmissionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if IsAdmin().has_permission(self.request, self):
            return queryset
        return queryset.filter(user=self.request.user)


class SurveyListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Survey.objects.prefetch_related('questions__options').all()
        if IsAdmin().has_permission(self.request, self):
            return queryset
        return queryset.filter(status=Survey.Status.PUBLISHED)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SurveyCreateSerializer
        return SurveySerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class SurveyDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Survey.objects.prefetch_related('questions__options').all()
        if IsAdmin().has_permission(self.request, self):
            return queryset
        return queryset.filter(status=Survey.Status.PUBLISHED)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return SurveyCreateSerializer
        return SurveySerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:
            return [IsAdmin()]
        return super().get_permissions()


class SurveySubmitView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, survey_id):
        survey = generics.get_object_or_404(Survey.objects.prefetch_related('questions__options'), pk=survey_id)
        serializer = SurveySubmitSerializer(data=request.data, context={'request': request, 'survey': survey})
        serializer.is_valid(raise_exception=True)
        response = serializer.save()
        return Response(SurveyResponseSerializer(response).data, status=201)


class SurveyResponseListView(generics.ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = SurveyResponseSerializer

    def get_queryset(self):
        survey_id = self.kwargs['survey_id']
        return SurveyResponse.objects.filter(survey_id=survey_id).select_related('survey', 'user').prefetch_related('answers__question')
