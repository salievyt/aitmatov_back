from rest_framework import serializers
from .models import ProgressItem, QuarterGrade
from courses.serializers import LessonSerializer, CourseListSerializer
from users.serializers import UserSerializer


class ProgressItemSerializer(serializers.ModelSerializer):
    lesson = LessonSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = ProgressItem
        fields = [
            'id', 'user', 'lesson', 'completed',
            'score', 'grade', 'notes', 'updated_at', 'created_at',
        ]


class ProgressItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressItem
        fields = ['lesson', 'completed', 'score', 'grade', 'notes']

    def create(self, validated_data, user=None):
        if user is None:
            user = self.context['request'].user
        lesson = validated_data.get('lesson')
        progress, created = ProgressItem.objects.update_or_create(
            user=user,
            lesson=lesson,
            defaults={
                'completed': validated_data.get('completed', False),
                'score': validated_data.get('score'),
                'grade': validated_data.get('grade'),
                'notes': validated_data.get('notes', ''),
            }
        )
        return progress


class QuarterGradeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    course = CourseListSerializer(read_only=True)

    class Meta:
        model = QuarterGrade
        fields = [
            'id', 'user', 'course', 'quarter',
            'grade', 'notes', 'updated_at', 'created_at',
        ]


class QuarterGradeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuarterGrade
        fields = ['user', 'course', 'quarter', 'grade', 'notes']
