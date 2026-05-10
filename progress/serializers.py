from rest_framework import serializers
from .models import ProgressItem
from courses.serializers import LessonSerializer
from users.serializers import UserSerializer


class ProgressItemSerializer(serializers.ModelSerializer):
    lesson = LessonSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = ProgressItem
        fields = [
            'id', 'user', 'lesson', 'completed',
            'score', 'notes', 'updated_at', 'created_at',
        ]


class ProgressItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressItem
        fields = ['lesson', 'completed', 'score', 'notes']

    def create(self, validated_data):
        user = self.context['request'].user
        lesson = validated_data.get('lesson')
        progress, created = ProgressItem.objects.update_or_create(
            user=user,
            lesson=lesson,
            defaults={
                'completed': validated_data.get('completed', False),
                'score': validated_data.get('score'),
                'notes': validated_data.get('notes', ''),
            }
        )
        return progress
