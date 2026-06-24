import pytest
from unittest.mock import MagicMock, patch
from datetime import date, time, datetime, timedelta
from copy import deepcopy

from src.services.clinic_service import ClinicService
from src.services.notification_service import NotificationService
from src.domain.entities import Doctor, Patient, Appointment, WorkingHours
from src.domain.enums import DoctorSpecialization, AppointmentStatus, WeekDay
from src.domain.exceptions import (
    DoctorNotFoundError, PatientNotFoundError, AppointmentNotFoundError,
    ValidationError, AppointmentTimeUnavailableError, AppointmentLimitExceededError,
    AppointmentCancellationError, PatientHasNoShowError, InvalidWorkingHoursError,
    DuplicatePatientError, DomainError
)

# ========== Фикстуры ==========

@pytest.fixture
def mock_repos():
    """Создание моков для репозиториев"""
    doctor_repo = MagicMock()
    patient_repo = MagicMock()
    appointment_repo = MagicMock()
    return doctor_repo, patient_repo, appointment_repo

@pytest.fixture
def mock_notification():
    """Создание мока для сервиса уведомлений"""
    return MagicMock(spec=NotificationService)

@pytest.fixture
def service(mock_repos, mock_notification):
    """Создание сервиса с моками"""
    doctor_repo, patient_repo, appointment_repo = mock_repos
    return ClinicService(doctor_repo, patient_repo, appointment_repo, mock_notification)

@pytest.fixture
def sample_doctor():
    """Пример данных врача"""
    working_hours = {
        WeekDay.MONDAY: WorkingHours(
            day=WeekDay.MONDAY,
            start_time=time(9, 0),
            end_time=time(18, 0),
            lunch_start=time(13, 0),
            lunch_end=time(14, 0)
        ),
        WeekDay.WEDNESDAY: WorkingHours(
            day=WeekDay.WEDNESDAY,
            start_time=time(9, 0),
            end_time=time(18, 0),
            lunch_start=time(13, 0),
            lunch_end=time(14, 0)
        )
    }
    return Doctor(
        id=1,
        full_name="Иван Иванов",
        specialization=DoctorSpecialization.THERAPIST,
        cabinet="101",
        phone="+79111234567",
        email="ivan@clinic.ru",
        working_hours=working_hours
    )

@pytest.fixture
def sample_patient():
    """Пример данных пациента"""
    return Patient(
        id=1,
        full_name="Петр Петров",
        birth_date=date(1990, 1, 1),
        phone="+79221234567",
        email="petr@mail.ru",
        no_show_count=0
    )

@pytest.fixture
def sample_appointment(sample_doctor, sample_patient):
    """Пример данных записи"""
    return Appointment(
        id=1,
        doctor_id=sample_doctor.id,
        patient_id=sample_patient.id,
        appointment_date=date(2026, 1, 15),  # Понедельник
        appointment_time=time(10, 0),
        duration_minutes=30,
        status=AppointmentStatus.SCHEDULED
    )

# ========== Тесты для врачей ==========

def test_add_doctor_success(service, mock_repos, mock_notification):
    """Тест успешного добавления врача"""
    doctor_repo, _, _ = mock_repos
    
    doctor_data = {
        "full_name": "Анна Смирнова",
        "specialization": "Терапевт",
        "cabinet": "202",
        "phone": "+79998887766",
        "email": "anna@clinic.ru",
        "working_hours": {
            "MONDAY": {
                "day": "MONDAY",
                "start_time": "09:00",
                "end_time": "18:00",
                "lunch_start": "13:00",
                "lunch_end": "14:00"
            }
        }
    }
    
    expected_doctor = Doctor(id=1, **doctor_data)
    doctor_repo.add.return_value = expected_doctor
    
    result = service.add_doctor(doctor_data)
    
    assert result == expected_doctor
    doctor_repo.add.assert_called_once()

