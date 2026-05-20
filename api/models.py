from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


def _get_request_meta(request, key, default=''):
    if not request:
        return default
    return request.META.get(key, default)


class AuditLog(models.Model):
    class Action(models.TextChoices):
        LOGIN = 'login', _('Вход в аккаунт')
        SIGNUP = 'signup', _('Регистрация аккаунта')
        COURSE_PUBLISHED = 'course_published', _('Публикация курса')
        LESSON_PUBLISHED = 'lesson_published', _('Публикация урока')
        OTHER = 'other', _('Прочее действие')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name=_('пользователь'),
    )
    action = models.CharField(_('действие'), max_length=50, choices=Action.choices)
    target_type = models.CharField(_('тип объекта'), max_length=50, blank=True, null=True)
    target_id = models.PositiveBigIntegerField(_('ID объекта'), blank=True, null=True)
    target_name = models.CharField(_('название объекта'), max_length=255, blank=True)
    details = models.JSONField(_('детали'), blank=True, null=True)
    ip_address = models.CharField(_('IP адрес'), max_length=45, blank=True)
    user_agent = models.CharField(_('User-Agent'), max_length=512, blank=True)
    created_at = models.DateTimeField(_('создано'), auto_now_add=True)

    class Meta:
        verbose_name = _('Журнал действий')
        verbose_name_plural = _('Журналы действий')
        ordering = ['-created_at']

    def __str__(self):
        user_label = str(self.user) if self.user else _('Система')
        return f"{self.get_action_display()} — {user_label}"


def create_audit_log(
    action,
    user=None,
    target_type=None,
    target_id=None,
    target_name=None,
    details=None,
    request=None,
):
    return AuditLog.objects.create(
        user=user,
        action=action,
        target_type=target_type,
        target_id=target_id,
        target_name=target_name or '',
        details=details or {},
        ip_address=_get_request_meta(request, 'REMOTE_ADDR', ''),
        user_agent=_get_request_meta(request, 'HTTP_USER_AGENT', ''),
    )
