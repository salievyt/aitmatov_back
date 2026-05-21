from django.db import connections
from django.db.utils import OperationalError
from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import generics, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from datetime import timedelta

from .models import AuditLog
from .serializers import (
    AuditLogSerializer,
    PlatformAnalyticsOverviewSerializer,
    PlatformAnalyticsUsersSerializer,
    PlatformAnalyticsEngagementSerializer,
)
from users.views import IsAdmin
from courses.models import Course, Lesson
from subjects.models import Subject
from schedule.models import DailySchedule
from aitmatov.models import AitmatovTheme
from progress.models import ProgressItem, QuarterGrade
from messenger.models import ChatGroup, GroupMembership, Message, Channel, ChannelMessage

User = get_user_model()


def _get_positive_int_query_param(request, key, default):
    try:
        return max(int(request.query_params.get(key, default)), 1)
    except (TypeError, ValueError):
        return default


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({'status': 'ok'})


class ReadinessCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        db_ok = True
        try:
            connections['default'].cursor()
        except OperationalError:
            db_ok = False

        status_code = 200 if db_ok else 503
        return Response({'status': 'ready' if db_ok else 'not_ready', 'database': db_ok}, status=status_code)


class AuditLogListView(generics.ListAPIView):
    queryset = AuditLog.objects.select_related('user').all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action', 'target_type', 'user__id']
    search_fields = ['target_name', 'user__email', 'user__phone', 'user__username']
    ordering_fields = ['created_at', 'action', 'user__email']
    ordering = ['-created_at']


class PlatformAnalyticsOverviewView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        now = timezone.now()
        online_window_minutes = _get_positive_int_query_param(request, 'online_window_minutes', 15)
        recent_window_hours = _get_positive_int_query_param(request, 'recent_window_hours', 24)
        online_since = now - timedelta(minutes=online_window_minutes)
        recent_since = now - timedelta(hours=recent_window_hours)
        week_since = now - timedelta(days=7)
        month_since = now - timedelta(days=30)

        users = User.objects.all()
        active_users = users.filter(is_active=True)
        progress_items = ProgressItem.objects.all()
        recent_login_logs = AuditLog.objects.filter(action=AuditLog.Action.LOGIN, created_at__gte=recent_since)

        progress_stats = progress_items.aggregate(
            total=Count('id'),
            completed=Count('id', filter=Q(completed=True)),
            avg_score=Avg('score'),
            avg_grade=Avg('grade'),
            active_learners=Count('user', distinct=True),
        )
        total_progress = progress_stats['total'] or 0
        completed_progress = progress_stats['completed'] or 0

        payload = {
            'generated_at': now,
            'windows': {
                'online_minutes': online_window_minutes,
                'recent_hours': recent_window_hours,
            },
            'users': {
                'total': users.count(),
                'active': active_users.count(),
                'inactive': users.filter(is_active=False).count(),
                'students': users.filter(role=User.Role.STUDENT).count(),
                'teachers': users.filter(role=User.Role.TEACHER).count(),
                'admins': users.filter(role=User.Role.ADMIN).count(),
                'online_now': users.filter(is_active=True, last_login__gte=online_since).count(),
                'active_last_24h': users.filter(is_active=True, last_login__gte=now - timedelta(hours=24)).count(),
                'active_last_7d': users.filter(is_active=True, last_login__gte=week_since).count(),
                'new_last_7d': users.filter(date_joined__gte=week_since).count(),
                'new_last_30d': users.filter(date_joined__gte=month_since).count(),
            },
            'content': {
                'subjects_total': Subject.objects.count(),
                'subjects_active': Subject.objects.filter(is_active=True).count(),
                'courses_total': Course.objects.count(),
                'courses_active': Course.objects.filter(is_active=True).count(),
                'aitmatov_courses': Course.objects.filter(is_aitmatov=True).count(),
                'lessons_total': Lesson.objects.count(),
                'lessons_active': Lesson.objects.filter(is_active=True).count(),
                'themes_total': AitmatovTheme.objects.count(),
                'themes_active': AitmatovTheme.objects.filter(is_active=True).count(),
                'schedule_items_total': DailySchedule.objects.count(),
                'schedule_items_active': DailySchedule.objects.filter(is_active=True).count(),
            },
            'learning': {
                'progress_items_total': total_progress,
                'progress_completed_total': completed_progress,
                'progress_completion_rate': round((completed_progress / total_progress) * 100, 2) if total_progress else 0,
                'active_learners_total': progress_stats['active_learners'] or 0,
                'average_score': round(progress_stats['avg_score'], 2) if progress_stats['avg_score'] is not None else None,
                'average_grade': round(progress_stats['avg_grade'], 2) if progress_stats['avg_grade'] is not None else None,
                'quarter_grades_total': QuarterGrade.objects.count(),
                'quarter_grades_average': round(QuarterGrade.objects.aggregate(avg=Avg('grade'))['avg'], 2) if QuarterGrade.objects.exists() else None,
            },
            'communication': {
                'chat_groups_total': ChatGroup.objects.count(),
                'channels_total': Channel.objects.count(),
                'group_memberships_total': GroupMembership.objects.count(),
                'messages_total': Message.objects.count(),
                'channel_messages_total': ChannelMessage.objects.count(),
                'messages_last_window': Message.objects.filter(created_at__gte=recent_since).count(),
                'channel_messages_last_window': ChannelMessage.objects.filter(created_at__gte=recent_since).count(),
            },
            'logins': {
                'last_window_total': recent_login_logs.count(),
                'last_window_unique_users': recent_login_logs.values('user_id').exclude(user_id__isnull=True).distinct().count(),
                'today_total': AuditLog.objects.filter(action=AuditLog.Action.LOGIN, created_at__date=now.date()).count(),
                'last_7d_total': AuditLog.objects.filter(action=AuditLog.Action.LOGIN, created_at__gte=week_since).count(),
            },
        }

        serializer = PlatformAnalyticsOverviewSerializer(payload)
        return Response(serializer.data)