def test_add_doctor_validation_error(service, mock_repos):
    """Тест ошибки валидации при добавлении врача"""
    doctor_repo, _, _ = mock_repos
    
    invalid_data = {
        "full_name": "",  # Пустое имя
        "specialization": "Терапевт",
        "cabinet": "202",
        "phone": "+79998887766",
        "working_hours": {}
    }
    
    with pytest.raises(ValidationError):
        service.add_doctor(invalid_data)
    
    doctor_repo.add.assert_not_called()

def test_get_doctor_success(service, mock_repos, sample_doctor):
    """Тест успешного получения врача"""
    doctor_repo, _, _ = mock_repos
    doctor_repo.get_by_id.return_value = sample_doctor
    
    result = service.get_doctor(1)
    
    assert result == sample_doctor
    doctor_repo.get_by_id.assert_called_once_with(1)

def test_get_doctor_not_found(service, mock_repos):
    """Тест ошибки при получении несуществующего врача"""
    doctor_repo, _, _ = mock_repos
    doctor_repo.get_by_id.return_value = None
    
    with pytest.raises(DoctorNotFoundError):
        service.get_doctor(999)

# ========== Тесты для пациентов ==========

def test_register_patient_success(service, mock_repos, mock_notification):
    """Тест успешной регистрации пациента"""
    _, patient_repo, _ = mock_repos
    
    patient_data = {
        "full_name": "Иван Сидоров",
        "birth_date": "1985-05-15",
        "phone": "+79001234567",
        "email": "ivan@mail.ru"
    }
    
    expected_patient = Patient(id=1, **patient_data)
    patient_repo.get_by_phone.return_value = None
    patient_repo.add.return_value = expected_patient
    
    result = service.register_patient(patient_data)
    
    assert result == expected_patient
    patient_repo.get_by_phone.assert_called_once()
    patient_repo.add.assert_called_once()

def test_register_patient_duplicate_phone(service, mock_repos, sample_patient):
    """Тест ошибки при регистрации с дублирующимся телефоном"""
    _, patient_repo, _ = mock_repos
    patient_repo.get_by_phone.return_value = sample_patient
    
    patient_data = {
        "full_name": "Другой Иван",
        "birth_date": "1990-01-01",
        "phone": "+79221234567",  # Тот же телефон
        "email": "other@mail.ru"
    }
    
    with pytest.raises(DuplicatePatientError):
        service.register_patient(patient_data)
    
    patient_repo.add.assert_not_called()

# ========== Тесты для записей ==========

def test_create_appointment_success(service, mock_repos, mock_notification, sample_doctor, sample_patient):
    """Тест успешного создания записи"""
    doctor_repo, patient_repo, appointment_repo = mock_repos
    
    appointment_data = {
        "doctor_id": sample_doctor.id,
        "patient_id": sample_patient.id,
        "appointment_date": "2026-01-15",
        "appointment_time": "10:00",
        "duration_minutes": 30
    }
    
    expected_appointment = Appointment(id=1, **appointment_data)
    
    doctor_repo.get_by_id.return_value = sample_doctor
    patient_repo.get_by_id.return_value = sample_patient
    appointment_repo.get_by_doctor_and_date.return_value = []  # Нет других записей
    appointment_repo.add.return_value = expected_appointment
    
    result = service.create_appointment(appointment_data)
    
    assert result == expected_appointment
    appointment_repo.add.assert_called_once()
    mock_notification.send_appointment_reminder.assert_called_once()

def test_create_appointment_doctor_not_found(service, mock_repos, sample_patient):
    """Тест ошибки при создании записи к несуществующему врачу"""
    doctor_repo, patient_repo, _ = mock_repos
    doctor_repo.get_by_id.return_value = None
    patient_repo.get_by_id.return_value = sample_patient
    
    appointment_data = {
        "doctor_id": 999,
        "patient_id": sample_patient.id,
        "appointment_date": "2026-01-15",
        "appointment_time": "10:00"
    }
    
    with pytest.raises(DoctorNotFoundError):
        service.create_appointment(appointment_data)

