# WebSocket Backend Архитектура

## Обзор

Проект использует **Django Channels** для реализации WebSocket функциональности, обеспечивая двустороннюю реальную коммуникацию между клиентами и сервером.

## Технологический Стек

| Компонент | Технология | Назначение |
|-----------|------------|------------|
| ASGI Server | **Daphne** | ASGI-совместимый сервер для обработки WebSocket |
| Фреймворк | **Django Channels** | Интеграция WebSocket с Django |
| Channel Layer | **Redis** | Бэкенд для межпроцессной коммуникации и групп |
| Аутентификация | **JWT** | Авторизация WebSocket подключений |



### 1. ASGI Configuration (`aitmatov_digital/asgi.py`)

```python
application = ProtocolTypeRouter({
    'http': get_asgi_application(),        # Обычные HTTP запросы
    'websocket': AuthMiddlewareStack(      # WebSocket с auth
        URLRouter(
            messenger.routing.websocket_urlpatterns,
        )
    ),
})
```

**Поток обработки:**
1. Daphne получает входящее WebSocket подключение
2. `AuthMiddlewareStack` извлекает JWT токен и аутентифицирует пользователя
3. `URLRouter` направляет подключение к соответствующему Consumer

### 2. WebSocket Routing (`messenger/routing.py`)

```python
websocket_urlpatterns = [
    path('ws/messenger/<int:group_id>/', ChatConsumer.as_asgi()),
    path('ws/messenger/channels/<int:channel_id>/', ChannelConsumer.as_asgi()),
    path('ws/channel/<int:channel_id>/', ChannelConsumer.as_asgi()),
]
```

**Маршруты:**
| Путь | Consumer | Описание |
|------|----------|----------|
| `ws/messenger/<group_id>/` | `ChatConsumer` | Групповые чаты |
| `ws/messenger/channels/<channel_id>/` | `ChannelConsumer` | Каналы объявлений |
| `ws/channel/<channel_id>/` | `ChannelConsumer` | Альтернативный путь к каналам |

### 3. Consumers (`messenger/consumers.py`)

#### BaseMessageConsumer

Базовый класс для обработки общих сообщений:

```python
class BaseMessageConsumer(AsyncJsonWebsocketConsumer):
    
    async def receive_json(self, content):
        action = content.get('action')
        if action == 'history':
            await self.handle_history(content)
        elif action == 'send.message':
            await self.handle_send_message(content)
        elif action == 'ping':
            await self.send_json({'type': 'pong'})
```

**Поддерживаемые действия:**
- `history` — получение истории сообщений
- `send.message` — отправка нового сообщения
- `ping` — проверка соединения (сервер отвечает `pong`)

#### ChatConsumer

Обработка групповых чатов:

```python
class ChatConsumer(BaseMessageConsumer):
    
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.user = self.scope['user']
        
        # Проверка аутентификации
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Проверка членства в группе
        self.group = await self.get_group(self.group_id)
        if not self.group or not await self.is_group_member():
            await self.close()
            return
        
        # Добавление в группу каналов Redis
        self.room_group_name = f'chat_group_{self.group_id}'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
```

**Жизненный цикл:**
1. `connect()` — проверка прав, добавление в группу
2. `receive_json()` — обработка входящих сообщений
3. `disconnect()` — удаление из группы

#### ChannelConsumer

Аналогичен `ChatConsumer`, но для каналов:

```python
class ChannelConsumer(BaseMessageConsumer):
    
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
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
```

## Channel Layer и Redis

### Конфигурация (`settings.py`)

```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [
                (os.getenv('REDIS_HOST', 'redis'), 6379),
            ],
        },
    },
}
```

### Групповая Коммуникация

**Ключи групп в Redis:**
- `chat_group_{group_id}` — группа для чата
- `chat_channel_{channel_id}` — группа для канала

**Принцип работы:**
1. При подключении клиент добавляется в группу через `group_add()`
2. При отправке сообщения используется `group_send()` для рассылки всем участникам
3. При отключении клиент удаляется из группы через `group_discard()`

## Сообщение Потока

### Отправка Сообщения

