-- 1–5. Создание БД и таблиц. Обратите внимание на связь M:N между книгами и авторами (таблица BookAuthors).--
create database biblioteka
use biblioteka
create table books (
id_книги INT PRIMARY KEY AUTO_INCREMENT,
название varchar(200) not null,
автор varchar(100) not null,
год int,
isbn varchar(20) unique,
количество_экземпляров int default 1
);
create table autors (
id_автора INT PRIMARY KEY AUTO_INCREMENT,
ФИО varchar(200) not null
);
create table bookautors (
id_книги int,
id_автора int,
primary key (id_книги, id_автора),
FOREIGN KEY (id_книги) REFERENCES books(id_книги) ON DELETE CASCADE,
FOREIGN KEY (id_автора) REFERENCES autors(id_автора) ON DELETE CASCADE
);
create table readers (
id_читателя int primary key auto_increment,
ФИО varchar(200) not null,
дата_рождения date not null,
телефон varchar(20),
адрес varchar(225),
дата_регистрации date not null
);
create table loans (
id_выдачи  int primary key auto_increment,
id_читателя int,
id_книги int,
дата_выдачи date,
дата_возврата_план date,
дата_возврата_факт date,
статус varchar(20),
FOREIGN KEY (id_книги) REFERENCES books(id_книги),
FOREIGN KEY (id_читателя) REFERENCES readers(id_читателя)
);
create table fines (
id_штрафа int primary key auto_increment,
id_читателя int,
сумма decimal(10,2),
причина varchar(200),
статус boolean default FALSE,
FOREIGN KEY (id_читателя) REFERENCES readers(id_читателя)
);
-- 6.	Вставьте 5 книг (название, год, isbn). --
INSERT INTO books (название, автор, год, isbn, количество_экземпляров) VALUES
('Мастер и Маргарита', 'Булгаков М.А.', 1967, '978-5-17-118-123-4', 5),
('Преступление и наказание', 'Достоевский Ф.М.', 1866, '978-5-04-108-456-7', 4),
('Война и мир', 'Толстой Л.Н', 1869, '978-5-17-096-789-0', 3),
('Евгений Онегин', 'Пушкин А.С.', 1833, '978-5-04-112-345-6', 6),
('Мёртвые души', 'Гоголь Н.В.', 1842, '978-5-17-101-234-5', 4);
-- 7.	Вставьте 4 авторов (имя, фамилия). --
insert into autors (ФИО) values
('Булгаков М.А.'),
('Достоевский Ф.М.'),
('Толстой Л.Н.'),
('Пушкин А.С.'),
('Гоголь Н.В.');
-- 8.	Свяжите книги с авторами (например, книга «Война и мир» – Толстой). --
INSERT INTO bookautors (id_книги, id_автора) VALUES (1, 1);
INSERT INTO bookautors (id_книги, id_автора) VALUES (2, 2);
INSERT INTO bookautors (id_книги, id_автора) VALUES (3, 3);
INSERT INTO bookautors (id_книги, id_автора) VALUES (4, 4);
INSERT INTO bookautors (id_книги, id_автора) VALUES (5, 5);
-- 9.	Добавьте 3 читателей.
insert into readers (ФИО, дата_рождения, телефон, адрес, дата_регистрации) values
('Иванов Сергей Петрович', '1990-05-15', '+7(495)123-45-67', 'ул. Ленина, д. 10, кв. 5', '2023-01-10'),
('Петрова Анна Сергеевна', '1985-08-22', '+7(495)234-56-78', 'пр. Мира, д. 25, кв. 18', '2023-05-15'),
('Сидоров Алексей Владимирович', '2000-12-10', '+7(916)345-67-89', 'ул. Гагарина, д. 7, кв. 42', '2023-03-20');
-- 10.	Создайте 5 записей о выдаче книг (дата выдачи, дата возврата плановая, фактическая – может быть NULL). --
insert into loans (id_книги,id_читателя, дата_выдачи, дата_возврата_план, дата_возврата_факт, статус) values
(1, 2, '2025-06-01', '2025-06-15', '2025-06-14', 'возвращена'),
(2, 2, '2025-06-02', '2025-06-16', null, 'выдана'),
(3, 3, '2025-06-03', '2025-06-17', '2025-06-18', 'просрочена'),
(4, 1, '2025-06-05', '2025-06-19', '2025-06-29', 'просрочена'),
(5, 2, '2025-06-07', '2025-06-21', '2025-06-20', 'возвращена');
-- 11.	Добавьте 2 штрафа (для читателей, которые просрочили возврат). --
insert into fines (id_читателя, сумма, причина, статус) values
(3, 150.00, 'просрочка книги Война и мир', false),
(1, 200.00, 'просрочка книги Евгений онегин и повреждение', true);
-- 12.	Вывести все книги, изданные после 2000 года -- 
select * from biblioteka.books
where год > 2000
-- 13.	Вывести список читателей, отсортированных по фамилии --
select * from biblioteka.readers
order by фио
-- 14.	Найти книги, в названии которых есть слово «мир» (LIKE). --
select * from biblioteka.books
where название like '%мир%'
-- 15.	Вывести все выдачи с указанием фамилии читателя и названия книги (JOIN). --
SELECT 
    l.id_выдачи,
    r.ФИО,
    b.название,
    l.дата_выдачи,
    l.дата_возврата_план,
    l.дата_возврата_факт
