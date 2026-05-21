from django.contrib.auth import get_user_model
from rest_framework import serializers

from users.serializers import UserSerializer
from .models import ChatGroup, GroupMembership, Message, Channel, ChannelMessage

User = get_user_model()


class UserMiniSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'avatar', 'avatar_url', 'role']
        read_only_fields = fields

    def get_avatar_url(self, obj):
        request = self.context.get('request')
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return obj.avatar.url if obj.avatar else None


class GroupMembershipSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = GroupMembership
        fields = ['id', 'user', 'user_id', 'is_leader', 'joined_at']
        read_only_fields = ['id', 'user', 'joined_at']


class ChatGroupSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    admin = UserSerializer(read_only=True)
    leader_id = serializers.IntegerField(read_only=True)
    members_count = serializers.IntegerField(read_only=True)
    websocket_path = serializers.SerializerMethodField()
    member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = ChatGroup
        fields = [
            'id', 'name', 'description', 'is_private',
            'created_by', 'admin', 'leader_id', 'members_count', 'websocket_path', 'member_ids',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'created_by', 'admin', 'leader_id', 'members_count',
            'created_at', 'updated_at',
        ]

    def create(self, validated_data):
        validated_data.pop('member_ids', None)
        return super().create(validated_data)

    def get_websocket_path(self, obj):
        return f'/ws/messenger/{obj.id}/'


class ChatGroupDetailSerializer(ChatGroupSerializer):
    members = GroupMembershipSerializer(source='memberships', many=True, read_only=True)

    class Meta(ChatGroupSerializer.Meta):
        fields = ChatGroupSerializer.Meta.fields + ['members']


class MessageSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    author_id = serializers.IntegerField(read_only=True)
    attachment_url = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'group', 'author', 'author_id',
            'message_type', 'text', 'sticker_code',
            'attachment', 'attachment_url', 'created_at',
        ]
        read_only_fields = ['id', 'author', 'author_id', 'created_at']

    def get_attachment_url(self, obj):
        request = self.context.get('request')
        if obj.attachment and request:
            return request.build_absolute_uri(obj.attachment.url)
        return obj.attachment.url if obj.attachment else None


class AssignLeaderSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()

    def validate_user_id(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError('Пользователь не найден.')
        return value


class ChannelMessageSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    author_id = serializers.IntegerField(read_only=True)
    attachment_url = serializers.SerializerMethodField()

    class Meta:
        model = ChannelMessage
        fields = [
            'id', 'channel', 'author', 'author_id',
            'message_type', 'text', 'sticker_code',
            'attachment', 'attachment_url', 'created_at',
        ]
        read_only_fields = ['id', 'author', 'author_id', 'created_at']

    def get_attachment_url(self, obj):
        request = self.context.get('request')
        if obj.attachment and request:
            return request.build_absolute_uri(obj.attachment.url)
        return obj.attachment.url if obj.attachment else None


class ChannelSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    websocket_path = serializers.SerializerMethodField()

    class Meta:
        model = Channel
        fields = ['id', 'name', 'description', 'created_by', 'websocket_path', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def validate(self, data):
        user = self.context['request'].user
        if user and not (user.role == 'admin' or user.is_staff):
            raise serializers.ValidationError('Только администраторы платформы могут создавать каналы.')
        return data

    def get_websocket_path(self, obj):
        return f'/ws/messenger/channels/{obj.id}/'
