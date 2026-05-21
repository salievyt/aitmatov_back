from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class FeedbackSubmission(models.Model):
    class FeedbackType(models.TextChoices):
        GENERAL = 'general', _('Общее')
        IDEA = 'idea', _('Идея')
        BUG = 'bug', _('Ошибка')
        COMPLAINT = 'complaint', _('Жалоба')
        SUPPORT = 'support', _('Поддержка')

    class Status(models.TextChoices):
        NEW = 'new', _('Новое')
        IN_PROGRESS = 'in_progress', _('В работе')
        RESOLVED = 'resolved', _('Решено')
        CLOSED = 'closed', _('Закрыто')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedback_submissions',
        verbose_name=_('пользователь'),
    )
    feedback_type = models.CharField(_('тип обращения'), max_length=20, choices=FeedbackType.choices, default=FeedbackType.GENERAL)
    subject = models.CharField(_('тема'), max_length=255)
    message = models.TextField(_('сообщение'))
    rating = models.PositiveSmallIntegerField(
        _('оценка'),
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    contact_email = models.EmailField(_('контактный email'), blank=True)
    is_anonymous = models.BooleanField(_('анонимно'), default=False)
    status = models.CharField(_('статус'), max_length=20, choices=Status.choices, default=Status.NEW)
    admin_notes = models.TextField(_('заметки администратора'), blank=True)
    created_at = models.DateTimeField(_('создано'), auto_now_add=True)
    updated_at = models.DateTimeField(_('обновлено'), auto_now=True)

    class Meta:
        verbose_name = _('Обратная связь')
        verbose_name_plural = _('Обратная связь')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} ({self.get_feedback_type_display()})"


class Survey(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Черновик')
        PUBLISHED = 'published', _('Опубликован')
        CLOSED = 'closed', _('Закрыт')

    title = models.CharField(_('название'), max_length=255)
    description = models.TextField(_('описание'), blank=True)
    status = models.CharField(_('статус'), max_length=20, choices=Status.choices, default=Status.DRAFT)
    is_anonymous = models.BooleanField(_('анонимный опрос'), default=False)
    allow_multiple_submissions = models.BooleanField(_('разрешить несколько отправок'), default=False)
    starts_at = models.DateTimeField(_('начало'), blank=True, null=True)
    ends_at = models.DateTimeField(_('окончание'), blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_surveys',
        verbose_name=_('создатель'),
    )
    created_at = models.DateTimeField(_('создано'), auto_now_add=True)
    updated_at = models.DateTimeField(_('обновлено'), auto_now=True)

    class Meta:
        verbose_name = _('Опрос')
        verbose_name_plural = _('Опросы')
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_active(self):
        now = timezone.now()
        if self.status != self.Status.PUBLISHED:
            return False
        if self.starts_at and self.starts_at > now:
            return False
        if self.ends_at and self.ends_at < now:
            return False
        return True


class SurveyQuestion(models.Model):
    class QuestionType(models.TextChoices):
        SINGLE_CHOICE = 'single_choice', _('Один вариант')
        MULTIPLE_CHOICE = 'multiple_choice', _('Несколько вариантов')
        TEXT = 'text', _('Текст')
        RATING = 'rating', _('Оценка')

    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('опрос'),
    )
    text = models.CharField(_('вопрос'), max_length=500)
    question_type = models.CharField(_('тип вопроса'), max_length=20, choices=QuestionType.choices)
    is_required = models.BooleanField(_('обязательный'), default=True)
    order = models.PositiveSmallIntegerField(_('порядок'), default=0)

    class Meta:
        verbose_name = _('Вопрос опроса')
        verbose_name_plural = _('Вопросы опроса')
        ordering = ['order', 'id']

    def __str__(self):
        return self.text


class SurveyOption(models.Model):
    question = models.ForeignKey(
        SurveyQuestion,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name=_('вопрос'),
    )
    text = models.CharField(_('вариант'), max_length=255)
    order = models.PositiveSmallIntegerField(_('порядок'), default=0)

    class Meta:
        verbose_name = _('Вариант ответа')
        verbose_name_plural = _('Варианты ответов')
        ordering = ['order', 'id']

    def __str__(self):
        return self.text


class SurveyResponse(models.Model):
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name=_('опрос'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='survey_responses',
        verbose_name=_('пользователь'),
    )
    submitted_at = models.DateTimeField(_('отправлено'), auto_now_add=True)

    class Meta:
        verbose_name = _('Ответ на опрос')
        verbose_name_plural = _('Ответы на опрос')
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.survey} — {self.user or 'anonymous'}"


class SurveyAnswer(models.Model):
    response = models.ForeignKey(
        SurveyResponse,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=_('ответ'),
    )
    question = models.ForeignKey(
        SurveyQuestion,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=_('вопрос'),
    )
    text_answer = models.TextField(_('текстовый ответ'), blank=True)
    rating_answer = models.PositiveSmallIntegerField(
        _('оценка'),
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    selected_option_ids = models.JSONField(_('выбранные варианты'), default=list, blank=True)

    class Meta:
        verbose_name = _('Ответ на вопрос')
        verbose_name_plural = _('Ответы на вопросы')

    def __str__(self):
        return f"{self.response_id}:{self.question_id}"
