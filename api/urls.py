from django.urls import path

from .views import (
    AuditLogListView,
    HealthCheckView,
    PlatformAnalyticsEngagementView,
    PlatformAnalyticsOverviewView,
    PlatformAnalyticsUsersView,
    ReadinessCheckView,
)

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('ready/', ReadinessCheckView.as_view(), name='readiness-check'),
    path('logs/', AuditLogListView.as_view(), name='auditlog-list'),
    path('analytics/overview/', PlatformAnalyticsOverviewView.as_view(), name='platform-analytics-overview'),
    path('analytics/users/', PlatformAnalyticsUsersView.as_view(), name='platform-analytics-users'),
    path('analytics/engagement/', PlatformAnalyticsEngagementView.as_view(), name='platform-analytics-engagement'),
]
