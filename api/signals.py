from django.apps import apps
from django.contrib.auth.signals import user_logged_in
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import AuditLog, create_audit_log


User = apps.get_model(settings.AUTH_USER_MODEL)
Course = apps.get_model('courses', 'Course')
Lesson = apps.get_model('courses', 'Lesson')


@receiver(post_save, sender=User)
def log_user_created(sender, instance, created, **kwargs):
    if created:
        create_audit_log(
            AuditLog.Action.SIGNUP,
            user=instance,
            target_type='user',
            target_id=instance.pk,
            target_name=str(instance),
            details={'event': 'user.created'},
        )


@receiver(user_logged_in)
def log_user_logged_in(sender, request, user, **kwargs):
    create_audit_log(
        AuditLog.Action.LOGIN,
        user=user,
        target_type='user',
        target_id=user.pk,
        target_name=str(user),
        request=request,
        details={'event': 'user.logged_in'},
    )


@receiver(post_save, sender=Course)
def log_course_created(sender, instance, created, **kwargs):
    if created:
        create_audit_log(
            AuditLog.Action.COURSE_PUBLISHED,
            user=instance.teacher,
            target_type='course',
            target_id=instance.pk,
            target_name=instance.title,
            details={'course_id': instance.pk, 'course_title': instance.title},
        )


@receiver(post_save, sender=Lesson)
def log_lesson_created(sender, instance, created, **kwargs):
    if created:
        course_title = instance.course.title if instance.course_id else ''
        create_audit_log(
            AuditLog.Action.LESSON_PUBLISHED,
            user=instance.course.teacher,
            target_type='lesson',
            target_id=instance.pk,
            target_name=instance.title,
            details={
                'lesson_id': instance.pk,
                'course_id': instance.course_id,
                'course_title': course_title,
            },
        )
