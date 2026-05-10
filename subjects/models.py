from django.db import models
from django.utils.translation import gettext_lazy as _


class Subject(models.Model):
    name = models.CharField(_('название'), max_length=100, unique=True)
    slug = models.SlugField(_('slug'), max_length=50, unique=True)
    description = models.TextField(_('описание'), blank=True)
    icon = models.CharField(_('иконка'), max_length=50, blank=True, help_text='Material icon name')
    order = models.PositiveSmallIntegerField(_('порядок'), default=0)
    is_active = models.BooleanField(_('активен'), default=True)

    class Meta:
        verbose_name = _('Предмет')
        verbose_name_plural = _('Предметы')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name