FROM loans l
JOIN readers r ON l.id_читателя = r.id_читателя
JOIN books b ON l.id_книги = b.id_книги;
-- 16.	Для каждой книги посчитать, сколько раз её брали (выводить только книги с количеством > 0). --
SELECT 
    b.название,
    COUNT(l.id_выдачи) AS количество_выдач
FROM books b
JOIN loans l ON b.id_книги = l.id_книги
GROUP BY b.id_книги
HAVING количество_выдач > 0;
-- 17.	Найти читателя, который брал книги чаще всего (сортировка и LIMIT). -- 
SELECT 
    r.ФИО,
    COUNT(l.id_выдачи) AS количество_выдач
FROM readers r
JOIN loans l ON r.id_читателя = l.id_читателя
GROUP BY r.id_читателя
ORDER BY количество_выдач DESC
LIMIT 1;
-- 18.	Вывести среднюю дату возврата (фактическую) по всем выдачам, где возврат был. --
-- Средняя разница в днях между выдачей и возвратом
SELECT 
    AVG(DATEDIFF(дата_возврата_факт, дата_выдачи)) AS средняя_разница
FROM loans
WHERE дата_возврата_факт IS NOT NULL;
-- 19.	Сгруппировать выдачи по месяцам и подсчитать количество выдач. --
SELECT 
    YEAR(дата_выдачи) AS year,
    MONTH(дата_выдачи) AS month,
    COUNT(*) AS количество_выдач
FROM loans
GROUP BY YEAR(дата_выдачи), MONTH(дата_выдачи)
ORDER BY year DESC, month DESC;
-- 20.	Найти книги, которые ни разу не выдавались (LEFT JOIN + NULL).
SELECT b.*
FROM books b
LEFT JOIN loans l ON b.id_книги = l.id_книги
WHERE l.id_выдачи IS NULL;
-- 21.	Установить штраф в размере 50 руб. для всех неоплаченных штрафов (UPDATE).
update Fines 
set сумма = 50.00 
where статус = FALSE;
-- 22.	Удалить книгу с id=5 (если у неё нет выдач, иначе сначала удалить связи).
SELECT * FROM loans WHERE id_книги = 5;
DELETE FROM books WHERE id_книги = 5;
DELETE FROM loans WHERE id_книги = 5;
DELETE FROM books WHERE id_книги = 5;
-- 23.	Добавить в таблицу Books поле pages (INT).
ALTER TABLE books ADD COLUMN pages INT;
-- 24.	Создать представление OverdueLoans, показывающее читателей и книги, у которых planned_return_date < CURDATE() и фактический возврат NULL.
CREATE VIEW OverdueLoans AS
SELECT 
    r.ФИО AS читатель,
    b.название AS книга,
    l.дата_выдачи,
    l.дата_возврата_план AS план_возврата,
    DATEDIFF(CURDATE(), l.дата_возврата_план) AS дней_просрочки
FROM loans l
JOIN readers r ON l.id_читателя = r.id_читателя
JOIN books b ON l.id_книги = b.id_книги
WHERE l.дата_возврата_план < CURDATE() 
  AND l.дата_возврата_факт IS NULL;