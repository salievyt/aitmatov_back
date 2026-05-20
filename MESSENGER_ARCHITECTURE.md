# 📐 Архитектура обновленного мессенджера

## Структура моделей

```
┌─────────────────────────────────────────────────────────┐
│                         User Model                      │
│  (role: ADMIN/TEACHER/STUDENT, is_staff, ...)         │
└─────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │         │         │
                    ▼         ▼         ▼
        ┌──────────────┐ ┌────────────┐ ┌───────────────────┐
        │  ChatGroup   │ │  Channel   │ │  GroupMembership  │
        ├──────────────┤ ├────────────┤ ├───────────────────┤
        │ id           │ │ id         │ │ id                │
        │ name         │ │ name       │ │ user (FK→User)    │
        │ description  │ │ description│ │ group (FK→Group)  │
        │ is_private   │ │ created_by │ │ is_leader         │
        │ created_by   │ │ created_at │ │ joined_at         │
        │ admin        │ │ updated_at │ └───────────────────┘
        │ members (M2M)│ │            │
        │ created_at   │ │            │
        │ updated_at   │ │            │
        └──────────────┘ └────────────┘
                │              │
                │              │
        ┌───────▼────────┐    ┌───────────────────────┐
        │    Message     │    │  ChannelMessage       │
        ├────────────────┤    ├───────────────────────┤
        │ id             │    │ id                    │
        │ group (FK)     │    │ channel (FK→Channel)  │
        │ author (FK)    │    │ author (FK)           │
        │ message_type   │    │ message_type          │
        │ text           │    │ text                  │
        │ sticker_code   │    │ sticker_code          │
        │ attachment     │    │ attachment            │
        │ created_at     │    │ created_at            │
        └────────────────┘    └───────────────────────┘
```

## Иерархия представлений

```
API Endpoints
│
├── Chat Groups (Группы)
│   ├── /api/messenger/groups/
│   │   ├── GET → ChatGroupListCreateView.list()
│   │   └── POST → ChatGroupListCreateView.create()
│   │
│   ├── /api/messenger/groups/<id>/
│   │   └── GET → ChatGroupDetailView.retrieve()
│   │
│   ├── /api/messenger/groups/<id>/members/
│   │   ├── GET → GroupMembershipListCreateView.list()
│   │   └── POST → GroupMembershipListCreateView.create()
│   │
│   ├── /api/messenger/groups/<id>/assign-leader/
│   │   └── PATCH → GroupLeaderAssignView.patch()
│   │
│   └── /api/messenger/groups/<id>/messages/
│       ├── GET → MessageListCreateView.list()
│       └── POST → MessageListCreateView.create()
│
└── Channels (Каналы) ⭐ NEW
    ├── /api/messenger/channels/
    │   ├── GET → ChannelListCreateView.list() (все)
    │   └── POST → ChannelListCreateView.create() (админ)
    │
    ├── /api/messenger/channels/<id>/
    │   ├── GET → ChannelDetailView.retrieve()
    │   ├── PATCH → ChannelDetailView.update() (админ)
    │   └── DELETE → ChannelDetailView.destroy() (админ)
    │
    └── /api/messenger/channels/<id>/messages/
        ├── GET → ChannelMessageListCreateView.list()
        └── POST → ChannelMessageListCreateView.create()
```

## WebSocket соединения

```
┌──────────────────────────────────────────────────────┐
│          WebSocket Router (routing.py)               │
├──────────────────────────────────────────────────────┤
│                                                       │
│  ws/messenger/<group_id>/ → ChatConsumer            │
│  ├── connect()                                       │
│  ├── disconnect()                                    │
│  ├── receive_json()                                 │
│  ├── handle_send_message()                          │
│  ├── chat_message()                                 │
│  └── broadcast via channel_layer                    │
│                                                       │
│  ws/channel/<channel_id>/ → ChannelConsumer ⭐ NEW │
│  ├── connect()                                       │
│  ├── disconnect()                                    │
│  ├── receive_json()                                 │
│  ├── handle_send_message()                          │
│  ├── channel_message()                              │
│  └── broadcast via channel_layer                    │
│                                                       │
└──────────────────────────────────────────────────────┘
```

