#!/bin/sh
set -e

# Ждём доступности PostgreSQL
if [ "$DB_HOST" = "db" ]; then
    echo "Waiting for PostgreSQL..."
    while ! nc -z $DB_HOST $DB_PORT; do
        sleep 0.1
    done
    echo "PostgreSQL started"
fi
# Ждём доступность Redis
if [ -n "$REDIS_HOST" ] && [ "$REDIS_HOST" = "redis" ]; then
    echo "Waiting for Redis..."
    while ! nc -z $REDIS_HOST $REDIS_PORT; do
        sleep 0.1
    done
    echo "Redis started"
fi
# Создание папки для логов
mkdir -p /app/logs

# Выполнение переданной команды
exec "$@"
