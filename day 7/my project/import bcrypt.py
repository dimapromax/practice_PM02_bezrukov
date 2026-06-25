import bcrypt
import MySQLdb

# Подключение к БД
conn = MySQLdb.connect(
    host='localhost',
    user='root',
    passwd='dimabdn2008BEZR',
    db='biblioteka'
)
cursor = conn.cursor()

# Создаём хеши для паролей
users = [
    ('admin', 'admin123', 'admin'),
    ('worker', 'worker123', 'worker')
]

for login, password, role in users:
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        cursor.execute(
            "INSERT INTO Пользователи (логин, пароль_hash, роль) VALUES (%s, %s, %s)",
            (login, hashed.decode('utf-8'), role)
        )
        print(f"Пользователь {login} создан")
    except:
        print(f"Пользователь {login} уже существует")

conn.commit()
cursor.close()
conn.close()
