from django.urls import path

from .views import (
    FeedbackSubmissionDetailView,
    FeedbackSubmissionListCreateView,
    SurveyDetailView,
    SurveyListCreateView,
    SurveyResponseListView,
    SurveySubmitView,
)

urlpatterns = [
    path('submissions/', FeedbackSubmissionListCreateView.as_view(), name='feedback-submission-list-create'),
    path('submissions/<int:pk>/', FeedbackSubmissionDetailView.as_view(), name='feedback-submission-detail'),
    path('surveys/', SurveyListCreateView.as_view(), name='survey-list-create'),
    path('surveys/<int:pk>/', SurveyDetailView.as_view(), name='survey-detail'),
    path('surveys/<int:survey_id>/submit/', SurveySubmitView.as_view(), name='survey-submit'),
    path('surveys/<int:survey_id>/responses/', SurveyResponseListView.as_view(), name='survey-response-list'),
]
