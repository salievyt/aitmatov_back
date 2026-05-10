from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        STUDENT = 'student', _('Ученик')
        TEACHER = 'teacher', _('Учитель')
        ADMIN = 'admin', _('Администратор')

    email = models.EmailField(_('email address'), unique=True, blank=True, null=True)
    phone = models.CharField(_('телефон'), max_length=20, unique=True, blank=True, null=True)
    first_name = models.CharField(_('имя'), max_length=150, blank=True)
    last_name = models.CharField(_('фамилия'), max_length=150, blank=True)
    role = models.CharField(_('роль'), max_length=20, choices=Role.choices, default=Role.STUDENT)
    class_level = models.PositiveSmallIntegerField(_('класс'), blank=True, null=True)
    school = models.CharField(_('школа'), max_length=255, blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email or self.phone})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name
