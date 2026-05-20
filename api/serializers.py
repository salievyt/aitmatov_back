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
