#!/bin/bash
# restore_mongodb.sh - Восстановление MongoDB из бэкапа

set -e

# Конфигурация
MONGO_HOST="${MONGO_HOST:-localhost}"
MONGO_PORT="${MONGO_PORT:-27017}"
MONGO_USER="${MONGO_USER:-admin}"
MONGO_PASSWORD="${MONGO_PASSWORD:-}"
S3_BUCKET="${S3_BUCKET:-dragonforge-backups}"
S3_PREFIX="${S3_PREFIX:-mongodb/profiles/snapshots/}"
RESTORE_DIR="${RESTORE_DIR:-/tmp/restore}"

# Парсинг аргументов
BACKUP_TIMESTAMP="${1:-latest}"

if [ "$BACKUP_TIMESTAMP" == "latest" ]; then
    echo "Getting latest backup timestamp..."
    BACKUP_TIMESTAMP=$(aws s3 ls "s3://$S3_BUCKET/$S3_PREFIX" | sort | tail -n 1 | awk '{print $2}' | sed 's/\/$//')
    echo "Latest backup: $BACKUP_TIMESTAMP"
else
    echo "Using specified timestamp: $BACKUP_TIMESTAMP"
fi

# Создание директории для восстановления
mkdir -p "$RESTORE_DIR"

# Скачивание бэкапа
echo "Downloading backup from S3..."
aws s3 cp "s3://$S3_BUCKET/$S3_PREFIX$BACKUP_TIMESTAMP/backup.tar.gz" "$RESTORE_DIR/backup.tar.gz"

# Проверка контрольной суммы
echo "Verifying checksum..."
aws s3 cp "s3://$S3_BUCKET/$S3_PREFIX$BACKUP_TIMESTAMP/backup.tar.gz.sha256" "$RESTORE_DIR/backup.tar.gz.sha256"
if ! sha256sum -c "$RESTORE_DIR/backup.tar.gz.sha256"; then
    echo "❌ Checksum verification failed!"
    exit 1
fi

# Распаковка
echo "Extracting backup..."
tar -xzf "$RESTORE_DIR/backup.tar.gz" -C "$RESTORE_DIR"

# Восстановление MongoDB
echo "Restoring MongoDB..."
if [ -n "$MONGO_PASSWORD" ]; then
    mongorestore --host "$MONGO_HOST" --port "$MONGO_PORT" \
        --username "$MONGO_USER" --password "$MONGO_PASSWORD" \
        --authenticationDatabase admin \
        --oplogReplay \
        "$RESTORE_DIR/$BACKUP_TIMESTAMP"/
else
    mongorestore --host "$MONGO_HOST" --port "$MONGO_PORT" \
        --oplogReplay \
        "$RESTORE_DIR/$BACKUP_TIMESTAMP"/
fi

# Проверка целостности
echo "Verifying restoration..."
MONGO_CMD="mongo --host $MONGO_HOST --port $MONGO_PORT"
if [ -n "$MONGO_PASSWORD" ]; then
    MONGO_CMD="$MONGO_CMD --username $MONGO_USER --password $MONGO_PASSWORD --authenticationDatabase admin"
fi
PLAYER_COUNT=$($MONGO_CMD --eval "db.players.count()" --quiet)
echo "Total players restored: $PLAYER_COUNT"

# Очистка
rm -rf "$RESTORE_DIR"

echo "✅ MongoDB restoration completed successfully"