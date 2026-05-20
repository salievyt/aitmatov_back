# Примеры использования API мессенджера (для фронтенда)

## JavaScript/TypeScript примеры

### 1. Создание групповой беседы

```javascript
// Создание новой группы
async function createChatGroup(name, description, memberIds) {
    const response = await fetch('/api/messenger/groups/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            name: name,
            description: description,
            is_private: false,
            member_ids: memberIds
        })
    });
    
    const group = await response.json();
    console.log(`Группа создана. Админ: ${group.admin.username}, участников: ${group.members_count}`);
    return group;
}

// Пример использования
createChatGroup('Класс 10-А', 'Чат класса 10-А', [2, 3, 4]);
```

### 2. Получение данных о группе (с админом и количеством участников)

```javascript
// Получить детали группы
async function getChatGroupDetails(groupId) {
    const response = await fetch(`/api/messenger/groups/${groupId}/`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    const group = await response.json();
    
    console.log(`Группа: ${group.name}`);
    console.log(`Администратор: ${group.admin.first_name} ${group.admin.last_name}`);
    console.log(`Количество участников: ${group.members_count}`);
    console.log(`Лидер: ${group.leader_id}`);
    
    return group;
}
```

### 3. Работа с каналами (только для администраторов)

```javascript
// Создание канала (только для админов)
async function createChannel(name, description) {
    const response = await fetch('/api/messenger/channels/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${adminToken}`
        },
        body: JSON.stringify({
            name: name,
            description: description
        })
    });
    
    if (!response.ok) {
        const error = await response.json();
        console.error('Ошибка:', error.detail);
        return null;
    }
    
    const channel = await response.json();
    console.log(`Канал "${channel.name}" создан администратором ${channel.created_by.username}`);
    return channel;
}

