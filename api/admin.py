from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'action', 'user', 'target_type', 'target_name']
    list_filter = ['action', 'target_type', 'created_at']
    search_fields = ['user__email', 'user__username', 'target_name', 'details']
    ordering = ['-created_at']
