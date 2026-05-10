from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'phone', 'first_name', 'last_name', 'role', 'class_level', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'class_level']
    search_fields = ['email', 'phone', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'phone', 'password')}),
        (_('Персональная информация'), {'fields': ('first_name', 'last_name', 'role', 'class_level', 'school')}),
        (_('Права'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Даты'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
