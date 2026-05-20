# Тесты мессенджера

Создать файл `messenger/tests.py` со следующим содержимым:

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import ChatGroup, GroupMembership, Channel, Message, ChannelMessage

User = get_user_model()


class ChatGroupTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Создать пользователей
        self.teacher = User.objects.create_user(
            email='teacher@test.com',
            first_name='Иван',
            last_name='Иванов',
            password='password123',
            role=User.Role.TEACHER
        )
        
        self.student1 = User.objects.create_user(
            email='student1@test.com',
            first_name='Петр',
            last_name='Петров',
            password='password123',
            role=User.Role.STUDENT
        )
        
        self.student2 = User.objects.create_user(
            email='student2@test.com',
            first_name='Сергей',
            last_name='Сергеев',
            password='password123',
            role=User.Role.STUDENT
        )
        
        self.admin = User.objects.create_user(
            email='admin@test.com',
            first_name='Администратор',
            last_name='Системы',
            password='password123',
            role=User.Role.ADMIN
        )
    
    def test_create_chat_group_with_admin(self):
        """Тест: при создании группы создатель становится админом"""
        self.client.force_authenticate(user=self.teacher)
        
        response = self.client.post('/api/messenger/groups/', {
            'name': 'Класс 10-А',
            'description': 'Чат класса 10-А',
            'is_private': False,
            'member_ids': [self.student1.id, self.student2.id]
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Проверить, что админ установлен
        group = ChatGroup.objects.get(id=response.data['id'])
        self.assertEqual(group.admin_id, self.teacher.id)
        self.assertEqual(group.members_count, 3)  # teacher + 2 students
        
        # Проверить в ответе API
        self.assertEqual(response.data['admin']['id'], self.teacher.id)
        self.assertEqual(response.data['members_count'], 3)
    
    def test_get_group_members_count(self):
        """Тест: получение количества участников группы"""
        group = ChatGroup.objects.create(
            name='Тестовая группа',
            created_by=self.teacher,
            admin=self.teacher
        )
        GroupMembership.objects.create(group=group, user=self.teacher, is_leader=True)
        GroupMembership.objects.create(group=group, user=self.student1)
        GroupMembership.objects.create(group=group, user=self.student2)
        
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(f'/api/messenger/groups/{group.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['members_count'], 3)
    
    def test_assign_group_leader(self):
        """Тест: назначение лидера группы"""
        group = ChatGroup.objects.create(
            name='Тестовая группа',
            created_by=self.teacher,
            admin=self.teacher
        )
        GroupMembership.objects.create(group=group, user=self.teacher, is_leader=True)
        GroupMembership.objects.create(group=group, user=self.student1)
        
        self.client.force_authenticate(user=self.teacher)
        response = self.client.patch(
            f'/api/messenger/groups/{group.id}/assign-leader/',
            {'user_id': self.student1.id}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_leader'])
        
        # Проверить БД
        self.assertTrue(
            GroupMembership.objects.get(group=group, user=self.student1).is_leader
        )
        self.assertFalse(
            GroupMembership.objects.get(group=group, user=self.teacher).is_leader
        )


class ChannelTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.admin = User.objects.create_user(
            email='admin@test.com',
            first_name='Администратор',
            last_name='Системы',
            password='password123',
            role=User.Role.ADMIN
        )
        
        self.teacher = User.objects.create_user(
            email='teacher@test.com',
            first_name='Иван',
            last_name='Иванов',
            password='password123',
            role=User.Role.TEACHER
        )
        
        self.student = User.objects.create_user(
            email='student@test.com',
            first_name='Петр',
            last_name='Петров',
            password='password123',
            role=User.Role.STUDENT
        )
    
    def test_create_channel_as_admin(self):
        """Тест: администратор может создавать каналы"""
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.post('/api/messenger/channels/', {
            'name': 'Объявления',
            'description': 'Официальные объявления'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Объявления')
        self.assertEqual(response.data['created_by']['id'], self.admin.id)
    
    def test_create_channel_as_teacher_fails(self):
        """Тест: учитель не может создавать каналы"""
        self.client.force_authenticate(user=self.teacher)
        
        response = self.client.post('/api/messenger/channels/', {
            'name': 'Мой канал',
            'description': 'Персональный канал'
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('администраторы платформы', str(response.data['detail']).lower())
    
    def test_create_channel_as_student_fails(self):
        """Тест: студент не может создавать каналы"""
        self.client.force_authenticate(user=self.student)
        
        response = self.client.post('/api/messenger/channels/', {
            'name': 'Мой канал',
            'description': 'Персональный канал'
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_all_channels(self):
        """Тест: все пользователи могут видеть каналы"""
        Channel.objects.create(
            name='Канал 1',
            description='Описание 1',
            created_by=self.admin
        )
        Channel.objects.create(
            name='Канал 2',
            description='Описание 2',
            created_by=self.admin
        )
        
        self.client.force_authenticate(user=self.student)
        response = self.client.get('/api/messenger/channels/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_delete_channel_as_admin(self):
        """Тест: администратор может удалять каналы"""
        channel = Channel.objects.create(
            name='Тестовый канал',
            created_by=self.admin
        )
        
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f'/api/messenger/channels/{channel.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Channel.objects.filter(id=channel.id).exists())
    
    def test_delete_channel_as_teacher_fails(self):
        """Тест: учитель не может удалять каналы"""
        channel = Channel.objects.create(
            name='Тестовый канал',
            created_by=self.admin
        )
        
        self.client.force_authenticate(user=self.teacher)
        response = self.client.delete(f'/api/messenger/channels/{channel.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ChannelMessageTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.admin = User.objects.create_user(
            email='admin@test.com',
            first_name='Администратор',
            last_name='Системы',
            password='password123',
            role=User.Role.ADMIN
        )
        
        self.student = User.objects.create_user(
            email='student@test.com',
            first_name='Петр',
            last_name='Петров',
            password='password123',
            role=User.Role.STUDENT
        )
        
        self.channel = Channel.objects.create(
            name='Тестовый канал',
            created_by=self.admin
        )
    
    def test_post_message_to_channel(self):
        """Тест: отправка сообщения в канал"""
        self.client.force_authenticate(user=self.student)
        
        response = self.client.post(
            f'/api/messenger/channels/{self.channel.id}/messages/',
            {
                'message_type': 'text',
                'text': 'Привет, канал!'
            }
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['text'], 'Привет, канал!')
        self.assertEqual(response.data['author']['id'], self.student.id)
    
    def test_get_channel_messages(self):
        """Тест: получение сообщений канала"""
        ChannelMessage.objects.create(
            channel=self.channel,
            author=self.admin,
            message_type='text',
            text='Сообщение 1'
        )
        ChannelMessage.objects.create(
            channel=self.channel,
            author=self.student,
            message_type='text',
            text='Сообщение 2'
        )
        
        self.client.force_authenticate(user=self.student)
        response = self.client.get(f'/api/messenger/channels/{self.channel.id}/messages/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


class GroupMembershipTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.teacher = User.objects.create_user(
            email='teacher@test.com',
            first_name='Иван',
            last_name='Иванов',
            password='password123',
            role=User.Role.TEACHER
        )
        
        self.student1 = User.objects.create_user(
            email='student1@test.com',
            first_name='Петр',
            last_name='Петров',
            password='password123',
            role=User.Role.STUDENT
        )
        
        self.student2 = User.objects.create_user(
            email='student2@test.com',
            first_name='Сергей',
            last_name='Сергеев',
            password='password123',
            role=User.Role.STUDENT
        )
        
        self.group = ChatGroup.objects.create(
            name='Тестовая группа',
            created_by=self.teacher,
            admin=self.teacher
        )
        GroupMembership.objects.create(
            group=self.group,
            user=self.teacher,
            is_leader=True
        )
    
    def test_add_member_to_group(self):
        """Тест: добавление члена в группу"""
        self.client.force_authenticate(user=self.teacher)
        
        response = self.client.post(
            f'/api/messenger/groups/{self.group.id}/members/',
            {'user_id': self.student1.id}
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Проверить БД
        self.assertTrue(
            GroupMembership.objects.filter(
                group=self.group,
                user=self.student1
            ).exists()
        )
    
    def test_non_leader_cannot_add_member(self):
        """Тест: не-лидер не может добавлять членов"""
        # Добавить студента в группу
        GroupMembership.objects.create(group=self.group, user=self.student1)
        
        self.client.force_authenticate(user=self.student1)
        
        response = self.client.post(
            f'/api/messenger/groups/{self.group.id}/members/',
            {'user_id': self.student2.id}
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
```

## Запуск тестов

```bash
# Запустить все тесты мессенджера
python manage.py test messenger

# Запустить конкретный класс тестов
python manage.py test messenger.tests.ChatGroupTestCase

# Запустить конкретный тест
python manage.py test messenger.tests.ChatGroupTestCase.test_create_chat_group_with_admin

# Запустить с verbose output
python manage.py test messenger -v 2

# Запустить с покрытием кода (если установлен coverage)
coverage run --source='.' manage.py test messenger
coverage report
```

## Проверяемые функции

✅ **ChatGroup:**
- Создание группы с автоматической инициализацией админа
- Количество участников
- Назначение лидера группы
- Добавление членов

✅ **Channel:**
- Создание канала только администраторами
- Запрет создания для учителей и студентов
- Получение списка каналов для всех пользователей
- Удаление канала администратором

✅ **ChannelMessage:**
- Отправка сообщений в канал
- Получение истории сообщений

✅ **Права доступа:**
- Лидер может управлять группой
- Администратор может управлять каналами
- Обычные пользователи могут читать и писать
