from django.db import models
from django.utils.translation import gettext_lazy as _


class AitmatovTheme(models.Model):
    name = models.CharField(_('название темы'), max_length=100)
    slug = models.SlugField(_('slug'), max_length=50, unique=True)
    description = models.TextField(_('описание'))
    icon = models.CharField(_('иконка'), max_length=50, blank=True)
    order = models.PositiveSmallIntegerField(_('порядок'), default=0)
    is_active = models.BooleanField(_('активна'), default=True)

    class Meta:
        verbose_name = _('Тема Айтматова')
        verbose_name_plural = _('Темы Айтматова')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name