def test_create_appointment_patient_blocked(service, mock_repos, sample_doctor):
    """Тест ошибки при создании записи для заблокированного пациента"""
    doctor_repo, patient_repo, _ = mock_repos
    
    blocked_patient = Patient(
        id=1,
        full_name="Петр Петров",
        birth_date=date(1990, 1, 1),
        phone="+79221234567",
        no_show_count=3  # Превышен лимит
    )
    
    doctor_repo.get_by_id.return_value = sample_doctor
    patient_repo.get_by_id.return_value = blocked_patient
    
    appointment_data = {
        "doctor_id": sample_doctor.id,
        "patient_id": blocked_patient.id,
        "appointment_date": "2026-01-15",
        "appointment_time": "10:00"
    }
    
    with pytest.raises(PatientHasNoShowError):
        service.create_appointment(appointment_data)

def test_create_appointment_time_unavailable(service, mock_repos, sample_doctor, sample_patient):
    """Тест ошибки при создании записи на занятое время"""
    doctor_repo, patient_repo, appointment_repo = mock_repos
    
    doctor_repo.get_by_id.return_value = sample_doctor
    patient_repo.get_by_id.return_value = sample_patient
    
    # Создаем существующую запись на то же время
    existing_appointment = Appointment(
        id=1,
        doctor_id=sample_doctor.id,
        patient_id=2,
        appointment_date=date(2026, 1, 15),
        appointment_time=time(10, 0),
        duration_minutes=30,
        status=AppointmentStatus.SCHEDULED
    )
    appointment_repo.get_by_doctor_and_date.return_value = [existing_appointment]
    
    appointment_data = {
        "doctor_id": sample_doctor.id,
        "patient_id": sample_patient.id,
        "appointment_date": "2026-01-15",
        "appointment_time": "10:00",
        "duration_minutes": 30
    }
    
    with pytest.raises(AppointmentTimeUnavailableError):
        service.create_appointment(appointment_data)

def test_create_appointment_limit_exceeded(service, mock_repos, sample_doctor, sample_patient):
    """Тест ошибки при превышении лимита записей на день"""
    doctor_repo, patient_repo, appointment_repo = mock_repos
    
    doctor_repo.get_by_id.return_value = sample_doctor
    patient_repo.get_by_id.return_value = sample_patient
    
    # Создаем MAX_APPOINTMENTS_PER_DAY записей
    existing_appointments = []
    for i in range(service.MAX_APPOINTMENTS_PER_DAY):
        app = Appointment(
            id=i+1,
            doctor_id=sample_doctor.id,
            patient_id=i+2,
            appointment_date=date(2026, 1, 15),
            appointment_time=time(9 + i//2, (i%2)*30),
            duration_minutes=30,
            status=AppointmentStatus.SCHEDULED
        )
        existing_appointments.append(app)
    
    appointment_repo.get_by_doctor_and_date.return_value = existing_appointments
    
    appointment_data = {
        "doctor_id": sample_doctor.id,
        "patient_id": sample_patient.id,
        "appointment_date": "2026-01-15",
        "appointment_time": "17:00",  # Последний слот
        "duration_minutes": 30
    }
    
    with pytest.raises(AppointmentLimitExceededError):
        service.create_appointment(appointment_data)

def test_cancel_appointment_success(service, mock_repos, mock_notification, sample_appointment, sample_doctor, sample_patient):
    """Тест успешной отмены записи"""
    _, _, appointment_repo = mock_repos
    
    # Настраиваем время отмены (за 3 часа до приема)
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 1, 15, 7, 0)  # 7:00 утра, за 3 часа до приема в 10:00
        mock_datetime.combine = datetime.combine
        
        appointment_repo.get_by_id.return_value = sample_appointment
        appointment_repo.update.return_value = sample_appointment.model_copy(update={
            "status": AppointmentStatus.CANCELLED,
            "updated_at": datetime(2026, 1, 15, 7, 0),
            "fine_amount": 0.0
        })
        
        # Мокаем методы получения пациента и врача
        doctor_repo, patient_repo, _ = mock_repos
        doctor_repo.get_by_id.return_value = sample_doctor
        patient_repo.get_by_id.return_value = sample_patient
        
        result = service.cancel_appointment(1, "Не могу прийти")
        
        assert result["fine"] == 0.0
        assert "Запись отменена" in result["message"]
        appointment_repo.update.assert_called_once()

