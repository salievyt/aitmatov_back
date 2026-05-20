from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class ProgressItem(models.Model):
    class GradeScale(models.IntegerChoices):
        ONE = 1, _('1')
        TWO = 2, _('2')
        THREE = 3, _('3')
        FOUR = 4, _('4')
        FIVE = 5, _('5')

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
    grade = models.PositiveSmallIntegerField(
        _('оценка'),
        choices=GradeScale.choices,
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
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


class QuarterGrade(models.Model):
    class Quarter(models.IntegerChoices):
        FIRST = 1, _('1 четверть')
        SECOND = 2, _('2 четверть')
        THIRD = 3, _('3 четверть')
        FOURTH = 4, _('4 четверть')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quarter_grades',
        verbose_name=_('ученик'),
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='quarter_grades',
        verbose_name=_('курс'),
    )
    quarter = models.PositiveSmallIntegerField(
        _('четверть'),
        choices=Quarter.choices,
        default=Quarter.FIRST,
    )
    grade = models.PositiveSmallIntegerField(
        _('оценка'),
        choices=ProgressItem.GradeScale.choices,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    notes = models.TextField(_('комментарий'), blank=True)
    updated_at = models.DateTimeField(_('обновлен'), auto_now=True)
    created_at = models.DateTimeField(_('создан'), auto_now_add=True)

    class Meta:
        verbose_name = _('четвертная оценка')
        verbose_name_plural = _('четвертные оценки')
        unique_together = ['user', 'course', 'quarter']
        ordering = ['course', 'user', 'quarter']

    def __str__(self):
        return f"{self.user} — {self.course} ({self.get_quarter_display()}): {self.grade}"
