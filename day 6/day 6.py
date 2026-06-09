import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error

# ==================================================
# Функция подключения к вашей БД
# ==================================================
def connect_db():
    """Подключение к базе данных MySQL"""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="dimabdn2008BEZR",          # ⚠️ ВВЕДИТЕ ВАШ ПАРОЛЬ
            database="biblioteka"
        )
        return connection
    except Error as e:
        messagebox.showerror("Ошибка БД", f"Не удалось подключиться: {e}")
        return None

# ==================================================
# Класс приложения для таблицы books
# ==================================================
class DatabaseApp:
    def __init__(self, root):
        self.root = root
        self.table_name = "books"
        
        # Описание столбцов таблицы books (ТОЧНЫЕ имена полей из DESCRIBE)
        self.columns = [
            {"name": "id_книги", "label": "ID", "pk": True, "auto_increment": True},
            {"name": "название", "label": "Название", "required": True},
            {"name": "автор", "label": "Автор", "required": True},
            {"name": "год", "label": "Год", "required": False},
            {"name": "isbn", "label": "ISBN", "required": False},
            {"name": "количество_экземпляров", "label": "Кол-во", "required": False},
            {"name": "pages", "label": "Страниц", "required": False}
        ]
        
        self.root.title("Управление таблицей: КНИГИ (библиотека)")
        self.root.geometry("950x550")
        
        self.create_widgets()
        self.refresh_table()
    
    def create_widgets(self):
        """Создание всех элементов интерфейса"""
        
        # === Рамка для полей ввода ===
        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=10)
        
        self.entries = {}
        
        # Создаём поля для каждого столбца (кроме PK с AUTO_INCREMENT)
        col_index = 0
        for col in self.columns:
            # Пропускаем PK с AUTO_INCREMENT
            if col.get('pk') and col.get('auto_increment'):
                continue
            
            # Метка
            label = tk.Label(input_frame, text=f"{col['label']}:", font=("Arial", 10, "bold"))
            label.grid(row=0, column=col_index*2, padx=5, pady=5, sticky="e")
            
            # Поле ввода
            entry = tk.Entry(input_frame, width=25, font=("Arial", 10))
            entry.grid(row=0, column=col_index*2+1, padx=5, pady=5)
            self.entries[col['name']] = entry
            col_index += 1
        
        # === Кнопки ===
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="➕ Добавить", command=self.add_record, 
                  bg="#90EE90", width=12, font=("Arial", 10)).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="✏️ Обновить", command=self.update_record, 
                  bg="#FFD700", width=12, font=("Arial", 10)).grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="🗑️ Удалить", command=self.delete_record, 
                  bg="#FF6347", width=12, font=("Arial", 10)).grid(row=0, column=2, padx=5)
        tk.Button(button_frame, text="🧹 Очистить", command=self.clear_entries, 
                  width=12, font=("Arial", 10)).grid(row=0, column=3, padx=5)
        tk.Button(button_frame, text="🔄 Показать всех", command=self.refresh_table, 
                  width=15, font=("Arial", 10)).grid(row=0, column=4, padx=5)
        
        # === Поле для поиска ===
        search_frame = tk.Frame(self.root)
        search_frame.pack(pady=5)
        
        tk.Label(search_frame, text="🔍 Поиск по названию:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame, width=40, font=("Arial", 10))
        self.search_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Найти", command=self.search, width=10, 
                  font=("Arial", 10)).pack(side=tk.LEFT)
        
        # === Таблица Treeview ===
        tree_frame = tk.Frame(self.root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Создаём скроллы
        scroll_y = tk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x = tk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Определяем колонки для Treeview
        columns_display = [col['name'] for col in self.columns]
        self.tree = ttk.Treeview(tree_frame, columns=columns_display, show="headings",
                                 yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)
        
        # Настраиваем заголовки и ширину колонок
        for col in self.columns:
            self.tree.heading(col['name'], text=col['label'])
            if col['name'] == 'название':
                self.tree.column(col['name'], width=250, anchor="w")
            elif col['name'] == 'автор':
                self.tree.column(col['name'], width=150, anchor="w")
            elif col['name'] == 'id_книги':
                self.tree.column(col['name'], width=50, anchor="center")
            elif col['name'] == 'год':
                self.tree.column(col['name'], width=70, anchor="center")
            elif col['name'] == 'isbn':
                self.tree.column(col['name'], width=150, anchor="center")
            elif col['name'] == 'количество_экземпляров':
                self.tree.column(col['name'], width=70, anchor="center")
            elif col['name'] == 'pages':
                self.tree.column(col['name'], width=70, anchor="center")
            else:
                self.tree.column(col['name'], width=100, anchor="center")
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Привязываем событие выбора строки
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
    
    def refresh_table(self):
        """Обновить данные в таблице Treeview"""
        # Очищаем текущие данные
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        conn = connect_db()
        if not conn:
            return
        
        cursor = conn.cursor()
        columns_names = [col['name'] for col in self.columns]
        query = f"SELECT {', '.join(columns_names)} FROM {self.table_name}"
        
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            for row in rows:
                # Пропускаем строки с NULL id
                if row[0] is not None:
                    self.tree.insert("", tk.END, values=row)
        except Error as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def search(self):
        """Поиск по названию книги"""
        keyword = self.search_entry.get().strip()
        if not keyword:
            self.refresh_table()
            return
        
        conn = connect_db()
        if not conn:
            return
        
        cursor = conn.cursor()
        query = f"SELECT * FROM {self.table_name} WHERE название LIKE %s"
        
        try:
            cursor.execute(query, (f"%{keyword}%",))
            rows = cursor.fetchall()
            
            # Очищаем таблицу
            for row in self.tree.get_children():
                self.tree.delete(row)
            
            # Заполняем результатами поиска
            for row in rows:
                if row[0] is not None:
                    self.tree.insert("", tk.END, values=row)
                
            if len(rows) == 0:
                messagebox.showinfo("Поиск", "Ничего не найдено")
        except Error as e:
            messagebox.showerror("Ошибка", str(e))
        finally:
            cursor.close()
            conn.close()
    
    def on_select(self, event):
        """При выборе строки в таблице — заполняем поля ввода"""
        selected = self.tree.selection()
        if not selected:
            return
        
        values = self.tree.item(selected[0])['values']
        
        idx = 0
        for col in self.columns:
            col_name = col['name']
            if col.get('pk') and col.get('auto_increment'):
                continue
            if col_name in self.entries:
                self.entries[col_name].delete(0, tk.END)
                if idx < len(values) and values[idx] is not None:
                    self.entries[col_name].insert(0, str(values[idx]))
                idx += 1
    
    def get_pk_name(self):
        """Вернуть имя первичного ключа"""
        for col in self.columns:
            if col.get('pk'):
                return col['name']
        return None
    
    def add_record(self):
        """Добавить новую запись"""
        # Собираем значения из полей ввода
        values = {}
        for col_name, entry in self.entries.items():
            val = entry.get().strip()
            if val == "":
                val = None
            values[col_name] = val
        
        # Проверяем обязательные поля
        for col in self.columns:
            col_name = col['name']
            if col.get('required') and col_name in self.entries:
                if not values[col_name]:
                    messagebox.showwarning("Ошибка", f"Поле '{col['label']}' обязательно для заполнения")
                    return
        
        conn = connect_db()
        if not conn:
            return
        
        cursor = conn.cursor()
        
        # Формируем INSERT-запрос
        columns_names = list(values.keys())
        placeholders = ", ".join(["%s"] * len(columns_names))
        query = f"INSERT INTO {self.table_name} ({', '.join(columns_names)}) VALUES ({placeholders})"
        
        try:
            cursor.execute(query, list(values.values()))
            conn.commit()
            messagebox.showinfo("Успех", "Запись добавлена")
            self.clear_entries()
            self.refresh_table()
        except Error as e:
            messagebox.showerror("Ошибка БД", str(e))
        finally:
            cursor.close()
            conn.close()
    
    def update_record(self):
        """Обновить выбранную запись"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите запись для обновления")
            return
        
        pk_name = self.get_pk_name()
        if not pk_name:
            return
        
        # Получаем ID выбранной записи
        values_current = self.tree.item(selected[0])['values']
        pk_index = [col['name'] for col in self.columns].index(pk_name)
        pk_value = values_current[pk_index]
        
        # Собираем новые значения из полей
        new_values = {}
        for col_name, entry in self.entries.items():
            val = entry.get().strip()
            if val == "":
                val = None
            new_values[col_name] = val
        
        conn = connect_db()
        if not conn:
            return
        
        cursor = conn.cursor()
        
        # Формируем UPDATE-запрос
        set_clause = ", ".join([f"{col} = %s" for col in new_values.keys()])
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE {pk_name} = %s"
        
        try:
            params = list(new_values.values()) + [pk_value]
            cursor.execute(query, params)
            conn.commit()
            messagebox.showinfo("Успех", "Запись обновлена")
            self.refresh_table()
        except Error as e:
            messagebox.showerror("Ошибка БД", str(e))
        finally:
            cursor.close()
            conn.close()
    
    def delete_record(self):
        """Удалить выбранную запись"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите запись для удаления")
            return
        
        # Подтверждение удаления
        if not messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить запись?"):
            return
        
        pk_name = self.get_pk_name()
        if not pk_name:
            return
        
        values = self.tree.item(selected[0])['values']
        pk_index = [col['name'] for col in self.columns].index(pk_name)
        pk_value = values[pk_index]
        
        conn = connect_db()
        if not conn:
            return
        
        cursor = conn.cursor()
        query = f"DELETE FROM {self.table_name} WHERE {pk_name} = %s"
        
        try:
            cursor.execute(query, (pk_value,))
            conn.commit()
            messagebox.showinfo("Успех", "Запись удалена")
            self.clear_entries()
            self.refresh_table()
        except Error as e:
            messagebox.showerror("Ошибка БД", str(e))
        finally:
            cursor.close()
            conn.close()
    
    def clear_entries(self):
        """Очистить все поля ввода"""
        for entry in self.entries.values():
            entry.delete(0, tk.END)

# ==================================================
# Запуск приложения
# ==================================================
def main():
    root = tk.Tk()
    app = DatabaseApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()