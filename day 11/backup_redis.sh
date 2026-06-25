#!/bin/bash
# backup_redis.sh - Бэкап Redis RDB-снапшотов

set -e

# Конфигурация
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
BACKUP_DIR="${BACKUP_DIR:-/backup/redis}"
S3_BUCKET="${S3_BUCKET:-dragonforge-backups}"
S3_PREFIX="${S3_PREFIX:-redis/}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

# Создание директории
mkdir -p "$BACKUP_DIR"

# Создание RDB-снапшота
echo "Creating Redis RDB snapshot..."
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" SAVE

# Копирование RDB-файла
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RDB_FILE="$BACKUP_DIR/dump_$TIMESTAMP.rdb"
cp /var/lib/redis/dump.rdb "$RDB_FILE"

# Сжатие
gzip -9 "$RDB_FILE"

# Вычисление контрольной суммы
sha256sum "$RDB_FILE.gz" > "$RDB_FILE.gz.sha256"

# Загрузка в S3
echo "Uploading to S3..."
aws s3 cp "$RDB_FILE.gz" "s3://$S3_BUCKET/$S3_PREFIX$TIMESTAMP/dump.rdb.gz" \
    --storage-class STANDARD_IA \
    --server-side-encryption AES256

aws s3 cp "$RDB_FILE.gz.sha256" "s3://$S3_BUCKET/$S3_PREFIX$TIMESTAMP/dump.rdb.gz.sha256"

# Очистка локальных файлов старше N дней
echo "Cleaning up old backups..."
find "$BACKUP_DIR" -name "dump_*.rdb.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "dump_*.rdb.gz.sha256" -mtime +$RETENTION_DAYS -delete

# Отправка метрики
curl -X POST "http://localhost:9091/metrics/job/backup" \
    --data-binary "backup_status{job=\"redis\"} 1\n"

echo "✅ Redis backup completed successfully"