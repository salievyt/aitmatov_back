from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import ChatGroup, GroupMembership, Message, Channel, ChannelMessage
from .serializers import MessageSerializer, ChannelMessageSerializer


class BaseMessageConsumer(AsyncJsonWebsocketConsumer):
    history_limit_default = 50
    history_limit_max = 100

    async def receive_json(self, content):
        action = content.get('action')
        if action == 'history':
            await self.handle_history(content)
            return
        if action == 'send.message':
            await self.handle_send_message(content)
            return
        if action == 'ping':
            await self.send_json({'type': 'pong'})
            return
        await self.send_error('Unsupported action.')

    async def handle_history(self, content):
        limit = self._normalize_limit(content.get('limit'))
        before_id = content.get('before_id')
        items = await self.get_history(limit=limit, before_id=before_id)
        await self.send_json({
            'type': 'history',
            'items': items,
            'limit': limit,
            'before_id': before_id,
        })

    async def handle_send_message(self, content):
        message_type = content.get('message_type', self.message_type_enum.TEXT)
        text = content.get('text', '')
        sticker_code = content.get('sticker_code', '')

        validation_error = self.validate_message_payload(
            message_type=message_type,
            text=text,
            sticker_code=sticker_code,
        )
        if validation_error:
            await self.send_error(validation_error)
            return

        message = await self.create_message(
            message_type=message_type,
            text=text,
            sticker_code=sticker_code,
        )
        payload = await self.serialize_message(message)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': self.broadcast_event_type,
                'message': payload,
            },
        )

    async def broadcast_message(self, event):
        await self.send_json({
            'type': 'message',
            'data': event['message'],
        })

    async def send_error(self, error_message):
        await self.send_json({
            'type': 'error',
            'error': error_message,
        })

    def validate_message_payload(self, message_type, text, sticker_code):
        if message_type == self.message_type_enum.TEXT and not text:
            return 'Text message cannot be empty.'
        if message_type == self.message_type_enum.STICKER and not sticker_code:
            return 'Sticker code is required for sticker messages.'
        if message_type in [self.message_type_enum.VOICE, self.message_type_enum.VIDEO]:
            return 'Voice and video messages still require HTTP upload flow for attachments.'
        return None

    def _normalize_limit(self, raw_limit):
        try:
            parsed = int(raw_limit or self.history_limit_default)
        except (TypeError, ValueError):
            parsed = self.history_limit_default
        return max(1, min(parsed, self.history_limit_max))


class ChatConsumer(BaseMessageConsumer):
    broadcast_event_type = 'broadcast_message'
    message_type_enum = Message.MessageType

    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        self.group = await self.get_group(self.group_id)
        if not self.group or not await self.is_group_member():
            await self.close()
            return

        self.room_group_name = f'chat_group_{self.group_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.send_json({
            'type': 'connected',
            'room': 'group',
            'group_id': int(self.group_id),
        })

    async def disconnect(self, code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    @database_sync_to_async
    def get_group(self, group_id):
        try:
            return ChatGroup.objects.get(pk=group_id)
        except ChatGroup.DoesNotExist:
            return None

    @database_sync_to_async
    def is_group_member(self):
        return GroupMembership.objects.filter(group=self.group, user=self.user).exists()

    @database_sync_to_async
    def create_message(self, message_type, text, sticker_code):
        return Message.objects.create(
            group=self.group,
            author=self.user,
            message_type=message_type,
            text=text,
            sticker_code=sticker_code,
        )

    @database_sync_to_async
    def get_history(self, limit, before_id=None):
        queryset = Message.objects.filter(group=self.group).select_related('author').order_by('-id')
        if before_id:
            queryset = queryset.filter(id__lt=before_id)
        items = list(queryset[:limit])
        items.reverse()
        return MessageSerializer(items, many=True).data

    @database_sync_to_async
    def serialize_message(self, message):
        return MessageSerializer(message).data


class ChannelConsumer(BaseMessageConsumer):
    broadcast_event_type = 'broadcast_message'
    message_type_enum = ChannelMessage.MessageType

    async def connect(self):
        self.channel_id = self.scope['url_route']['kwargs']['channel_id']
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        self.channel = await self.get_channel(self.channel_id)
        if not self.channel:
            await self.close()
            return

        self.room_group_name = f'chat_channel_{self.channel_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.send_json({
            'type': 'connected',
            'room': 'channel',
            'channel_id': int(self.channel_id),
        })

    async def disconnect(self, code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    @database_sync_to_async
    def get_channel(self, channel_id):
        try:
            return Channel.objects.get(pk=channel_id)
        except Channel.DoesNotExist:
            return None

    @database_sync_to_async
    def create_message(self, message_type, text, sticker_code):
        return ChannelMessage.objects.create(
            channel=self.channel,
            author=self.user,
            message_type=message_type,
            text=text,
            sticker_code=sticker_code,
        )

    @database_sync_to_async
    def get_history(self, limit, before_id=None):
        queryset = ChannelMessage.objects.filter(channel=self.channel).select_related('author').order_by('-id')
        if before_id:
            queryset = queryset.filter(id__lt=before_id)
        items = list(queryset[:limit])
        items.reverse()
        return ChannelMessageSerializer(items, many=True).data

    @database_sync_to_async
    def serialize_message(self, message):
        return ChannelMessageSerializer(message).data
