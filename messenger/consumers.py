from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from .models import ChatGroup, GroupMembership, Message, Channel, ChannelMessage
from .serializers import MessageSerializer, ChannelMessageSerializer

User = get_user_model()


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        self.group = await self.get_group(self.group_id)
        if not self.group or not await self.is_group_member(self.group, self.user):
            await self.close()
            return

        self.group_name = f'chat_group_{self.group_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content):
        action = content.get('action')
        if action == 'send.message':
            await self.handle_send_message(content)

    async def handle_send_message(self, content):
        message_type = content.get('message_type', Message.MessageType.TEXT)
        text = content.get('text', '')
        sticker_code = content.get('sticker_code', '')

        if message_type == Message.MessageType.TEXT and not text:
            await self.send_json({'error': 'Текстовое сообщение не может быть пустым.'})
            return

        if message_type == Message.MessageType.STICKER and not sticker_code:
            await self.send_json({'error': 'Код стикера обязателен для стикера.'})
            return

        message = await self.create_message(message_type, text, sticker_code)
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat.message',
                'message': MessageSerializer(message).data,
            },
        )

    async def chat_message(self, event):
        await self.send_json(event['message'])

    @database_sync_to_async
    def get_group(self, group_id):
        try:
            return ChatGroup.objects.get(pk=group_id)
        except ChatGroup.DoesNotExist:
            return None

    @database_sync_to_async
    def is_group_member(self, group, user):
        return GroupMembership.objects.filter(group=group, user=user).exists()

    @database_sync_to_async
    def create_message(self, message_type, text, sticker_code):
        return Message.objects.create(
            group=self.group,
            author=self.user,
            message_type=message_type,
            text=text,
            sticker_code=sticker_code,
        )


class ChannelConsumer(AsyncJsonWebsocketConsumer):
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

        self.group_name = f'chat_channel_{self.channel_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content):
        action = content.get('action')
        if action == 'send.message':
            await self.handle_send_message(content)

    async def handle_send_message(self, content):
        message_type = content.get('message_type', ChannelMessage.MessageType.TEXT)
        text = content.get('text', '')
        sticker_code = content.get('sticker_code', '')

        if message_type == ChannelMessage.MessageType.TEXT and not text:
            await self.send_json({'error': 'Текстовое сообщение не может быть пустым.'})
            return

        if message_type == ChannelMessage.MessageType.STICKER and not sticker_code:
            await self.send_json({'error': 'Код стикера обязателен для стикера.'})
            return

        message = await self.create_message(message_type, text, sticker_code)
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'channel.message',
                'message': ChannelMessageSerializer(message).data,
            },
        )

    async def channel_message(self, event):
        await self.send_json(event['message'])

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
