from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import ChatGroup, GroupMembership, Message, Channel, ChannelMessage
from .serializers import (
    AssignLeaderSerializer,
    ChatGroupDetailSerializer,
    ChatGroupSerializer,
    GroupMembershipSerializer,
    MessageCreateSerializer,
    MessageSerializer,
    ChannelSerializer,
    ChannelMessageSerializer,
    ChannelMessageCreateSerializer,
)

User = get_user_model()


def is_group_member(user, group):
    return GroupMembership.objects.filter(group=group, user=user).exists()


def is_group_leader(user, group):
    return GroupMembership.objects.filter(group=group, user=user, is_leader=True).exists()


def can_manage_group(user, group):
    return is_group_leader(user, group) or getattr(user, 'role', None) == User.Role.ADMIN or user.is_staff


def is_platform_admin(user):
    return getattr(user, 'role', None) == User.Role.ADMIN or user.is_staff


def broadcast_message(message):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    async_to_sync(channel_layer.group_send)(
        f'chat_group_{message.group_id}',
        {
            'type': 'chat.message',
            'message': MessageSerializer(message).data,
        },
    )


def broadcast_channel_message(message):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    async_to_sync(channel_layer.group_send)(
        f'chat_channel_{message.channel_id}',
        {
            'type': 'channel.message',
            'message': ChannelMessageSerializer(message).data,
        },
    )


class ChatGroupListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatGroup.objects.filter(members=self.request.user).prefetch_related('memberships__user', 'created_by')

    def perform_create(self, serializer):
        member_ids = self.request.data.get('member_ids', []) or []
        group = serializer.save(created_by=self.request.user, admin=self.request.user)
        GroupMembership.objects.create(group=group, user=self.request.user, is_leader=True)
        for member_id in set(member_ids):
            if member_id == self.request.user.id:
                continue
            user = get_object_or_404(User, id=member_id)
            GroupMembership.objects.get_or_create(group=group, user=user)


class ChatGroupDetailView(generics.RetrieveAPIView):
    serializer_class = ChatGroupDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = ChatGroup.objects.all().prefetch_related('memberships__user', 'created_by')

    def get_object(self):
        group = super().get_object()
        if not is_group_member(self.request.user, group):
            raise permissions.PermissionDenied('Вы не участник группы.')
        return group


class GroupMembershipListCreateView(generics.ListCreateAPIView):
    serializer_class = GroupMembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_group(self):
        return get_object_or_404(ChatGroup, pk=self.kwargs['group_id'])

    def get_queryset(self):
        group = self.get_group()
        if not is_group_member(self.request.user, group):
            raise permissions.PermissionDenied('Вы не участник группы.')
        return GroupMembership.objects.filter(group=group).select_related('user')

    def perform_create(self, serializer):
        group = self.get_group()
        if not can_manage_group(self.request.user, group):
            raise permissions.PermissionDenied('Только лидер группы или администратор могут добавлять участников.')
        user_id = self.request.data.get('user_id')
        user = get_object_or_404(User, id=user_id)
        serializer.save(group=group, user=user)


class GroupLeaderAssignView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, group_id):
        group = get_object_or_404(ChatGroup, pk=group_id)
        if not can_manage_group(request.user, group):
            raise permissions.PermissionDenied('Только лидер группы или администратор могут назначать старосту.')
        serializer = AssignLeaderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data['user_id']
        membership = get_object_or_404(GroupMembership, group=group, user_id=user_id)
        GroupMembership.objects.filter(group=group, is_leader=True).update(is_leader=False)
        membership.is_leader = True
        membership.save()
        return Response(GroupMembershipSerializer(membership).data)


class MessageListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_group(self):
        return get_object_or_404(ChatGroup, pk=self.kwargs['group_id'])

    def get_queryset(self):
        group = self.get_group()
        if not is_group_member(self.request.user, group):
            raise permissions.PermissionDenied('Вы не участник группы.')
        return Message.objects.filter(group=group).select_related('author').order_by('created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MessageCreateSerializer
        return MessageSerializer

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True, context={'request': request})
        return Response(serializer.data)

    def perform_create(self, serializer):
        group = self.get_group()
        if not is_group_member(self.request.user, group):
            raise permissions.PermissionDenied('Вы не участник группы.')
        message = serializer.save(author=self.request.user, group=group)
        broadcast_message(message)


class ChannelListCreateView(generics.ListCreateAPIView):
    serializer_class = ChannelSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Channel.objects.all().select_related('created_by')

    def perform_create(self, serializer):
        if not is_platform_admin(self.request.user):
            raise permissions.PermissionDenied('Только администраторы платформы могут создавать каналы.')
        serializer.save(created_by=self.request.user)


class ChannelDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChannelSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Channel.objects.all().select_related('created_by')

    def check_object_permissions(self, request, obj):
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            if not is_platform_admin(request.user):
                raise permissions.PermissionDenied('Только администраторы платформы могут редактировать или удалять каналы.')


class ChannelMessageListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_channel(self):
        return get_object_or_404(Channel, pk=self.kwargs['channel_id'])

    def get_queryset(self):
        channel = self.get_channel()
        return ChannelMessage.objects.filter(channel=channel).select_related('author').order_by('created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ChannelMessageCreateSerializer
        return ChannelMessageSerializer

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True, context={'request': request})
        return Response(serializer.data)

    def perform_create(self, serializer):
        channel = self.get_channel()
        message = serializer.save(author=self.request.user, channel=channel)
        broadcast_channel_message(message)
