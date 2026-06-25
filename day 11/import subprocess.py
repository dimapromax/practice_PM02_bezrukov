import subprocess
import boto3
import os
import logging
from datetime import datetime
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Конфигурация
DB_NAME = "fenix_orders"
S3_BUCKET = "fenix-backups-prod"
S3_PREFIX = "postgresql/wal/"
IMMUTABLE_DAYS = 30
LOCAL_WAL_DIR = "/var/lib/postgresql/wal_archive/"

def check_disk_space():
    """Проверка свободного места перед бэкапом (должно быть > 20%)"""
    stat = os.statvfs(LOCAL_WAL_DIR)
    free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
    if free_gb < 50:  # минимум 50 ГБ свободно
        raise Exception(f"Недостаточно места: {free_gb:.2f} ГБ")
    logger.info(f"Свободно: {free_gb:.2f} ГБ")

def upload_to_s3_with_lock(file_path, s3_key):
    """Загрузка с включением Object Lock (Immutable)"""
    s3 = boto3.client('s3')
    with open(file_path, 'rb') as f:
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=f,
            ObjectLockMode='GOVERNANCE',
            ObjectLockRetainUntilDate=datetime.now() + timedelta(days=IMMUTABLE_DAYS)
        )
    logger.info(f"Загружен {s3_key} с защитой от удаления на {IMMUTABLE_DAYS} дней")

def cleanup_local(days=7):
    """Удаление локальных файлов старше 7 дней"""
    cutoff = datetime.now() - timedelta(days=days)
    for f in os.listdir(LOCAL_WAL_DIR):
        fpath = os.path.join(LOCAL_WAL_DIR, f)
        if os.path.getctime(fpath) < cutoff.timestamp():
            os.remove(fpath)
            logger.info(f"Удален локальный файл: {fpath}")

def run_backup():
    """Основная функция бэкапа"""
    try:
        check_disk_space()
        
        # 1. Создание WAL-архива
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        wal_file = f"{LOCAL_WAL_DIR}/wal_{timestamp}.wal"
        
        cmd = f"pg_basebackup -D {LOCAL_WAL_DIR} -X stream -P -U repl_user -h localhost"
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
        
        # 2. Сжатие
        compressed_file = f"{wal_file}.zst"
        subprocess.run(f"zstd -19 {wal_file} -o {compressed_file}", shell=True, check=True)
        
        # 3. Вычисление контрольной суммы (Checksum)
        with open(compressed_file, 'rb') as f:
            checksum = hashlib.md5(f.read()).hexdigest()
        
        # 4. Загрузка в S3 с тегом immutable
        s3_key = f"{S3_PREFIX}{timestamp}/wal_{timestamp}.zst"
        upload_to_s3_with_lock(compressed_file, s3_key)
        
        # 5. Отправка метрики в мониторинг (Prometheus Pushgateway)
        metric_payload = {
            "job_name": "Dragon's Forge",
            "status": "success",
            "size_bytes": os.path.getsize(compressed_file),
            "duration_seconds": 0,  # замеряется отдельно
            "timestamp": timestamp,
            "checksum_md5": checksum
        }
        # Отправка HTTP POST на Pushgateway (опущено для краткости)
        
        # 6. Очистка локального хранилища
        cleanup_local()
        
        logger.info("Бэкап успешно завершен")
        return metric_payload
        
    except Exception as e:
        logger.error(f"Ошибка бэкапа: {e}")
        # Отправка алерта в Slack (опущено)
        raise

if __name__ == "__main__":
    run_backup()