```
Client                                  Backend
  │                                       │
  ├────── send.message ─────────────────► │
  │  {action, text, message_type}         │
  │                                       │
  │                    1. Валидация       │
  │                    2. Сохранение в DB │
  │                    3. Serializing     │
  │                                       │
  │        group_send() ─────────► Redis  │
  │                    │                  │
  │                    ▼                  │
  │              broadcast_message()      │
  │                    │                  │
  ◄───── message ──────┤                  │
  │  {type, data}      │                  │
```

**Код обработки:**

```python
async def handle_send_message(self, content):
    # 1. Валидация
    validation_error = self.validate_message_payload(
        message_type=message_type,
        text=text,
        sticker_code=sticker_code,
    )
    if validation_error:
        await self.send_error(validation_error)
        return
    
    # 2. Создание сообщения в БД
    message = await self.create_message(
        message_type=message_type,
        text=text,
        sticker_code=sticker_code,
    )
    
    # 3. Сериализация
    payload = await self.serialize_message(message)
    
    # 4. Рассылка всем подключенным клиентам в группе
    await self.channel_layer.group_send(
        self.room_group_name,
        {
            'type': self.broadcast_event_type,  # 'broadcast_message'
            'message': payload,
        },
    )

async def broadcast_message(self, event):
    await self.send_json({
        'type': 'message',
        'data': event['message'],
    })
```

### Получение Истории

```python
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
```

**Параметры:**
- `limit` — количество сообщений (1-100, по умолчанию 50)
- `before_id` — ID сообщения, перед которым начать выборку (пагинация)

## Аутентификация

WebSocket подключения используют JWT токен из заголовка:

```
ws://localhost:8000/ws/messenger/1/
Headers:
  Authorization: Bearer <jwt_token>
```

**Поток аутентификации:**
1. `AuthMiddlewareStack` извлекает токен из заголовка
2. JWT токен валидируется (проверка подписи, expiration)
3. `scope['user']` устанавливается на аутентифицированного пользователя
4. В `connect()` проверяется `self.user.is_authenticated`

## Синхронизация с Базой Данных

Django Channels работает асинхронно, но ORM Django синхронная. Используются обёртки:

```python
@database_sync_to_async
def get_group(self, group_id):
    try:
        return ChatGroup.objects.get(pk=group_id)
    except ChatGroup.DoesNotExist:
        return None

@database_sync_to_async
def create_message(self, message_type, text, sticker_code):
    return Message.objects.create(
        group=self.group,
        author=self.user,
        message_type=message_type,
        text=text,
        sticker_code=sticker_code,
    )
```

**Преимущества:**
- Не блокирует event loop
- Позволяет использовать Django ORM в асинхронном коде

## Типы Сообщений

### От Клиента (WebSocket)

| Тип | Формат | Описание |
|-----|--------|----------|
| `send.message` | `{"action": "send.message", "text": "...", "message_type": "text"}` | Отправка текста |
| `send.message` | `{"action": "send.message", "sticker_code": "...", "message_type": "sticker"}` | Отправка стикера |
| `history` | `{"action": "history", "limit": 50, "before_id": 123}` | Получение истории |
| `ping` | `{"action": "ping"}` | Проверка соединения |

### От Клиента (HTTP POST)

**Отправить сообщение через HTTP (альтернатива WebSocket):**

```bash
POST /api/messenger/groups/<group_id>/messages/
Authorization: Bearer <token>
Content-Type: application/json

{
    "message_type": "text",
    "text": "Привет!"
}
```

**Ответ:**
```json
{
    "id": 42,
    "group": 5,
    "author": {...},
    "message_type": "text",
    "text": "Привет!",
    "created_at": "2024-01-15T10:30:00Z"
}
```

### От Сервера

| Тип | Формат | Описание |
|-----|--------|----------|
| `connected` | `{"type": "connected", "room": "group", "group_id": 1}` | Успешное подключение |
| `message` | `{"type": "message", "data": {...}}` | Новое сообщение |
| `history` | `{"type": "history", "items": [...], "limit": 50}` | История сообщений |
| `error` | `{"type": "error", "error": "description"}` | Ошибка |
| `pong` | `{"type": "pong"}` | Ответ на ping |

## Типы Сообщений (Content Types)

