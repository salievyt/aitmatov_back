from django.contrib import admin
from .models import ProgressItem, QuarterGrade


@admin.register(ProgressItem)
class ProgressItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'completed', 'score', 'grade', 'updated_at']
    list_filter = ['completed']
    search_fields = ['user__email', 'lesson__title']
    autocomplete_fields = ['user', 'lesson']
    list_select_related = ['user', 'lesson']


@admin.register(QuarterGrade)
class QuarterGradeAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'quarter', 'grade', 'updated_at']
    list_filter = ['quarter', 'course']
    search_fields = ['user__email', 'course__title']
    autocomplete_fields = ['user', 'course']
    list_select_related = ['user', 'course']
