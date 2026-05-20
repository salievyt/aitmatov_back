# 🚀 Быстрый старт - Применение обновлений мессенджера

## Шаг 1: Применить миграции

```bash
# Перейти в директорию проекта
cd /Users/m1/Desktop/айтматов/aitmatov_digital_back

# Активировать виртуальное окружение (если еще не активировано)
source .venv/bin/activate

# Применить миграции (если используется Docker)
make migrate

# Или без Docker
python manage.py migrate messenger
```

## Шаг 2: Проверить, что все работает

```bash
# Убедиться, что синтаксис правильный
python -m py_compile messenger/models.py
python -m py_compile messenger/serializers.py
python -m py_compile messenger/views.py
python -m py_compile messenger/consumers.py
```

## Шаг 3: Запустить тесты (опционально)

```bash
# Запустить все тесты мессенджера
make test
# или
python manage.py test messenger

# Запустить конкретный тест
python manage.py test messenger.tests.ChatGroupTestCase.test_create_chat_group_with_admin
```

## Шаг 4: Проверить Django Admin

1. Перейти на http://localhost:8000/admin/ (или ваш адрес)
2. Залогиниться как администратор
3. Перейти на http://localhost:8000/admin/messenger/
4. Проверить новые модели:
   - ✅ Channels (Каналы) - должны быть видны
   - ✅ Channel Messages (Сообщения канала) - должны быть видны
   - ✅ Chat Groups - должны показывать поле Admin

## Шаг 5: Проверить API

### Проверка через curl или Postman

#### 1. Создание группы (с админом)
```bash
curl -X POST http://localhost:8000/api/messenger/groups/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Тестовая группа",
    "description": "Описание группы",
    "is_private": false,
    "member_ids": [2, 3]
  }'
```

Ответ должен содержать:
```json
{
  "id": 1,
  "name": "Тестовая группа",
  "admin": {
    "id": 1,
    "username": "admin",
    "first_name": "Администратор",
    ...
  },
  "members_count": 3,
  ...
}
```

#### 2. Создание канала (как администратор)
```bash
curl -X POST http://localhost:8000/api/messenger/channels/ \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Объявления",
    "description": "Официальные объявления"
  }'
```

#### 3. Попытка создания канала (как обычный пользователь)
```bash
curl -X POST http://localhost:8000/api/messenger/channels/ \
  -H "Authorization: Bearer USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Мой канал",
    "description": "Попытка создать канал"
  }'
```

Должна вернуться ошибка 403.

#### 4. Получить список всех каналов
```bash
curl http://localhost:8000/api/messenger/channels/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Шаг 6: Проверить WebSocket

### Используя Python
```python
import websocket
import json

# Подключиться к группе
ws = websocket.WebSocketApp("ws://localhost:8000/ws/messenger/1/")

def on_message(ws, message):
    print(f"Получено: {json.loads(message)}")

def on_open(ws):
    # Отправить сообщение
    ws.send(json.dumps({
        "action": "send.message",
        "message_type": "text",
        "text": "Привет!"
    }))

ws.on_open = on_open
ws.on_message = on_message
ws.run_forever()
```

### Используя JavaScript
```javascript
// Подключиться к каналу
const ws = new WebSocket('ws://localhost:8000/ws/channel/1/');

ws.onopen = () => {
    // Отправить сообщение
    ws.send(JSON.stringify({
        action: 'send.message',
        message_type: 'text',
        text: 'Привет, канал!'
    }));
};

ws.onmessage = (event) => {
    console.log('Получено:', JSON.parse(event.data));
};
```

## Шаг 7: Обновить фронтенд

1. Скопировать примеры из `MESSENGER_FRONTEND_EXAMPLES.md`
2. Обновить компоненты для отображения:
   - `admin` поле в группе
   - `members_count` количество участников
3. Добавить компоненты для работы с каналами
4. Добавить WebSocket соединение для каналов

## Возможные проблемы и решения

### Проблема 1: "ModuleNotFoundError: No module named 'messenger'"
**Решение:** Убедиться, что `'messenger'` добавлено в `INSTALLED_APPS` в settings.py

### Проблема 2: "AttributeError: 'Channel' object has no attribute..."
**Решение:** Убедиться, что миграции были применены правильно
```bash
python manage.py migrate messenger
python manage.py showmigrations messenger
```

### Проблема 3: WebSocket не подключается
**Решение:** Убедиться, что:
1. Django Channels установлен
2. WebSocket URL правильный
3. Authenticated пользователь
4. ASGI сервер запущен (не запустить Django development сервер)

### Проблема 4: Ошибка при создании канала не-админом
**Решение:** Это ожидаемое поведение - только админы могут создавать каналы.
Для тестирования используйте админский токен.

## Важные моменты

⚠️ **ВАЖНО:**
1. Перед применением миграций в продакшене - сделайте backup БД
2. Тестируйте на staging окружении сначала
3. Убедитесь, что WebSocket маршруты добавлены в основной routing.py проекта
4. Проверьте, что CORS/CSRF настройки позволяют новым endpoints

## Быстрая проверка функциональности

```bash
# Все ошибки?
python manage.py check

# Миграции OK?
python manage.py showmigrations messenger

# Статика OK?
python manage.py collectstatic --noinput

# Django shell тест
python manage.py shell

# В shell:
>>> from messenger.models import Channel, ChatGroup
>>> Channel.objects.count()  # Должен вернуть 0 или количество
>>> ChatGroup.objects.count()  # Должен вернуть количество
>>> # Все OK!
```

## Документация для разработчиков

- 📖 **MESSENGER_API_DOCUMENTATION.md** - Полная API документация
- 💻 **MESSENGER_FRONTEND_EXAMPLES.md** - Примеры кода для фронтенда
- 🧪 **MESSENGER_TESTS.md** - Примеры тестов
- 📋 **MESSENGER_UPDATES.md** - Список изменений
- 📊 **MESSENGER_SUMMARY.md** - Общее резюме

## Контакт и поддержка

Если возникли проблемы:
1. Проверьте документацию выше
2. Запустите тесты: `python manage.py test messenger`
3. Проверьте логи Django
4. Убедитесь, что виртуальное окружение активировано

---

✅ **Готово!** Все обновления применены и готовы к использованию.
