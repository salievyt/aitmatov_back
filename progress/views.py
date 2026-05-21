from django.utils.translation import gettext_lazy as _
from django.db.models import Avg, Count, Q
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import ProgressItem, QuarterGrade
from .serializers import (
    ProgressItemSerializer,
    ProgressItemCreateSerializer,
    QuarterGradeSerializer,
    QuarterGradeCreateSerializer,
    ProgressSummarySerializer,
)


class ProgressListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProgressItemCreateSerializer
        return ProgressItemSerializer

    def get_queryset(self):
        return ProgressItem.objects.filter(user=self.request.user).select_related('lesson', 'lesson__course')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class QuarterGradeListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return QuarterGradeCreateSerializer
        return QuarterGradeSerializer

    def get_queryset(self):
        if self.request.user.role == 'teacher':
            return QuarterGrade.objects.filter(course__teacher=self.request.user).select_related('user', 'course')
        return QuarterGrade.objects.filter(user=self.request.user).select_related('user', 'course')

    def perform_create(self, serializer):
        if self.request.user.role != 'teacher':
            raise permissions.PermissionDenied(_('Только учитель может выставлять четвертные оценки'))
        serializer.save()


class ProgressSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        progress_queryset = ProgressItem.objects.filter(user=user).select_related(
            'lesson__course__subject'
        )
        grade_queryset = QuarterGrade.objects.filter(user=user).select_related(
            'course__subject', 'course__teacher'
        )

        progress_stats = progress_queryset.aggregate(
            total_lessons=Count('id'),
            completed_lessons=Count('id', filter=Q(completed=True)),
            in_progress_lessons=Count(
                'id',
                filter=Q(completed=False) & (Q(score__isnull=False) | Q(grade__isnull=False) | ~Q(notes='')),
            ),
            average_score=Avg('score'),
            average_grade=Avg('grade'),
        )

        total_lessons = progress_stats['total_lessons'] or 0
        completed_lessons = progress_stats['completed_lessons'] or 0
        progress_percent = round((completed_lessons / total_lessons) * 100, 2) if total_lessons else 0

        by_course = []
        course_rows = (
            progress_queryset.values(
                'lesson__course_id',
                'lesson__course__title',
                'lesson__course__subject__name',
            )
            .annotate(
                total_lessons=Count('id'),
                completed_lessons=Count('id', filter=Q(completed=True)),
                average_score=Avg('score'),
                average_grade=Avg('grade'),
            )
            .order_by('lesson__course__title')
        )
        for row in course_rows:
            course_total = row['total_lessons'] or 0
            course_completed = row['completed_lessons'] or 0
            by_course.append({
                'course_id': row['lesson__course_id'],
                'course_title': row['lesson__course__title'],
                'subject_name': row['lesson__course__subject__name'],
                'total_lessons': course_total,
                'completed_lessons': course_completed,
                'remaining_lessons': max(course_total - course_completed, 0),
                'completion_percent': round((course_completed / course_total) * 100, 2) if course_total else 0,
                'average_score': round(row['average_score'], 2) if row['average_score'] is not None else None,
                'average_grade': round(row['average_grade'], 2) if row['average_grade'] is not None else None,
            })

        quarter_stats = grade_queryset.aggregate(
            total_quarter_grades=Count('id'),
            average_quarter_grade=Avg('grade'),
            excellent_count=Count('id', filter=Q(grade=5)),
            good_count=Count('id', filter=Q(grade=4)),
            satisfactory_count=Count('id', filter=Q(grade=3)),
            unsatisfactory_count=Count('id', filter=Q(grade__lte=2)),
        )

        payload = {
            'overall': {
                'total_lessons': total_lessons,
                'completed_lessons': completed_lessons,
                'remaining_lessons': max(total_lessons - completed_lessons, 0),
                'in_progress_lessons': progress_stats['in_progress_lessons'] or 0,
                'completion_percent': progress_percent,
                'average_score': round(progress_stats['average_score'], 2) if progress_stats['average_score'] is not None else None,
                'average_grade': round(progress_stats['average_grade'], 2) if progress_stats['average_grade'] is not None else None,
            },
            'by_course': by_course,
            'quarter_grades': {
                'total': quarter_stats['total_quarter_grades'] or 0,
                'average_grade': round(quarter_stats['average_quarter_grade'], 2) if quarter_stats['average_quarter_grade'] is not None else None,
                'distribution': {
                    '5': quarter_stats['excellent_count'] or 0,
                    '4': quarter_stats['good_count'] or 0,
                    '3': quarter_stats['satisfactory_count'] or 0,
                    '1_2': quarter_stats['unsatisfactory_count'] or 0,
                },
                'items': QuarterGradeSerializer(grade_queryset, many=True).data,
            },
        }

        serializer = ProgressSummarySerializer(payload)
        return Response(serializer.data)
