from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Course(models.Model):
    title = models.CharField(_('название'), max_length=200)
    description = models.TextField(_('описание'), blank=True)
    subject = models.ForeignKey(
        'subjects.Subject',
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name=_('предмет'),
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='teaching_courses',
        verbose_name=_('учитель'),
    )
    is_aitmatov = models.BooleanField(_('курс Айтматова'), default=False)
    aitmatov_theme = models.ForeignKey(
        'aitmatov.AitmatovTheme',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name=_('тема Айтматова'),
    )
    class_level = models.PositiveSmallIntegerField(_('класс'), blank=True, null=True)
    image = models.ImageField(_('изображение'), upload_to='courses/', blank=True, null=True)
    is_active = models.BooleanField(_('активен'), default=True)
    created_at = models.DateTimeField(_('создан'), auto_now_add=True)
    updated_at = models.DateTimeField(_('обновлен'), auto_now=True)

    class Meta:
        verbose_name = _('Курс')
        verbose_name_plural = _('Курсы')
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Lesson(models.Model):
    class ContentType(models.TextChoices):
        TEXT = 'text', _('Текст')
        VIDEO = 'video', _('Видео')
        AUDIO = 'audio', _('Аудио')

    title = models.CharField(_('название'), max_length=200)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name=_('курс'),
    )
    order = models.PositiveSmallIntegerField(_('порядок'), default=0)
    content_type = models.CharField(
        _('тип контента'),
        max_length=20,
        choices=ContentType.choices,
        default=ContentType.TEXT,
    )
    video_url = models.URLField(_('URL видео'), blank=True, null=True)
    text_body = models.TextField(_('текст урока'), blank=True)
    quiz_enabled = models.BooleanField(_('включить тест'), default=False)
    is_active = models.BooleanField(_('активен'), default=True)
    created_at = models.DateTimeField(_('создан'), auto_now_add=True)

    class Meta:
        verbose_name = _('Урок')
        verbose_name_plural = _('Уроки')
        ordering = ['course', 'order', 'title']

    def __str__(self):
        return f"{self.course.title} — {self.title}"
