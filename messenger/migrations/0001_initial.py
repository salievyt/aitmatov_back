from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='название группы')),
                ('description', models.TextField(blank=True, verbose_name='описание')),
                ('is_private', models.BooleanField(default=False, verbose_name='закрытая группа')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='создано')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='обновлено')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_chat_groups', to=settings.AUTH_USER_MODEL, verbose_name='создатель')),
            ],
            options={
                'verbose_name': 'Чат-группа',
                'verbose_name_plural': 'Чат-группы',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='GroupMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_leader', models.BooleanField(default=False, verbose_name='староста')),
                ('joined_at', models.DateTimeField(auto_now_add=True, verbose_name='дата вступления')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='messenger.chatgroup', verbose_name='группа')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_memberships', to=settings.AUTH_USER_MODEL, verbose_name='пользователь')),
            ],
            options={
                'verbose_name': 'Член группы',
                'verbose_name_plural': 'Члены группы',
                'unique_together': {('user', 'group')},
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message_type', models.CharField(choices=[('text', 'Текст'), ('sticker', 'Стикер'), ('voice', 'Голосовое'), ('video', 'Видео')], default='text', max_length=20, verbose_name='тип сообщения')),
                ('text', models.TextField(blank=True, verbose_name='текст')),
                ('sticker_code', models.CharField(blank=True, max_length=100, verbose_name='стикер')),
                ('attachment', models.FileField(blank=True, null=True, upload_to='messenger/attachments/%Y/%m/', verbose_name='вложение')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='создано')),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='messages', to=settings.AUTH_USER_MODEL, verbose_name='автор')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='messenger.chatgroup', verbose_name='группа')),
            ],
            options={
                'verbose_name': 'Сообщение',
                'verbose_name_plural': 'Сообщения',
                'ordering': ['created_at'],
            },
        ),
    ]
