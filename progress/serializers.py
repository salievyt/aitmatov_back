from rest_framework import serializers
from .models import ProgressItem, QuarterGrade
from courses.serializers import LessonSerializer, CourseListSerializer
from users.serializers import UserSerializer


class ProgressItemSerializer(serializers.ModelSerializer):
    lesson = LessonSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    grade_label = serializers.CharField(source='get_grade_display', read_only=True)
    course_id = serializers.IntegerField(source='lesson.course_id', read_only=True)
    course_title = serializers.CharField(source='lesson.course.title', read_only=True)
    subject_id = serializers.IntegerField(source='lesson.course.subject_id', read_only=True)
    subject_name = serializers.CharField(source='lesson.course.subject.name', read_only=True)
    completion_status = serializers.SerializerMethodField()

    class Meta:
        model = ProgressItem
        fields = [
            'id', 'user', 'lesson', 'completed',
            'score', 'grade', 'grade_label', 'notes',
            'course_id', 'course_title', 'subject_id', 'subject_name',
            'completion_status', 'updated_at', 'created_at',
        ]

    def get_completion_status(self, obj):
        if obj.completed:
            return 'completed'
        if obj.score is not None or obj.grade is not None or obj.notes:
            return 'in_progress'
        return 'not_started'


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
    grade_label = serializers.CharField(source='get_grade_display', read_only=True)
    quarter_label = serializers.CharField(source='get_quarter_display', read_only=True)
    subject_id = serializers.IntegerField(source='course.subject_id', read_only=True)
    subject_name = serializers.CharField(source='course.subject.name', read_only=True)
    teacher_id = serializers.IntegerField(source='course.teacher_id', read_only=True)
    teacher_name = serializers.SerializerMethodField()

    class Meta:
        model = QuarterGrade
        fields = [
            'id', 'user', 'course', 'quarter',
            'quarter_label', 'grade', 'grade_label', 'notes',
            'subject_id', 'subject_name', 'teacher_id', 'teacher_name',
            'updated_at', 'created_at',
        ]

    def get_teacher_name(self, obj):
        teacher = obj.course.teacher
        if teacher is None:
            return ''
        return teacher.get_full_name() or teacher.email or teacher.phone or ''


class ProgressSummarySerializer(serializers.Serializer):
    overall = serializers.DictField()
    by_course = serializers.ListField()
    quarter_grades = serializers.DictField()


class QuarterGradeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuarterGrade
        fields = ['user', 'course', 'quarter', 'grade', 'notes']
