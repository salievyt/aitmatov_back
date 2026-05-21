from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'action', 'target_type', 'target_id',
            'target_name', 'details', 'ip_address', 'user_agent', 'created_at',
        ]
        read_only_fields = fields


class PlatformAnalyticsOverviewSerializer(serializers.Serializer):
    generated_at = serializers.DateTimeField()
    windows = serializers.DictField()
    users = serializers.DictField()
    content = serializers.DictField()
    learning = serializers.DictField()
    communication = serializers.DictField()
    logins = serializers.DictField()


class PlatformAnalyticsUsersSerializer(serializers.Serializer):
    generated_at = serializers.DateTimeField()
    activity = serializers.DictField()
    role_distribution = serializers.ListField()
    class_distribution = serializers.ListField()
    school_distribution = serializers.ListField()
    registrations = serializers.ListField()


class PlatformAnalyticsEngagementSerializer(serializers.Serializer):
    generated_at = serializers.DateTimeField()
    progress = serializers.DictField()
    quarter_grades = serializers.DictField()
    top_courses = serializers.ListField()
    top_subjects = serializers.ListField()
    messenger = serializers.DictField()
