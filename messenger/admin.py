from django.contrib import admin

from .models import ChatGroup, GroupMembership, Message


@admin.register(ChatGroup)
class ChatGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_by', 'is_private', 'created_at')
    search_fields = ('name', 'description')


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'group', 'is_leader', 'joined_at')
    list_filter = ('is_leader',)
    search_fields = ('user__email', 'group__name')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'group', 'author', 'message_type', 'created_at')
    list_filter = ('message_type',)
    search_fields = ('text', 'sticker_code', 'author__email')