## Поток сообщения (Message Flow)

### Создание групповой беседы

```
Frontend                    Backend                     Database
  │                           │                           │
  ├─────POST /groups/──────────►│                           │
  │  {name, members}            │                           │
  │                             ├─validate─────────────────┤
  │                             │                           │
  │                             ├─create ChatGroup          │
  │                             │ (admin=creator)           │
  │                             ├─create GroupMemberships   │
  │                             │                           ◄─────
  │                             │ (creator as leader)       │
  │                             │                           │
  │◄────────JSON 201────────────│                           │
  │{id, name, admin, members}   │                           │
```

### Отправка сообщения в группу (WebSocket)

```
Frontend              WebSocket            Channel Layer     Database
   │                    │                      │               │
   ├─send_json─────────►│                      │               │
   │ {action, text}     │                      │               │
   │                    ├─validate─────────────┤               │
   │                    │                      │               │
   │                    ├─create Message───────────────────────┤
   │                    │                      │    saved       │
   │                    │◄──────────────────────────────────────┤
   │                    │                      │               │
   │                    ├─group_send────────►  │               │
   │                    │ {type:'chat.message'}│               │
   │                    │                      │               │
   │◄─chat_message─────────────────────────────┤               │
   │ {id, author, text} │                      │               │
```

### Создание канала (только администратор)

```
Admin                Backend              Channel Layer    Database
 │                     │                     │               │
 ├─POST /channels/────►│                     │               │
 │ {name, description} │                     │               │
 │                     ├─check is_admin      │               │
 │                     ├─create Channel      │               │
 │                     ├─validate save()─────┤               │
 │                     │ (verify admin)      │               │
 │                     │                     ├──────────────┤│
 │                     │                     │   Channel    ││
 │                     │                     │   saved      ││
 │                     │◄────────────────────────────────────┤
 │◄─JSON 201──────────│                     │               │
 │ {id, name, ...}    │                     │               │
 
 
Teacher (не администратор)
 │                     │
 ├─POST /channels/────►│
 │ {name, description} │
 │                     ├─check is_admin
 │                     ├─✗ FAIL
 │◄─403 Forbidden──────│
 │ "Только админист..."│
```

## Права доступа

```
┌─────────────────────────────────────────────────────────────┐
│                    Permission Matrix                        │
├────────────────┬──────────┬──────────┬──────────┬──────────┤
│ Action         │ Anonymous│ Student  │ Teacher  │ Admin    │
├────────────────┼──────────┼──────────┼──────────┼──────────┤
│ Read Groups    │    ✗     │    ✓     │    ✓     │    ✓     │
│ Create Group   │    ✗     │    ✓     │    ✓     │    ✓     │
│ Edit Group     │    ✗     │ Leader   │ Leader   │    ✓     │
│ Delete Group   │    ✗     │ Leader   │ Leader   │    ✓     │
│ Send Message   │    ✗     │ Member   │ Member   │ Member   │
│                │          │          │          │          │
│ Read Channels  │    ✗     │    ✓     │    ✓     │    ✓     │
│ Create Channel │    ✗     │    ✗     │    ✗     │    ✓     │
│ Edit Channel   │    ✗     │    ✗     │    ✗     │    ✓     │
│ Delete Channel │    ✗     │    ✗     │    ✗     │    ✓     │
│ Send to Channel│    ✗     │    ✓     │    ✓     │    ✓     │
└────────────────┴──────────┴──────────┴──────────┴──────────┘
```

## Сериализаторы и Валидация

```
┌────────────────────────────────────────────────────────┐
│          Serializer Hierarchy                         │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ChatGroupSerializer                                 │
│  ├── fields: [id, name, description, is_private,    │
│  │           created_by, admin, leader_id,           │
│  │           members_count, member_ids]              │
│  └── validate: member_ids must be valid users        │
│                                                        │
│  ChatGroupDetailSerializer (extends)                 │
│  └── fields: ChatGroupSerializer + [members]         │
│                                                        │
│  MessageSerializer                                    │
│  ├── fields: [id, group, author, author_id,         │
│  │           message_type, text, sticker_code,       │
│  │           attachment, attachment_url, created_at] │
│  └── validate: text/sticker_code required            │
│                                                        │
│  ChannelSerializer ⭐ NEW                            │
│  ├── fields: [id, name, description, created_by,    │
│  │           created_at, updated_at]                 │
│  └── validate: user must be admin                    │
│                                                        │
│  ChannelMessageSerializer ⭐ NEW                     │
│  ├── fields: [id, channel, author, author_id,       │
│  │           message_type, text, sticker_code,       │
│  │           attachment, attachment_url, created_at] │
│  └── validate: text/sticker_code required            │
│                                                        │
│  AssignLeaderSerializer (FIXED)                      │
│  └── validate: user_id must exist                    │
│                                                        │
└────────────────────────────────────────────────────────┘
```

