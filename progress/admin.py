from django.contrib import admin
from .models import ProgressItem


@admin.register(ProgressItem)
class ProgressItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'completed', 'score', 'updated_at']
    list_filter = ['completed']
    search_fields = ['user__email', 'lesson__title']
    autocomplete_fields = ['user', 'lesson']
    list_select_related = ['user', 'lesson']
