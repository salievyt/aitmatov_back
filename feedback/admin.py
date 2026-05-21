from django.contrib import admin

from .models import FeedbackSubmission, Survey, SurveyQuestion, SurveyOption, SurveyResponse, SurveyAnswer


class SurveyOptionInline(admin.TabularInline):
    model = SurveyOption
    extra = 1


class SurveyQuestionInline(admin.StackedInline):
    model = SurveyQuestion
    extra = 1


@admin.register(FeedbackSubmission)
class FeedbackSubmissionAdmin(admin.ModelAdmin):
    list_display = ['subject', 'feedback_type', 'user', 'status', 'rating', 'created_at']
    list_filter = ['feedback_type', 'status', 'is_anonymous', 'created_at']
    search_fields = ['subject', 'message', 'contact_email', 'user__email', 'user__phone']
    ordering = ['-created_at']


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'is_anonymous', 'allow_multiple_submissions', 'created_by', 'created_at']
    list_filter = ['status', 'is_anonymous', 'allow_multiple_submissions', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['-created_at']
    inlines = [SurveyQuestionInline]


@admin.register(SurveyQuestion)
class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display = ['survey', 'text', 'question_type', 'is_required', 'order']
    list_filter = ['question_type', 'is_required']
    search_fields = ['text', 'survey__title']
    inlines = [SurveyOptionInline]


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ['survey', 'user', 'submitted_at']
    search_fields = ['survey__title', 'user__email', 'user__phone']
    ordering = ['-submitted_at']


@admin.register(SurveyAnswer)
class SurveyAnswerAdmin(admin.ModelAdmin):
    list_display = ['response', 'question', 'rating_answer']
    search_fields = ['question__text', 'response__survey__title']