## Типы сообщений

```
Message Type = Choice(
    'text'  → requires: text field (not empty)
    'sticker' → requires: sticker_code field (not empty)
    'voice' → requires: attachment field (audio file)
    'video' → requires: attachment field (video file)
)
```

## Файловая структура проекта

```
messenger/
├── migrations/
│   ├── 0001_initial.py
│   ├── 0002_channel_chatgroup_admin_chatgroup_members_and_more.py ⭐ NEW
│   └── __init__.py
├── __init__.py
├── admin.py (ОБНОВЛЕН)
│   ├── ChatGroupAdmin
│   ├── GroupMembershipAdmin
│   ├── MessageAdmin
│   ├── ChannelAdmin ⭐ NEW
│   └── ChannelMessageAdmin ⭐ NEW
├── apps.py
├── consumers.py (ОБНОВЛЕН)
│   ├── ChatConsumer
│   └── ChannelConsumer ⭐ NEW
├── models.py (ОБНОВЛЕН)
│   ├── ChatGroup (добавлено admin)
│   ├── GroupMembership
│   ├── Message
│   ├── Channel ⭐ NEW
│   └── ChannelMessage ⭐ NEW
├── routing.py (ОБНОВЛЕН)
│   ├── ChatConsumer path
│   └── ChannelConsumer path ⭐ NEW
├── serializers.py (ОБНОВЛЕН)
│   ├── ChatGroupSerializer (добавлено admin)
│   ├── ChatGroupDetailSerializer
│   ├── MessageSerializer
│   ├── MessageCreateSerializer
│   ├── AssignLeaderSerializer ⭐ FIXED
│   ├── ChannelSerializer ⭐ NEW
│   ├── ChannelMessageSerializer ⭐ NEW
│   └── ChannelMessageCreateSerializer ⭐ NEW
├── urls.py (ОБНОВЛЕН)
│   ├── Group endpoints
│   └── Channel endpoints ⭐ NEW
├── views.py (ОБНОВЛЕН)
│   ├── ChatGroupListCreateView
│   ├── ChatGroupDetailView
│   ├── GroupMembershipListCreateView
│   ├── GroupLeaderAssignView
│   ├── MessageListCreateView
│   ├── ChannelListCreateView ⭐ NEW
│   ├── ChannelDetailView ⭐ NEW
│   └── ChannelMessageListCreateView ⭐ NEW
└── tests.py (примеры в документации)
```

## Интеграция с основным проектом

```
Project Root
├── manage.py
├── requirements.txt
├── aitmatov_digital_back/
│   ├── settings.py
│   │   └── INSTALLED_APPS
│   │       └── 'messenger' ✓
│   ├── urls.py
│   │   └── path('api/messenger/', include('messenger.urls'))
│   ├── asgi.py
│   │   └── WebSocket routing include
│   └── wsgi.py
├── messenger/ ← Обновленное приложение
│   └── (структура выше)
└── ... (другие приложения)
```

## Развертывание

```
Development                Production
─────────────────         ──────────────
Python runserver          Gunicorn/uWSGI
─────────────────         ──────────────
Django Channels           Daphne
─────────────────         ──────────────
Redis (optional)          Redis
─────────────────         ──────────────
SQLite/PostgreSQL         PostgreSQL
─────────────────         ──────────────

Оба требуют:
✓ Миграции: python manage.py migrate messenger
✓ WebSocket поддержка в ASGI
✓ Channel Layer конфигурация
```

---

**Готовая система полностью интегрирована и готова к использованию!**
