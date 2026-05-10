from rest_framework import serializers
from .models import Course, Lesson
from subjects.serializers import SubjectSerializer
from aitmatov.serializers import AitmatovThemeSerializer


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'order', 'content_type',
            'video_url', 'text_body', 'quiz_enabled',
            'is_active', 'created_at',
        ]


class CourseListSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)
    lessons_count = serializers.IntegerField(source='lessons.count', read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'subject',
            'is_aitmatov', 'class_level', 'image',
            'lessons_count', 'created_at',
        ]


class CourseDetailSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)
    aitmatov_theme = AitmatovThemeSerializer(read_only=True)
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'subject',
            'teacher', 'is_aitmatov', 'aitmatov_theme',
            'class_level', 'image', 'lessons',
            'is_active', 'created_at', 'updated_at',
        ]
