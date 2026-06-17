#!/usr/bin/env python3
"""
backup_mongodb.py - Инкрементальный бэкап MongoDB с oplog
"""

import subprocess
import boto3
import os
import logging
from datetime import datetime, timedelta
import hashlib
import json
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/backup/backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = os.getenv('MONGO_PORT', '27017')
MONGO_USER = os.getenv('MONGO_USER', 'backup_user')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD')
S3_BUCKET = os.getenv('S3_BUCKET', 'dragonforge-backups')
S3_PREFIX = os.getenv('S3_PREFIX', 'mongodb/profiles/snapshots/')
LOCAL_BACKUP_DIR = os.getenv('LOCAL_BACKUP_DIR', '/backup/mongodb/')
IMMUTABLE_DAYS = int(os.getenv('IMMUTABLE_DAYS', '30'))
RETENTION_DAYS = int(os.getenv('RETENTION_DAYS', '7'))
MIN_FREE_SPACE_GB = float(os.getenv('MIN_FREE_SPACE_GB', '50'))

# Инициализация S3-клиента
s3_client = boto3.client('s3')


def check_disk_space():
    """Проверка свободного места перед бэкапом"""
    stat = os.statvfs(LOCAL_BACKUP_DIR)
    free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
    if free_gb < MIN_FREE_SPACE_GB:
        raise Exception(f"Недостаточно места: {free_gb:.2f} ГБ (нужно {MIN_FREE_SPACE_GB} ГБ)")
    logger.info(f"Свободно: {free_gb:.2f} ГБ")
    return free_gb


def create_backup():
    """Создание бэкапа MongoDB с oplog"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(LOCAL_BACKUP_DIR, timestamp)
    os.makedirs(backup_dir, exist_ok=True)
    
    logger.info(f"Начинаем бэкап MongoDB в {backup_dir}")
    
    # mongodump с oplog
    cmd = [
        'mongodump',
        '--host', MONGO_HOST,
        '--port', MONGO_PORT,
        '--username', MONGO_USER,
        '--password', MONGO_PASSWORD,
        '--authenticationDatabase', 'admin',
        '--oplog',
        '--out', backup_dir,
        '--gzip'
    ]
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration = time.time() - start_time
    
    if result.returncode != 0:
        logger.error(f"mongodump failed: {result.stderr}")
        raise Exception(f"Backup failed: {result.stderr}")
    
    logger.info(f"mongodump завершен за {duration:.2f} сек")
    
    # Создание архива
    archive_file = f"{backup_dir}.tar.gz"
    cmd = ['tar', '-czf', archive_file, '-C', LOCAL_BACKUP_DIR, timestamp]
    subprocess.run(cmd, check=True, capture_output=True)
    
    # Вычисление контрольной суммы
    sha256_hash = hashlib.sha256()
    with open(archive_file, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256_hash.update(chunk)
    checksum = sha256_hash.hexdigest()
    
    # Сохранение контрольной суммы
    checksum_file = f"{archive_file}.sha256"
    with open(checksum_file, 'w') as f:
        f.write(f"{checksum}  {os.path.basename(archive_file)}")
    
    # Удаление временной директории
    subprocess.run(['rm', '-rf', backup_dir], check=True)
    
    return {
        'timestamp': timestamp,
        'archive_file': archive_file,
        'checksum': checksum,
        'duration_seconds': duration,
        'size_bytes': os.path.getsize(archive_file)
    }


def upload_to_s3(file_path, s3_key):
    """Загрузка в S3 с защитой от удаления (Immutable)"""
    logger.info(f"Загрузка {file_path} в s3://{S3_BUCKET}/{s3_key}")
    
    retain_until = datetime.now() + timedelta(days=IMMUTABLE_DAYS)
    
    try:
        with open(file_path, 'rb') as f:
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=f,
                ObjectLockMode='GOVERNANCE',
                ObjectLockRetainUntilDate=retain_until,
                StorageClass='STANDARD_IA',
                ServerSideEncryption='AES256',
                Metadata={
                    'backup_time': datetime.now().isoformat(),
                    'checksum': hashlib.sha256(open(file_path, 'rb').read()).hexdigest(),
                    'retention_days': str(IMMUTABLE_DAYS)
                }
            )
        logger.info(f"Успешно загружено: {s3_key}")
        return True
    except Exception as e:
        logger.error(f"Ошибка загрузки: {e}")
        return False


def cleanup_local(days=RETENTION_DAYS):
    """Удаление локальных файлов старше N дней"""
    cutoff = datetime.now() - timedelta(days=days)
    removed_count = 0
    total_size = 0
    
    for f in os.listdir(LOCAL_BACKUP_DIR):
        if not f.endswith('.tar.gz'):
            continue
        fpath = os.path.join(LOCAL_BACKUP_DIR, f)
        if os.path.getctime(fpath) < cutoff.timestamp():
            size = os.path.getsize(fpath)
            os.remove(fpath)
            os.remove(f"{fpath}.sha256") if os.path.exists(f"{fpath}.sha256") else None
            removed_count += 1
            total_size += size
            logger.info(f"Удален локальный файл: {f}")
    
    logger.info(f"Удалено {removed_count} файлов ({total_size / (1024**3):.2f} ГБ)")


def send_metrics(payload):
    """Отправка метрик в Prometheus Pushgateway"""
    pushgateway_url = os.getenv('PUSHGATEWAY_URL', 'http://localhost:9091')
    
    try:
        import requests
        response = requests.post(
            f"{pushgateway_url}/metrics/job/backup",
            data=payload,
            headers={'Content-Type': 'text/plain'}
        )
        if response.status_code != 200:
            logger.warning(f"Pushgateway error: {response.status_code}")
    except Exception as e:
        logger.warning(f"Не удалось отправить метрики: {e}")


def main():
    """Основная функция"""
    try:
        logger.info("=" * 50)
        logger.info("Запуск бэкапа MongoDB")
        
        # 1. Проверка дискового пространства
        free_gb = check_disk_space()
        
        # 2. Создание бэкапа
        backup_info = create_backup()
        
        # 3. Загрузка в S3
        s3_key = f"{S3_PREFIX}{backup_info['timestamp']}/{os.path.basename(backup_info['archive_file'])}"
        upload_success = upload_to_s3(backup_info['archive_file'], s3_key)
        
        # 4. Загрузка контрольной суммы
        checksum_key = f"{s3_key}.sha256"
        upload_to_s3(f"{backup_info['archive_file']}.sha256", checksum_key)
        
        # 5. Очистка локального хранилища
        cleanup_local()
        
        # 6. Подготовка метрик
        metric_str = (
            f'backup_status{{job="mongodb_profiles"}} {1 if upload_success else 0}\n'
            f'backup_size_bytes{{job="mongodb_profiles"}} {backup_info["size_bytes"]}\n'
            f'backup_duration_seconds{{job="mongodb_profiles"}} {backup_info["duration_seconds"]}\n'
            f'backup_free_space_gb{{job="mongodb_profiles"}} {free_gb}\n'
            f'backup_last_timestamp{{job="mongodb_profiles"}} {int(datetime.now().timestamp())}\n'
        )
        send_metrics(metric_str)
        
        logger.info(" Бэкап успешно завершен")
        return 0
        
    except Exception as e:
        logger.error(f" Критическая ошибка: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())