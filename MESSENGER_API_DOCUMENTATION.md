# Документация API Мессенджера

## Обновления и исправления

### Исправленные баги:
1. **Добавлен недостающий сериализатор `AssignLeaderSerializer`** - был использован в views, но отсутствовал в serializers.py
2. **Исправлена инициализация админа группы** - при создании группы, создатель автоматически назначается администратором

### Новые функции:

#### 1. Параметры группы

**Количество участников** - уже реализовано:
- Поле `members_count` - количество участников в группе (доступно через API)

**Администратор группы** - новое поле:
- Поле `admin` - администратор группы (отличается от лидера группы)
- При создании группы создатель автоматически назначается админом
- Возвращается в ответе API в формате объекта пользователя

#### 2. Каналы

Новая модель **Channel** с функциональностью:
- **Создание каналов** - только администраторы платформы (role='admin' или is_staff=True)
- **Модель ChannelMessage** - сообщения в канале
- **WebSocket поддержка** - ChannelConsumer для real-time общения в каналах

### API Endpoints

#### Чат-группы (существующие):
```
GET    /api/messenger/groups/                          - Список групп пользователя
POST   /api/messenger/groups/                          - Создать группу
GET    /api/messenger/groups/<id>/                     - Детали группы
GET    /api/messenger/groups/<id>/members/             - Члены группы
POST   /api/messenger/groups/<id>/members/             - Добавить члена
PATCH  /api/messenger/groups/<id>/assign-leader/       - Назначить лидера
GET    /api/messenger/groups/<id>/messages/            - Сообщения группы
POST   /api/messenger/groups/<id>/messages/            - Отправить сообщение
```

#### Каналы (новые):
```
GET    /api/messenger/channels/                        - Список всех каналов
POST   /api/messenger/channels/                        - Создать канал (только админ)
GET    /api/messenger/channels/<id>/                   - Детали канала
PATCH  /api/messenger/channels/<id>/                   - Редактировать канал (только админ)
DELETE /api/messenger/channels/<id>/                   - Удалить канал (только админ)
GET    /api/messenger/channels/<id>/messages/          - Сообщения канала
POST   /api/messenger/channels/<id>/messages/          - Отправить сообщение
```

### Примеры запросов

#### Создание группы с админом
```bash
POST /api/messenger/groups/
{
    "name": "Класс 10-А",
    "description": "Чат класса 10-А",
    "is_private": true,
    "member_ids": [2, 3, 4]  # ID членов группы
}

Ответ:
{
    "id": 1,
    "name": "Класс 10-А",
    "description": "Чат класса 10-А",
    "is_private": true,
    "created_by": { "id": 1, "username": "teacher1", ... },
    "admin": { "id": 1, "username": "teacher1", ... },  # ← Новое поле
    "leader_id": 1,
    "members_count": 4,  # ← Количество участников
    "created_at": "2026-05-20T10:00:00Z",
    "updated_at": "2026-05-20T10:00:00Z"
}
```

#### Создание канала (только администратор платформы)
```bash
POST /api/messenger/channels/
Authorization: Bearer <token_админа>
{
    "name": "Объявления",
    "description": "Официальные объявления школы"
}

Ответ (если пользователь не админ):
{
    "detail": "Только администраторы платформы могут создавать каналы."
}

Ответ (если пользователь админ):
{
    "id": 1,
    "name": "Объявления",
    "description": "Официальные объявления школы",
    "created_by": { "id": 1, "username": "admin", ... },
    "created_at": "2026-05-20T10:00:00Z",
    "updated_at": "2026-05-20T10:00:00Z"
}
```

#### Получение списка каналов
```bash
GET /api/messenger/channels/

Ответ:
[
    {
        "id": 1,
        "name": "Объявления",
        "description": "Официальные объявления школы",
        "created_by": { "id": 1, "username": "admin", ... },
        "created_at": "2026-05-20T10:00:00Z",
        "updated_at": "2026-05-20T10:00:00Z"
    },
    ...
]
```

### WebSocket соединения

#### Групповой чат
```
URL: ws://domain/ws/messenger/<group_id>/

Отправка сообщения:
{
    "action": "send.message",
    "message_type": "text",
    "text": "Привет, все!"
}

Получение сообщения:
{
    "id": 1,
    "group": 1,
    "author": { "id": 2, "username": "student1", ... },
    "author_id": 2,
    "message_type": "text",
    "text": "Привет, все!",
    "sticker_code": "",
    "attachment": null,
    "attachment_url": null,
    "created_at": "2026-05-20T10:00:00Z"
}
```

#### Канал
```
URL: ws://domain/ws/channel/<channel_id>/

Отправка сообщения:
{
    "action": "send.message",
    "message_type": "text",
    "text": "Важное объявление!"
}

Получение сообщения:
{
    "id": 1,
    "channel": 1,
    "author": { "id": 1, "username": "admin", ... },
    "author_id": 1,
    "message_type": "text",
    "text": "Важное объявление!",
    "sticker_code": "",
    "attachment": null,
    "attachment_url": null,
    "created_at": "2026-05-20T10:00:00Z"
}
```

### Типы сообщений
- `text` - текстовое сообщение (требует поле `text`)
- `sticker` - стикер (требует поле `sticker_code`)
- `voice` - голосовое сообщение (требует `attachment`)
- `video` - видео сообщение (требует `attachment`)

### Ограничения по правам

**Группа:**
- Создать: любой авторизованный пользователь (становится админом)
- Добавить члена: лидер группы или администратор платформы
- Назначить лидера: лидер группы или администратор платформы

**Канал:**
- Создать: только администратор платформы
- Редактировать: только администратор платформы
- Удалить: только администратор платформы
- Читать/Писать: все авторизованные пользователи

### Миграции

Новая миграция добавлена: `messenger/migrations/0002_channel_chatgroup_admin_chatgroup_members_and_more.py`

Для применения:
```bash
make migrate
# или
python manage.py migrate
```

### Изменения в моделях

#### ChatGroup
- **Новое поле `admin`** - FK на User, администратор группы

#### Новая модель Channel
- `name` - уникальное имя канала
- `description` - описание канала
- `created_by` - создатель (только администратор платформы)
- `created_at`, `updated_at` - временные метки

#### Новая модель ChannelMessage
- `channel` - FK на Channel
- `author` - автор сообщения
- `message_type` - тип сообщения (text, sticker, voice, video)
- `text`, `sticker_code`, `attachment` - содержимое сообщения
- `created_at` - время создания
