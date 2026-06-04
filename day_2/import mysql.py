import json
import mysql.connector
from mysql.connector import Error
from datetime import datetime

# Конфигурация подключения к MySQL
config = {
    'host': 'localhost',
    'user': 'root',  # замените на вашего пользователя
    'password': 'dimabdn2008BEZR',  # замените на ваш пароль
    'database': 'mybd'  # замените на имя вашей БД
}

def create_table(cursor):
    """Создание таблицы читателей, если она не существует"""
    create_table_query = """
    CREATE TABLE IF NOT EXISTS читатели (
        id_читателя INT PRIMARY KEY,
        фамилия VARCHAR(100) NOT NULL,
        имя VARCHAR(100) NOT NULL,
        отчество VARCHAR(100),
        дата_рождения DATE,
        телефон VARCHAR(20),
        адрес TEXT,
        дата_регистрации DATE
    )
    """
    try:
        cursor.execute(create_table_query)
        print("Таблица 'читатели' создана/проверена")
    except Error as e:
        print(f"Ошибка при создании таблицы: {e}")

def import_json_to_mysql(json_file_path):
    """Импорт данных из JSON файла в MySQL"""
    connection = None
    try:
        # Подключение к MySQL
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Создание таблицы
        create_table(cursor)
        
        # Чтение JSON файла
        with open(json_file_path, 'r', encoding='utf-8') as file:
            readers = json.load(file)
        
        # Подготовка SQL запроса для вставки данных
        insert_query = """
        INSERT INTO читатели (
            id_читателя, фамилия, имя, отчество, 
            дата_рождения, телефон, адрес, дата_регистрации
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            фамилия = VALUES(фамилия),
            имя = VALUES(имя),
            отчество = VALUES(отчество),
            дата_рождения = VALUES(дата_рождения),
            телефон = VALUES(телефон),
            адрес = VALUES(адрес),
            дата_регистрации = VALUES(дата_регистрации)
        """
        
        # Вставка данных
        successful_inserts = 0
        for reader in readers:
            # Преобразование дат из строк в объекты date
            birth_date = datetime.strptime(reader['дата_рождения'], '%Y-%m-%d').date()
            reg_date = datetime.strptime(reader['дата_регистрации'], '%Y-%m-%d').date()
            
            data = (
                reader['id_читателя'],
                reader['фамилия'],
                reader['имя'],
                reader['отчество'],
                birth_date,
                reader['телефон'],
                reader['адрес'],
                reg_date
            )
            cursor.execute(insert_query, data)
            successful_inserts += 1
        
        # Подтверждение транзакции
        connection.commit()
        print(f"\nУспешно импортировано {successful_inserts} записей из {len(readers)}")
        
        # Вывод статистики
        cursor.execute("SELECT COUNT(*) FROM читатели")
        total_records = cursor.fetchone()[0]
        print(f"Всего записей в таблице: {total_records}")
        
    except FileNotFoundError:
        print(f"Ошибка: Файл {json_file_path} не найден")
    except json.JSONDecodeError as e:
        print(f"Ошибка при чтении JSON: {e}")
    except Error as e:
        print(f"Ошибка MySQL: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("\nСоединение с MySQL закрыто")

def show_sample_data(json_file_path):
    """Отображение примера данных перед импортом"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            readers = json.load(file)
        
        print("\n=== Пример данных для импорта ===")
        for i, reader in enumerate(readers[:3], 1):  # Показываем первых 3 читателя
            print(f"\n{i}. {reader['фамилия']} {reader['имя']} {reader['отчество']}")
            print(f"   Дата рождения: {reader['дата_рождения']}")
            print(f"   Телефон: {reader['телефон']}")
            print(f"   Адрес: {reader['адрес']}")
            print(f"   Дата регистрации: {reader['дата_регистрации']}")
        
        print(f"\nВсего записей в файле: {len(readers)}")
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")

# Основная часть программы
if __name__ == "__main__":
    # Путь к вашему JSON файлу
    json_file = "Читатели.json"  # или полный путь к файлу
    
    # Показываем пример данных
    show_sample_data(json_file)
    
    # Запрашиваем подтверждение
    print("\n" + "="*50)
    response = input("Импортировать данные в MySQL? (y/n): ")
    
    if response.lower() == 'y':
        # Выполняем импорт
        import_json_to_mysql(json_file)
    else:
        print("Импорт отменен.")