class PlatformAnalyticsUsersView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        now = timezone.now()
        users = User.objects.all()
        online_window_minutes = _get_positive_int_query_param(request, 'online_window_minutes', 15)
        online_since = now - timedelta(minutes=online_window_minutes)

        role_distribution = list(
            users.values('role').annotate(count=Count('id')).order_by('role')
        )
        class_distribution = list(
            users.exclude(class_level__isnull=True).values('class_level').annotate(count=Count('id')).order_by('class_level')
        )
        school_distribution = list(
            users.exclude(school__isnull=True).exclude(school='').values('school').annotate(count=Count('id')).order_by('-count', 'school')[:10]
        )
        registrations = list(
            users.annotate(day=TruncDate('date_joined')).values('day').annotate(count=Count('id')).order_by('-day')[:14]
        )

        payload = {
            'generated_at': now,
            'activity': {
                'online_now': users.filter(is_active=True, last_login__gte=online_since).count(),
                'last_24h': users.filter(is_active=True, last_login__gte=now - timedelta(hours=24)).count(),
                'last_7d': users.filter(is_active=True, last_login__gte=now - timedelta(days=7)).count(),
                'last_30d': users.filter(is_active=True, last_login__gte=now - timedelta(days=30)).count(),
            },
            'role_distribution': role_distribution,
            'class_distribution': class_distribution,
            'school_distribution': school_distribution,
            'registrations': registrations,
        }

        serializer = PlatformAnalyticsUsersSerializer(payload)
        return Response(serializer.data)


class PlatformAnalyticsEngagementView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        now = timezone.now()
        last_7d = now - timedelta(days=7)
        progress_items = ProgressItem.objects.select_related('lesson__course__subject')
        quarter_grades = QuarterGrade.objects.select_related('course__subject')

        progress_stats = progress_items.aggregate(
            total=Count('id'),
            completed=Count('id', filter=Q(completed=True)),
            avg_score=Avg('score'),
            avg_grade=Avg('grade'),
            unique_students=Count('user', distinct=True),
        )

        top_courses = list(
            progress_items.values('lesson__course_id', 'lesson__course__title')
            .annotate(
                learners=Count('user', distinct=True),
                total_progress_items=Count('id'),
                completed_lessons=Count('id', filter=Q(completed=True)),
                average_score=Avg('score'),
                average_grade=Avg('grade'),
            )
            .order_by('-learners', '-completed_lessons', 'lesson__course__title')[:10]
        )

        top_subjects = list(
            progress_items.values('lesson__course__subject_id', 'lesson__course__subject__name')
            .annotate(
                learners=Count('user', distinct=True),
                total_progress_items=Count('id'),
                completed_lessons=Count('id', filter=Q(completed=True)),
                average_score=Avg('score'),
                average_grade=Avg('grade'),
            )
            .order_by('-learners', '-completed_lessons', 'lesson__course__subject__name')[:10]
        )

        quarter_distribution = quarter_grades.aggregate(
            grade_5=Count('id', filter=Q(grade=5)),
            grade_4=Count('id', filter=Q(grade=4)),
            grade_3=Count('id', filter=Q(grade=3)),
            grade_1_2=Count('id', filter=Q(grade__lte=2)),
            average=Avg('grade'),
        )

        payload = {
            'generated_at': now,
            'progress': {
                'items_total': progress_stats['total'] or 0,
                'completed_total': progress_stats['completed'] or 0,
                'completion_rate': round(((progress_stats['completed'] or 0) / (progress_stats['total'] or 1)) * 100, 2) if progress_stats['total'] else 0,
                'unique_students': progress_stats['unique_students'] or 0,
                'average_score': round(progress_stats['avg_score'], 2) if progress_stats['avg_score'] is not None else None,
                'average_grade': round(progress_stats['avg_grade'], 2) if progress_stats['avg_grade'] is not None else None,
            },
            'quarter_grades': {
                'total': quarter_grades.count(),
                'average': round(quarter_distribution['average'], 2) if quarter_distribution['average'] is not None else None,
                'distribution': {
                    '5': quarter_distribution['grade_5'] or 0,
                    '4': quarter_distribution['grade_4'] or 0,
                    '3': quarter_distribution['grade_3'] or 0,
                    '1_2': quarter_distribution['grade_1_2'] or 0,
                },
            },
            'top_courses': top_courses,
            'top_subjects': top_subjects,
            'messenger': {
                'group_messages_last_7d': Message.objects.filter(created_at__gte=last_7d).count(),
                'channel_messages_last_7d': ChannelMessage.objects.filter(created_at__gte=last_7d).count(),
                'active_group_authors_last_7d': Message.objects.filter(created_at__gte=last_7d).values('author_id').exclude(author_id__isnull=True).distinct().count(),
                'active_channel_authors_last_7d': ChannelMessage.objects.filter(created_at__gte=last_7d).values('author_id').exclude(author_id__isnull=True).distinct().count(),
            },
        }

        serializer = PlatformAnalyticsEngagementSerializer(payload)
        return Response(serializer.data)
