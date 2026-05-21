from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FeedbackSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('feedback_type', models.CharField(choices=[('general', 'Общее'), ('idea', 'Идея'), ('bug', 'Ошибка'), ('complaint', 'Жалоба'), ('support', 'Поддержка')], default='general', max_length=20, verbose_name='тип обращения')),
                ('subject', models.CharField(max_length=255, verbose_name='тема')),
                ('message', models.TextField(verbose_name='сообщение')),
                ('rating', models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='оценка')),
                ('contact_email', models.EmailField(blank=True, max_length=254, verbose_name='контактный email')),
                ('is_anonymous', models.BooleanField(default=False, verbose_name='анонимно')),
                ('status', models.CharField(choices=[('new', 'Новое'), ('in_progress', 'В работе'), ('resolved', 'Решено'), ('closed', 'Закрыто')], default='new', max_length=20, verbose_name='статус')),
                ('admin_notes', models.TextField(blank=True, verbose_name='заметки администратора')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='создано')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='обновлено')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='feedback_submissions', to=settings.AUTH_USER_MODEL, verbose_name='пользователь')),
            ],
            options={
                'verbose_name': 'Обратная связь',
                'verbose_name_plural': 'Обратная связь',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Survey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='название')),
                ('description', models.TextField(blank=True, verbose_name='описание')),
                ('status', models.CharField(choices=[('draft', 'Черновик'), ('published', 'Опубликован'), ('closed', 'Закрыт')], default='draft', max_length=20, verbose_name='статус')),
                ('is_anonymous', models.BooleanField(default=False, verbose_name='анонимный опрос')),
                ('allow_multiple_submissions', models.BooleanField(default=False, verbose_name='разрешить несколько отправок')),
                ('starts_at', models.DateTimeField(blank=True, null=True, verbose_name='начало')),
                ('ends_at', models.DateTimeField(blank=True, null=True, verbose_name='окончание')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='создано')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='обновлено')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_surveys', to=settings.AUTH_USER_MODEL, verbose_name='создатель')),
            ],
            options={
                'verbose_name': 'Опрос',
                'verbose_name_plural': 'Опросы',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SurveyQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=500, verbose_name='вопрос')),
                ('question_type', models.CharField(choices=[('single_choice', 'Один вариант'), ('multiple_choice', 'Несколько вариантов'), ('text', 'Текст'), ('rating', 'Оценка')], max_length=20, verbose_name='тип вопроса')),
                ('is_required', models.BooleanField(default=True, verbose_name='обязательный')),
                ('order', models.PositiveSmallIntegerField(default=0, verbose_name='порядок')),
                ('survey', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='feedback.survey', verbose_name='опрос')),
            ],
            options={
                'verbose_name': 'Вопрос опроса',
                'verbose_name_plural': 'Вопросы опроса',
                'ordering': ['order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='SurveyOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=255, verbose_name='вариант')),
                ('order', models.PositiveSmallIntegerField(default=0, verbose_name='порядок')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='feedback.surveyquestion', verbose_name='вопрос')),
            ],
            options={
                'verbose_name': 'Вариант ответа',
                'verbose_name_plural': 'Варианты ответов',
                'ordering': ['order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='SurveyResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('submitted_at', models.DateTimeField(auto_now_add=True, verbose_name='отправлено')),
                ('survey', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='feedback.survey', verbose_name='опрос')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='survey_responses', to=settings.AUTH_USER_MODEL, verbose_name='пользователь')),
            ],
            options={
                'verbose_name': 'Ответ на опрос',
                'verbose_name_plural': 'Ответы на опрос',
                'ordering': ['-submitted_at'],
            },
        ),
        migrations.CreateModel(
            name='SurveyAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text_answer', models.TextField(blank=True, verbose_name='текстовый ответ')),
                ('rating_answer', models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='оценка')),
                ('selected_option_ids', models.JSONField(blank=True, default=list, verbose_name='выбранные варианты')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='feedback.surveyquestion', verbose_name='вопрос')),
                ('response', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='feedback.surveyresponse', verbose_name='ответ')),
            ],
            options={
                'verbose_name': 'Ответ на вопрос',
                'verbose_name_plural': 'Ответы на вопросы',
            },
        ),
    ]
