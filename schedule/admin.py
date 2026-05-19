from django.contrib import admin
from .models import DailySchedule


@admin.register(DailySchedule)
class DailyScheduleAdmin(admin.ModelAdmin):
    list_display = ['day', 'title', 'start_time', 'end_time', 'subject', 'teacher', 'is_active']
    list_filter = ['day', 'is_active', 'subject', 'teacher']
    search_fields = ['title', 'description', 'subject__title', 'teacher__email']
    autocomplete_fields = ['subject', 'teacher']
    ordering = ['day', 'start_time']