```python
# Из модели Message
class Message(models.Model):
    class MessageType(models.TextChoices):
        TEXT = 'text', 'Текст'
        STICKER = 'sticker', 'Стикер'
        VOICE = 'voice', 'Голосовое'
        VIDEO = 'video', 'Видео'
```

**Валидация:**
```python
def validate_message_payload(self, message_type, text, sticker_code):
    if message_type == 'text' and not text:
        return 'Text message cannot be empty.'
    if message_type == 'sticker' and not sticker_code:
        return 'Sticker code is required.'
    if message_type in ['voice', 'video']:
        return 'Voice/video require HTTP upload flow.'
    return None
```

## Масштабирование

### Множество Серверов

Redis Channel Layer позволяет масштабировать на несколько инстансов:

```
Client ──► Daphne #1 ──┐
                        ├─► Redis ──┐
Client ──► Daphne #2 ──┘            │
                                    ▼
                            Client получает сообщение
                            от любого сервера
```

**Ключевые моменты:**
- Все серверы подключены к одному Redis
- Сообщения транслируются всем подключенным клиентам, независимо от сервера
- Redis управляет очередями и доставкой

### Production Deployment

```dockerfile
# Dockerfile
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "aitmatov_digital.asgi:application"]
```

**docker-compose:**
```yaml
services:
  backend:
    command: daphne -b 0.0.0.0 -p 8000 aitmatov_digital.asgi:application
  
  redis:
    image: redis:alpine
```

## Обработка Ошибок

```python
async def send_error(self, error_message):
    await self.send_json({
        'type': 'error',
        'error': error_message,
    })

async def connect(self):
    if not self.user.is_authenticated:
        await self.close()  # Закрыть без объяснения (безопасность)
    if not await self.is_group_member():
        await self.close()  # Закрыть без объяснения
```

**Правила:**
- Аутентификационные ошибки — просто закрыть соединение
- Валидационные ошибки — отправить `error` сообщение с описанием

## Примеры Использования

### Подключение с Клиента

```javascript
const token = 'YOUR_JWT_TOKEN';
const ws = new WebSocket(
    `ws://localhost:8000/ws/messenger/1/?token=${token}`
);

ws.onopen = () => {
    console.log('Connected to WebSocket');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'message') {
        console.log('New message:', data.data);
    } else if (data.type === 'history') {
        console.log('History loaded:', data.items);
    } else if (data.type === 'error') {
        console.error('Error:', data.error);
    }
};

// Отправка сообщения
ws.send(JSON.stringify({
    action: 'send.message',
    text: 'Привет, группа!',
    message_type: 'text'
}));

// Получение истории
ws.send(JSON.stringify({
    action: 'history',
    limit: 50,
    before_id: null
}));
```

## Мониторинг и Логирование

```python
import logging

logger = logging.getLogger(__name__)

async def connect(self):
    logger.info(f'User {self.user.id} connecting to group {self.group_id}')
    # ...
    
async def disconnect(self, code):
    logger.info(f'User {self.user.id} disconnected with code {code}')
```

## Best Practices

1. **Всегда проверяйте аутентификацию** в `connect()`
2. **Проверяйте права доступа** перед добавлением в группу
3. **Используйте `@database_sync_to_async`** для всех DB операций
4. **Ограничивайте историю** (максимум 100 сообщений)
5. **Обрабатывайте disconnect** для очистки групп
6. **Используйте Redis** для production (не memory backend)
7. **Валидируйте payload** перед созданием сообщений
8. **Логгируйте** критические события (подключение, отключение, ошибки)

## Troubleshooting

### WebSocket не подключается

**Проверки:**
1. JWT токен валиден?
2. Пользователь аутентифицирован?
3. Пользователь является участником группы/канала?
4. Redis доступен?
5. Правильный ли WebSocket путь?

### Сообщения не доставляются

**Проверки:**
1. Клиент добавлен в правильную группу?
2. `group_send()` использует правильное имя группы?
3. Все серверы подключены к одному Redis?
4. Клиент не отключился?

### Высокая нагрузка

**Оптимизации:**
1. Увеличить лимит истории (но не более 100)
2. Использовать pagination для истории
3. Масштабировать Daphne инстансы
4. Настроить Redis timeout и maxmemory
