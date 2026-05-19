from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class DailySchedule(models.Model):
    class WeekDay(models.IntegerChoices):
        MONDAY = 1, _('Понедельник')
        TUESDAY = 2, _('Вторник')
        WEDNESDAY = 3, _('Среда')
        THURSDAY = 4, _('Четверг')
        FRIDAY = 5, _('Пятница')
        SATURDAY = 6, _('Суббота')
        SUNDAY = 7, _('Воскресенье')

    day = models.PositiveSmallIntegerField(_('день недели'), choices=WeekDay.choices)
    title = models.CharField(_('название'), max_length=200)
    description = models.TextField(_('описание'), blank=True)
    start_time = models.TimeField(_('начало'))
    end_time = models.TimeField(_('конец'))
    subject = models.ForeignKey(
        'subjects.Subject',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='daily_schedules',
        verbose_name=_('предмет'),
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='daily_schedules',
        verbose_name=_('учитель'),
    )
    is_active = models.BooleanField(_('активен'), default=True)
    created_at = models.DateTimeField(_('создан'), auto_now_add=True)
    updated_at = models.DateTimeField(_('обновлен'), auto_now=True)

    class Meta:
        verbose_name = _('Элемент расписания')
        verbose_name_plural = _('Расписания по дням')
        ordering = ['day', 'start_time', 'title']

    def __str__(self):
        return f"{self.get_day_display()} — {self.title}"
