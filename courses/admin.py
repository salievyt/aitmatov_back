from django.contrib import admin
from .models import Course, Lesson


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    ordering = ['order']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'teacher', 'is_aitmatov', 'class_level', 'is_active', 'created_at']
    list_filter = ['subject', 'is_aitmatov', 'class_level', 'is_active']
    search_fields = ['title', 'description']
    inlines = [LessonInline]
    autocomplete_fields = ['teacher', 'subject', 'aitmatov_theme']
    list_select_related = ['subject', 'teacher']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'content_type', 'quiz_enabled', 'is_active']
    list_filter = ['content_type', 'quiz_enabled', 'is_active']
    search_fields = ['title', 'course__title']
    ordering = ['course', 'order']
    list_select_related = ['course']
