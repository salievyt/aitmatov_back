from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class ProgressItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='progress_items',
        verbose_name=_('пользователь'),
    )
    lesson = models.ForeignKey(
        'courses.Lesson',
        on_delete=models.CASCADE,
        related_name='progress_items',
        verbose_name=_('урок'),
    )
    completed = models.BooleanField(_('завершен'), default=False)
    score = models.PositiveSmallIntegerField(_('баллы'), blank=True, null=True)
    notes = models.TextField(_('заметки'), blank=True)
    updated_at = models.DateTimeField(_('обновлен'), auto_now=True)
    created_at = models.DateTimeField(_('создан'), auto_now_add=True)

    class Meta:
        verbose_name = _('Элемент прогресса')
        verbose_name_plural = _('Элементы прогресса')
        unique_together = ['user', 'lesson']
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user} — {self.lesson} ({'✓' if self.completed else '○'})"
