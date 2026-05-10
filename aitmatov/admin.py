from django.contrib import admin
from .models import AitmatovTheme


@admin.register(AitmatovTheme)
class AitmatovThemeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order']
