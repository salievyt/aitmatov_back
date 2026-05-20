from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class ChatGroup(models.Model):
    name = models.CharField(_('название группы'), max_length=255)
    description = models.TextField(_('описание'), blank=True)
    is_private = models.BooleanField(_('закрытая группа'), default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_chat_groups',
        verbose_name=_('создатель'),
    )
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='administered_chat_groups',
        verbose_name=_('Администратор'),
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='GroupMembership',
        related_name='chat_groups',
    )
    created_at = models.DateTimeField(_('создано'), auto_now_add=True)
    updated_at = models.DateTimeField(_('обновлено'), auto_now=True)

    class Meta:
        verbose_name = _('Чат-группа')
        verbose_name_plural = _('Чат-группы')
        ordering = ['-updated_at']

    def __str__(self):
        return self.name

    @property
    def leader_id(self):
        leader = self.memberships.filter(is_leader=True).first()
        return leader.user_id if leader else None

    @property
    def members_count(self):
        return self.memberships.count()


class GroupMembership(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='group_memberships',
        verbose_name=_('пользователь'),
    )
    group = models.ForeignKey(
        ChatGroup,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name=_('группа'),
    )
    is_leader = models.BooleanField(_('староста'), default=False)
    joined_at = models.DateTimeField(_('дата вступления'), auto_now_add=True)

    class Meta:
        verbose_name = _('Член группы')
        verbose_name_plural = _('Члены группы')
        unique_together = ('user', 'group')

    def __str__(self):
        return f"{self.user} in {self.group}"


class Message(models.Model):
    class MessageType(models.TextChoices):
        TEXT = 'text', _('Текст')
        STICKER = 'sticker', _('Стикер')
        VOICE = 'voice', _('Голосовое')
        VIDEO = 'video', _('Видео')

    group = models.ForeignKey(
        ChatGroup,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('группа'),
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='messages',
        verbose_name=_('автор'),
    )
    message_type = models.CharField(
        _('тип сообщения'),
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT,
    )
    text = models.TextField(_('текст'), blank=True)
    sticker_code = models.CharField(_('стикер'), max_length=100, blank=True)
    attachment = models.FileField(
        _('вложение'),
        upload_to='messenger/attachments/%Y/%m/',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(_('создано'), auto_now_add=True)

    class Meta:
        verbose_name = _('Сообщение')
        verbose_name_plural = _('Сообщения')
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author}: {self.message_type} ({self.group})"


class Channel(models.Model):
    name = models.CharField(_('название канала'), max_length=255, unique=True)
    description = models.TextField(_('описание'), blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_channels',
        verbose_name=_('создатель'),
    )
    created_at = models.DateTimeField(_('создано'), auto_now_add=True)
    updated_at = models.DateTimeField(_('обновлено'), auto_now=True)

    class Meta:
        verbose_name = _('Канал')
        verbose_name_plural = _('Каналы')
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Проверяем, что создатель - администратор платформы
        if self.created_by and not (self.created_by.role == 'admin' or self.created_by.is_staff):
            raise ValueError(_('Только администраторы платформы могут создавать каналы.'))
        super().save(*args, **kwargs)


class ChannelMessage(models.Model):
    class MessageType(models.TextChoices):
        TEXT = 'text', _('Текст')
        STICKER = 'sticker', _('Стикер')
        VOICE = 'voice', _('Голосовое')
        VIDEO = 'video', _('Видео')

    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('канал'),
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='channel_messages',
        verbose_name=_('автор'),
    )
    message_type = models.CharField(
        _('тип сообщения'),
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT,
    )
    text = models.TextField(_('текст'), blank=True)
    sticker_code = models.CharField(_('стикер'), max_length=100, blank=True)
    attachment = models.FileField(
        _('вложение'),
        upload_to='messenger/channel_attachments/%Y/%m/',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(_('создано'), auto_now_add=True)

    class Meta:
        verbose_name = _('Сообщение канала')
        verbose_name_plural = _('Сообщения канала')
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author}: {self.message_type} ({self.channel})"
