# Инструкция по обновлению мессенджера

## Краткое описание обновлений

✅ **Исправлены баги:**
- Добавлен недостающий `AssignLeaderSerializer` в serializers.py
- Исправлена инициализация админа группы при создании

✨ **Новые функции:**
1. **Администратор группы** - поле `admin` в ChatGroup
2. **Количество участников** - поле `members_count` (уже было, но теперь явно задокументировано)
3. **Каналы** - новые модели Channel и ChannelMessage
4. **Ограничение по правам** - каналы могут создавать только администраторы платформы

## Шаги для применения

### 1. Применить миграции

```bash
# Используя make
make migrate

# Или напрямую
python manage.py migrate messenger
```

### 2. Проверить Django Admin

Перейти на `/admin/messenger/` и проверить новые модели:
- Channel (каналы)
- ChannelMessage (сообщения в канале)
- ChatGroup теперь показывает поле admin

### 3. Тестировать API

#### Тест создания группы с админом
```bash
POST /api/messenger/groups/
{
    "name": "Тестовая группа",
    "description": "Описание",
    "is_private": false,
    "member_ids": [2, 3]
}
```

Ответ должен содержать:
```json
{
    "id": 1,
    "name": "Тестовая группа",
    "admin": { "id": <ваш_id>, ... },
    "members_count": 3,
    ...
}
```

#### Тест создания канала (как админ)
```bash
POST /api/messenger/channels/
Authorization: Bearer <токен_админа>
{
    "name": "Канал объявлений",
    "description": "Для объявлений"
}
```

#### Тест создания канала (как обычный пользователь)
```bash
POST /api/messenger/channels/
Authorization: Bearer <токен_студента>
{
    "name": "Мой канал",
    "description": "Мой персональный канал"
}
```
Должна вернуться ошибка: "Только администраторы платформы могут создавать каналы."

## Структура изменений

### Файлы которые были изменены:
- `messenger/models.py` - добавлены Channel, ChannelMessage; поле admin в ChatGroup
- `messenger/serializers.py` - добавлены новые сериализаторы и исправлена ошибка
- `messenger/views.py` - добавлены новые view классы
- `messenger/urls.py` - добавлены новые URL маршруты
- `messenger/consumers.py` - добавлен ChannelConsumer для WebSocket
- `messenger/routing.py` - добавлен маршрут для ChannelConsumer
- `messenger/admin.py` - добавлены новые модели в админ-панель

### Новые файлы:
- `messenger/migrations/0002_channel_chatgroup_admin_chatgroup_members_and_more.py` - миграция

## Документация

Полная документация доступна в файле: `MESSENGER_API_DOCUMENTATION.md`

## Проверка кода

Все файлы проверены на синтаксические ошибки - ошибок не найдено ✓