def test_cancel_appointment_late(service, mock_repos, mock_notification, sample_appointment):
    """Тест отмены с штрафом (за 1 час до приема)"""
    _, _, appointment_repo = mock_repos
    
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 1, 15, 9, 0)  # 9:00 утра, за 1 час до приема
        mock_datetime.combine = datetime.combine
        
        appointment_repo.get_by_id.return_value = sample_appointment
        
        result = service.cancel_appointment(1, "Опоздал")
        
        assert result["fine"] == service.FINE_FOR_LATE_CANCEL
        assert "Штраф" in result["message"]

def test_cancel_appointment_already_cancelled(service, mock_repos, sample_appointment):
    """Тест ошибки при отмене уже отмененной записи"""
    _, _, appointment_repo = mock_repos
    
    cancelled_appointment = sample_appointment.model_copy(update={
        "status": AppointmentStatus.CANCELLED
    })
    appointment_repo.get_by_id.return_value = cancelled_appointment
    
    with pytest.raises(AppointmentCancellationError):
        service.cancel_appointment(1)

def test_mark_no_show_success(service, mock_repos, sample_appointment):
    """Тест успешной отметки неявки"""
    _, patient_repo, appointment_repo = mock_repos
    
    appointment_repo.get_by_id.return_value = sample_appointment
    appointment_repo.update.return_value = sample_appointment.model_copy(update={
        "status": AppointmentStatus.NO_SHOW,
        "fine_amount": service.FINE_FOR_NO_SHOW
    })
    patient_repo.increment_no_show.return_value = Patient(
        id=1,
        full_name="Петр Петров",
        birth_date=date(1990, 1, 1),
        phone="+79221234567",
        no_show_count=1
    )
    
    result = service.mark_no_show(1)
    
    assert result["fine"] == service.FINE_FOR_NO_SHOW
    assert result["patient_no_show_count"] == 1
    appointment_repo.update.assert_called_once()
    patient_repo.increment_no_show.assert_called_once_with(1)

def test_get_available_times_success(service, mock_repos, sample_doctor):
    """Тест получения доступных временных слотов"""
    doctor_repo, _, appointment_repo = mock_repos
    doctor_repo.get_by_id.return_value = sample_doctor
    appointment_repo.get_by_doctor_and_date.return_value = []  # Нет записей
    
    available_times = service.get_available_times(1, date(2026, 1, 15))
    
    # В понедельник с 9:00 до 18:00 с обедом 13:00-14:00
    # Должно быть: 9:00, 9:30, 10:00, 10:30, 11:00, 11:30, 12:00, 12:30, 14:00, 14:30, 15:00, 15:30, 16:00, 16:30, 17:00, 17:30
    assert len(available_times) == 16
    assert time(9, 0) in available_times
    assert time(13, 0) not in available_times  # Обед
    assert time(17, 30) in available_times

def test_get_available_times_with_existing_appointments(service, mock_repos, sample_doctor):
    """Тест получения доступных слотов с учетом существующих записей"""
    doctor_repo, _, appointment_repo = mock_repos
    doctor_repo.get_by_id.return_value = sample_doctor
    
    # Добавляем занятые слоты
    existing_appointments = [
        Appointment(
            id=1,
            doctor_id=1,
            patient_id=1,
            appointment_date=date(2026, 1, 15),
            appointment_time=time(10, 0),
            duration_minutes=30
        ),
        Appointment(
            id=2,
            doctor_id=1,
            patient_id=2,
            appointment_date=date(2026, 1, 15),
            appointment_time=time(14, 30),
            duration_minutes=30
        )
    ]
    appointment_repo.get_by_doctor_and_date.return_value = existing_appointments
    
    available_times = service.get_available_times(1, date(2026, 1, 15))
    
    # Проверяем, что занятые слоты отсутствуют
    assert time(10, 0) not in available_times
    assert time(14, 30) not in available_times
    # Проверяем, что другие слоты доступны
    assert time(9, 0) in available_times
    assert time(11, 0) in available_times