// Получить список всех каналов (для всех пользователей)
async function getAllChannels() {
    const response = await fetch('/api/messenger/channels/', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    const channels = await response.json();
    channels.forEach(ch => {
        console.log(`${ch.name} (${ch.description})`);
    });
    return channels;
}

// Удалить канал (только для админов)
async function deleteChannel(channelId) {
    const response = await fetch(`/api/messenger/channels/${channelId}/`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${adminToken}`
        }
    });
    
    if (response.ok) {
        console.log('Канал удален');
    }
}
```

### 4. Отправка сообщений в группе (WebSocket)

```javascript
class ChatGroupClient {
    constructor(groupId, token) {
        this.groupId = groupId;
        this.token = token;
        this.ws = null;
    }
    
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.ws = new WebSocket(
            `${protocol}//${window.location.host}/ws/messenger/${this.groupId}/`
        );
        
        this.ws.onopen = () => {
            console.log('Подключено к группе');
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket ошибка:', error);
        };
    }
    
    sendMessage(text) {
        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                action: 'send.message',
                message_type: 'text',
                text: text
            }));
        }
    }
    
    sendSticker(stickerCode) {
        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                action: 'send.message',
                message_type: 'sticker',
                sticker_code: stickerCode
            }));
        }
    }
    
    handleMessage(message) {
        console.log(`${message.author.first_name}: ${message.text}`);
        // Обновить UI
        this.displayMessage(message);
    }
    
    displayMessage(message) {
        const msgElement = document.createElement('div');
        msgElement.innerHTML = `
            <strong>${message.author.first_name} ${message.author.last_name}</strong>
            <p>${message.text}</p>
            <small>${new Date(message.created_at).toLocaleString()}</small>
        `;
        document.getElementById('messages-container').appendChild(msgElement);
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Использование
const chatClient = new ChatGroupClient(1, token);
chatClient.connect();

// Отправка сообщения при нажатии на кнопку
document.getElementById('send-btn').addEventListener('click', () => {
    const text = document.getElementById('message-input').value;
    chatClient.sendMessage(text);
    document.getElementById('message-input').value = '';
});
```

### 5. Отправка сообщений в канале (WebSocket)

```javascript
class ChannelClient {
    constructor(channelId, token) {
        this.channelId = channelId;
        this.token = token;
        this.ws = null;
    }
    
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.ws = new WebSocket(
            `${protocol}//${window.location.host}/ws/channel/${this.channelId}/`
        );
        
        this.ws.onopen = () => {
            console.log('Подключено к каналу');
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log(`Сообщение в канале: ${data.author.username}: ${data.text}`);
            this.displayMessage(data);
        };
    }
    
    sendMessage(text) {
        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                action: 'send.message',
                message_type: 'text',
                text: text
            }));
        }
    }
    
    displayMessage(message) {
        const msgElement = document.createElement('div');
        msgElement.className = 'channel-message';
        msgElement.innerHTML = `
            <strong>${message.author.username}</strong>: ${message.text}
        `;
        document.getElementById('channel-messages').appendChild(msgElement);
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Использование
const channelClient = new ChannelClient(1, token);
channelClient.connect();
```

### 6. Управление членами группы

```javascript
// Добавить члена в группу
async function addGroupMember(groupId, userId) {
    const response = await fetch(`/api/messenger/groups/${groupId}/members/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            user_id: userId
        })
    });
    
    if (!response.ok) {
        const error = await response.json();
        console.error('Ошибка:', error);
        return null;
    }
    
    const member = await response.json();
    console.log(`Пользователь ${member.user.username} добавлен в группу`);
    return member;
}

// Назначить лидера группы
async function assignGroupLeader(groupId, userId) {
    const response = await fetch(`/api/messenger/groups/${groupId}/assign-leader/`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            user_id: userId
        })
    });
    
    if (!response.ok) {
        const error = await response.json();
        console.error('Ошибка:', error);
        return null;
    }
    
    const member = await response.json();
    console.log(`${member.user.username} назначен лидером группы`);
    return member;
}

// Получить список членов группы
async function getGroupMembers(groupId) {
    const response = await fetch(`/api/messenger/groups/${groupId}/members/`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    const members = await response.json();
    members.forEach(m => {
        const role = m.is_leader ? '(Лидер)' : '';
        console.log(`${m.user.first_name} ${m.user.last_name} ${role}`);
    });
    return members;
}
```

### 7. Получение истории сообщений

```javascript
// Получить все сообщения группы
async function getGroupMessages(groupId) {
    const response = await fetch(`/api/messenger/groups/${groupId}/messages/`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    const messages = await response.json();
    messages.forEach(msg => {
        console.log(`[${msg.created_at}] ${msg.author.username}: ${msg.text}`);
    });
    return messages;
}

// Получить все сообщения канала
async function getChannelMessages(channelId) {
    const response = await fetch(`/api/messenger/channels/${channelId}/messages/`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    const messages = await response.json();
    return messages;
}
```

### 8. Проверка прав и ошибки

```javascript
// Проверка прав перед действием
async function checkCanManageGroup(groupId) {
    const group = await getChatGroupDetails(groupId);
    const currentUserId = getCurrentUserId(); // Ваша функция
    
    // Проверить, является ли текущий пользователь админом или лидером
    if (group.admin.id === currentUserId || group.leader_id === currentUserId) {
        return true;
    }
    
    console.log('У вас нет прав на управление группой');
    return false;
}

// Проверка прав для создания канала
async function checkCanCreateChannel() {
    const response = await fetch('/api/user/profile/', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    const user = await response.json();
    
    if (user.role === 'admin') {
        return true;
    }
    
    console.log('Только администраторы платформы могут создавать каналы');
    return false;
}

// Обработка ошибок
async function safeAPICall(fetchPromise) {
    try {
        const response = await fetchPromise;
        
        if (!response.ok) {
            if (response.status === 403) {
                console.error('Доступ запрещен');
            } else if (response.status === 404) {
                console.error('Ресурс не найден');
            } else {
                const error = await response.json();
                console.error('Ошибка:', error);
            }
            return null;
        }
        
        return await response.json();
    } catch (error) {
        console.error('Сетевая ошибка:', error);
        return null;
    }
}
```

## React компонент пример

```jsx
import React, { useState, useEffect, useRef } from 'react';

function ChatGroup({ groupId, token }) {
    const [messages, setMessages] = useState([]);
    const [groupInfo, setGroupInfo] = useState(null);
    const [messageText, setMessageText] = useState('');
    const ws = useRef(null);
    
    useEffect(() => {
        // Загрузить информацию о группе
        fetch(`/api/messenger/groups/${groupId}/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        .then(r => r.json())
        .then(data => setGroupInfo(data));
        
        // Загрузить сообщения
        fetch(`/api/messenger/groups/${groupId}/messages/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        .then(r => r.json())
        .then(data => setMessages(data));
        
        // Подключиться к WebSocket
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        ws.current = new WebSocket(
            `${protocol}//${window.location.host}/ws/messenger/${groupId}/`
        );
        
        ws.current.onmessage = (event) => {
            const message = JSON.parse(event.data);
            setMessages(prev => [...prev, message]);
        };
        
        return () => ws.current?.close();
    }, [groupId, token]);
    
    const sendMessage = () => {
        if (messageText && ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({
                action: 'send.message',
                message_type: 'text',
                text: messageText
            }));
            setMessageText('');
        }
    };
    
    if (!groupInfo) return <div>Загрузка...</div>;
    
    return (
        <div className="chat-group">
            <div className="group-header">
                <h2>{groupInfo.name}</h2>
                <p>Администратор: {groupInfo.admin.first_name} {groupInfo.admin.last_name}</p>
                <p>Участников: {groupInfo.members_count}</p>
            </div>
            
            <div className="messages">
                {messages.map(msg => (
                    <div key={msg.id} className="message">
                        <strong>{msg.author.first_name}:</strong> {msg.text}
                        <small>{new Date(msg.created_at).toLocaleString()}</small>
                    </div>
                ))}
            </div>
            
            <div className="message-input">
                <input
                    value={messageText}
                    onChange={(e) => setMessageText(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="Введите сообщение..."
                />
                <button onClick={sendMessage}>Отправить</button>
            </div>
        </div>
    );
}

export default ChatGroup;
```
