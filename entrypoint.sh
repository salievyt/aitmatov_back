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

# Создание папки для логов
mkdir -p /app/logs

# Выполнение переданной команды
exec "$@"
