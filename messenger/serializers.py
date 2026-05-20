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
    member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = ChatGroup
        fields = [
            'id', 'name', 'description', 'is_private',
            'created_by', 'admin', 'leader_id', 'members_count', 'member_ids',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'created_by', 'admin', 'leader_id', 'members_count',
            'created_at', 'updated_at',
        ]

    def create(self, validated_data):
        validated_data.pop('member_ids', None)
        return super().create(validated_data)


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


class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['message_type', 'text', 'sticker_code', 'attachment']

    def validate(self, data):
        message_type = data.get('message_type')
        if message_type == Message.MessageType.TEXT and not data.get('text'):
            raise serializers.ValidationError({'text': 'Текстовое сообщение не может быть пустым.'})
        if message_type == Message.MessageType.STICKER and not data.get('sticker_code'):
            raise serializers.ValidationError({'sticker_code': 'Код стикера обязателен для стикера.'})
        return data


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


class ChannelMessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelMessage
        fields = ['message_type', 'text', 'sticker_code', 'attachment']

    def validate(self, data):
        message_type = data.get('message_type')
        if message_type == ChannelMessage.MessageType.TEXT and not data.get('text'):
            raise serializers.ValidationError({'text': 'Текстовое сообщение не может быть пустым.'})
        if message_type == ChannelMessage.MessageType.STICKER and not data.get('sticker_code'):
            raise serializers.ValidationError({'sticker_code': 'Код стикера обязателен для стикера.'})
        return data


class ChannelSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Channel
        fields = ['id', 'name', 'description', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def validate(self, data):
        user = self.context['request'].user
        if user and not (user.role == 'admin' or user.is_staff):
            raise serializers.ValidationError('Только администраторы платформы могут создавать каналы.')
        return data
        if message_type in [Message.MessageType.VOICE, Message.MessageType.VIDEO] and not data.get('attachment'):
            raise serializers.ValidationError({'attachment': 'Файл обязателен для голосового или видео сообщения.'})
        return data


class AssignLeaderSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
