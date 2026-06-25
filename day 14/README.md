День 14. Разработка сервисной части программы
Цели занятия
Реализация сервисного слоя с бизнес-логикой

Внедрение зависимостей

Написание юнит-тестов

Отчёт о выполненной работе
Реализованные сервисы:

BookService - управление книгами (добавление, поиск, удаление)

ReaderService - управление читателями (регистрация, поиск)

LoanService - выдача и возврат книг с проверкой ограничений

FineService - расчёт и управление штрафами

Пример теста:

python
def test_lend_book_success():
    mock_book_repo = Mock()
    mock_book_repo.get_by_id.return_value = Book(id=1, copies=2)
    mock_reader_repo = Mock()
    mock_reader_repo.get_by_id.return_value = Reader(id=1, has_debt=False)
    mock_loan_repo = Mock()
    
    service = LoanService(mock_book_repo, mock_reader_repo, mock_loan_repo)
    result = service.lend_book(1, 1)
    
    assert result is True
    mock_book_repo.decrement_copies.assert_called_once_with(1)
    mock_loan_repo.add.assert_called_once()
Результат: Разработан полностью функционирующий сервисный слой с тестами.