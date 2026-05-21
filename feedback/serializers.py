from django.utils import timezone
from rest_framework import serializers

from users.serializers import UserSerializer
from .models import (
    FeedbackSubmission,
    Survey,
    SurveyQuestion,
    SurveyOption,
    SurveyResponse,
    SurveyAnswer,
)


class FeedbackSubmissionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    feedback_type_label = serializers.CharField(source='get_feedback_type_display', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = FeedbackSubmission
        fields = [
            'id', 'user', 'feedback_type', 'feedback_type_label', 'subject', 'message',
            'rating', 'contact_email', 'is_anonymous', 'status', 'status_label',
            'admin_notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'status', 'status_label', 'admin_notes', 'created_at', 'updated_at']


class FeedbackSubmissionAdminSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = FeedbackSubmission
        fields = [
            'id', 'user', 'feedback_type', 'subject', 'message', 'rating', 'contact_email',
            'is_anonymous', 'status', 'admin_notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class SurveyOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyOption
        fields = ['id', 'text', 'order']


class SurveyQuestionSerializer(serializers.ModelSerializer):
    options = SurveyOptionSerializer(many=True, read_only=True)
    question_type_label = serializers.CharField(source='get_question_type_display', read_only=True)

    class Meta:
        model = SurveyQuestion
        fields = ['id', 'text', 'question_type', 'question_type_label', 'is_required', 'order', 'options']


class SurveySerializer(serializers.ModelSerializer):
    questions = SurveyQuestionSerializer(many=True, read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    questions_count = serializers.IntegerField(source='questions.count', read_only=True)
    responses_count = serializers.IntegerField(source='responses.count', read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Survey
        fields = [
            'id', 'title', 'description', 'status', 'status_label',
            'is_anonymous', 'allow_multiple_submissions',
            'starts_at', 'ends_at', 'is_active',
            'questions', 'questions_count', 'responses_count',
            'created_at', 'updated_at',
        ]


class SurveyOptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyOption
        fields = ['text', 'order']


class SurveyQuestionCreateSerializer(serializers.ModelSerializer):
    options = SurveyOptionCreateSerializer(many=True, required=False)

    class Meta:
        model = SurveyQuestion
        fields = ['text', 'question_type', 'is_required', 'order', 'options']


class SurveyCreateSerializer(serializers.ModelSerializer):
    questions = SurveyQuestionCreateSerializer(many=True, required=False)

    class Meta:
        model = Survey
        fields = [
            'title', 'description', 'status', 'is_anonymous',
            'allow_multiple_submissions', 'starts_at', 'ends_at', 'questions',
        ]

    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        survey = Survey.objects.create(**validated_data)
        self._replace_questions(survey, questions_data)
        return survey

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if questions_data is not None:
            self._replace_questions(instance, questions_data)
        return instance

    def _replace_questions(self, survey, questions_data):
        survey.questions.all().delete()
        for question_data in questions_data:
            options_data = question_data.pop('options', [])
            question = SurveyQuestion.objects.create(survey=survey, **question_data)
            for option_data in options_data:
                SurveyOption.objects.create(question=question, **option_data)


class SurveyAnswerInputSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    text_answer = serializers.CharField(required=False, allow_blank=True)
    rating_answer = serializers.IntegerField(required=False, min_value=1, max_value=5)
    selected_option_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
    )


class SurveySubmitSerializer(serializers.Serializer):
    answers = SurveyAnswerInputSerializer(many=True)

    def validate(self, data):
        survey = self.context['survey']
        user = self.context['request'].user
        now = timezone.now()

        if survey.status != Survey.Status.PUBLISHED:
            raise serializers.ValidationError('Опрос не опубликован.')
        if survey.starts_at and survey.starts_at > now:
            raise serializers.ValidationError('Опрос еще не начался.')
        if survey.ends_at and survey.ends_at < now:
            raise serializers.ValidationError('Опрос уже завершен.')
        if not survey.allow_multiple_submissions and SurveyResponse.objects.filter(survey=survey, user=user).exists():
            raise serializers.ValidationError('Вы уже отправляли ответы на этот опрос.')

        questions = {question.id: question for question in survey.questions.prefetch_related('options').all()}
        answers = data.get('answers', [])
        answers_by_question = {}

        for answer in answers:
            question = questions.get(answer['question_id'])
            if question is None:
                raise serializers.ValidationError(f"Вопрос {answer['question_id']} не принадлежит этому опросу.")
            if answer['question_id'] in answers_by_question:
                raise serializers.ValidationError(f"Вопрос {answer['question_id']} передан несколько раз.")

            selected_option_ids = answer.get('selected_option_ids', [])
            if selected_option_ids:
                valid_option_ids = set(question.options.values_list('id', flat=True))
                invalid_ids = [option_id for option_id in selected_option_ids if option_id not in valid_option_ids]
                if invalid_ids:
                    raise serializers.ValidationError(f"Некорректные варианты ответа для вопроса {question.id}: {invalid_ids}")

            if question.question_type == SurveyQuestion.QuestionType.TEXT and not answer.get('text_answer'):
                raise serializers.ValidationError(f'Для вопроса {question.id} требуется text_answer.')
            if question.question_type == SurveyQuestion.QuestionType.RATING and answer.get('rating_answer') is None:
                raise serializers.ValidationError(f'Для вопроса {question.id} требуется rating_answer.')
            if question.question_type == SurveyQuestion.QuestionType.SINGLE_CHOICE and len(selected_option_ids) != 1:
                raise serializers.ValidationError(f'Для вопроса {question.id} нужно выбрать ровно один вариант.')
            if question.question_type == SurveyQuestion.QuestionType.MULTIPLE_CHOICE and not selected_option_ids and question.is_required:
                raise serializers.ValidationError(f'Для вопроса {question.id} нужно выбрать хотя бы один вариант.')

            answers_by_question[question.id] = answer

        missing_required = [
            question.id for question in questions.values()
            if question.is_required and question.id not in answers_by_question
        ]
        if missing_required:
            raise serializers.ValidationError(f'Не заполнены обязательные вопросы: {missing_required}')

        return data

    def create(self, validated_data):
        survey = self.context['survey']
        user = self.context['request'].user
        response = SurveyResponse.objects.create(
            survey=survey,
            user=user,
        )
        for answer_data in validated_data['answers']:
            SurveyAnswer.objects.create(
                response=response,
                question_id=answer_data['question_id'],
                text_answer=answer_data.get('text_answer', ''),
                rating_answer=answer_data.get('rating_answer'),
                selected_option_ids=answer_data.get('selected_option_ids', []),
            )
        return response


class SurveyAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyAnswer
        fields = ['id', 'question', 'text_answer', 'rating_answer', 'selected_option_ids']


class SurveyResponseSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    answers = SurveyAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = SurveyResponse
        fields = ['id', 'survey', 'user', 'submitted_at', 'answers']
