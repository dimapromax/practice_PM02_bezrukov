Сценарий: Полный отказ региона us-east-1
Шаг 1. Активация плана (0-5 минут)
bash
# Проверка доступности основного региона
aws ec2 describe-instances --region us-east-1

# Отправка уведомления команде
aws sns publish --topic-arn arn:aws:sns:us-west-2:123456789012:DR-Alerts \
    --message "⚠️ DR ACTIVATED: Full region failure us-east-1"
Ответственный: DevOps Lead
Ожидаемое время: 5 минут

Шаг 2. Развертывание инфраструктуры (5-30 минут)
bash
# 1. Клонирование Terraform-конфигураций
cd /infra/terraform/us-west-2/
git pull origin main

# 2. Применение конфигурации
export TF_VAR_environment="dr"
terraform apply -auto-approve

# 3. Проверка поднятых ресурсов
aws ec2 describe-instances --region us-west-2 --filters "Name=tag:Environment,Values=dr"
Ответственный: DevOps Lead
Ожидаемое время: 30 минут

Шаг 3. Восстановление MongoDB (Профили игроков) - 30-45 минут
bash
# 1. Получение последнего снапшота из S3
LATEST_SNAPSHOT=$(aws s3 ls s3://dragonforge-backups/mongodb/profiles/snapshots/ | sort | tail -n 1 | awk '{print $4}')
aws s3 cp s3://dragonforge-backups/mongodb/profiles/snapshots/${LATEST_SNAPSHOT} /tmp/snapshot.tar.gz

# 2. Распаковка и восстановление
tar -xzf /tmp/snapshot.tar.gz -C /tmp/snapshot/
mongorestore --host mongodb-dr-cluster:27017 --username admin --password ${MONGO_PASSWORD} \
    --authenticationDatabase admin --oplogReplay /tmp/snapshot/

# 3. Проверка целостности
mongo --host mongodb-dr-cluster:27017 --eval "db.players.count()"
# Ожидаемое: 4,500,000
Ответственный: DBA MongoDB
Ожидаемое время: 45 минут

Шаг 4. Восстановление Redis (Инвентарь игроков) - 10-15 минут
bash
# 1. Получение последнего RDB-файла
LATEST_RDB=$(aws s3 ls s3://dragonforge-backups/redis/ | sort | tail -n 1 | awk '{print $4}')
aws s3 cp s3://dragonforge-backups/redis/${LATEST_RDB} /tmp/dump.rdb

# 2. Остановка Redis и восстановление
redis-cli SHUTDOWN
cp /tmp/dump.rdb /var/lib/redis/dump.rdb
chown redis:redis /var/lib/redis/dump.rdb
systemctl start redis

# 3. Проверка
redis-cli INFO keyspace
# Ожидаемое: 50 млн ключей
Ответственный: DBA Redis
Ожидаемое время: 15 минут

Шаг 5. Восстановление История покупок - 20-30 минут
bash
# 1. Получение последнего снапшота
LATEST_SNAPSHOT=$(aws s3 ls s3://dragonforge-backups/mongodb/purchases/snapshots/ | sort | tail -n 1 | awk '{print $4}')
aws s3 cp s3://dragonforge-backups/mongodb/purchases/snapshots/${LATEST_SNAPSHOT} /tmp/purchases.tar.gz

# 2. Восстановление
tar -xzf /tmp/purchases.tar.gz -C /tmp/purchases/
mongorestore --host mongodb-dr-cluster:27017 --username admin --password ${MONGO_PASSWORD} \
    --authenticationDatabase admin /tmp/purchases/

# 3. Проверка: сумма транзакций за последний день
mongo --host mongodb-dr-cluster:27017 --eval "db.transactions.aggregate([{$match: {date: ISODate('2026-06-17')}}, {$group: {_id: null, total: {$sum: '$amount'}}}])"
# Ожидаемое: $1,200,000
Ответственный: DBA MongoDB
Ожидаемое время: 30 минут

Шаг 6. Восстановление Ceph (Скины, текстуры) - 60 минут
bash
# 1. Восстановление из S3 (последние 30 дней)
rclone sync s3:backups-ceph/skins/ ceph-dr:skins/ --checksum --transfers 16

# 2. Проверка
rados -p skins ls | wc -l
# Ожидаемое: 5,000,000
Ответственный: DevOps Lead
Ожидаемое время: 60 минут

Шаг 7. Проверка работоспособности (10 минут)
bash
# 1. Проверка MongoDB
mongo --host mongodb-dr-cluster:27017 --eval "db.players.count()" > /tmp/players_count.txt

# 2. Проверка Redis
redis-cli INFO keyspace | grep "db0" > /tmp/redis_keys.txt

# 3. Проверка API
curl -X GET https://api.dragonforge.com/health | jq '.status'

echo "=== Восстановление завершено ==="
Ответственный: On-Call Engineer
Ожидаемое время: 10 минут

Шаг 8. Переключение DNS (20 минут)
bash
# 1. Обновление DNS-записей
aws route53 change-resource-record-sets \
    --hosted-zone-id Z1234567890 \
    --change-batch file://dns_failover.json

# 2. Оповещение игроков
curl -X POST https://notifications.dragonforge.com/api/announce \
    -H "Content-Type: application/json" \
    -d '{"title": "Сервер восстановлен!", "message": "Игра доступна в обычном режиме."}'
Ответственный: DevOps Lead
Ожидаемое время: 20 минут

