from rest_framework import serializers
from .models import DailySchedule


class DailyScheduleSerializer(serializers.ModelSerializer):
    day_display = serializers.CharField(source='get_day_display', read_only=True)

    class Meta:
        model = DailySchedule
        fields = [
            'id',
            'day',
            'day_display',
            'title',
            'description',
            'start_time',
            'end_time',
            'subject',
            'teacher',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'day_display']
