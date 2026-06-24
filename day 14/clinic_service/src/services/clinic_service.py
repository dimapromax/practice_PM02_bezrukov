import logging
from datetime import date, time, datetime, timedelta
from typing import List, Optional, Dict, Any

from src.domain.entities import (
    Doctor, DoctorCreate, Patient, PatientCreate,
    Appointment, AppointmentCreate, WorkingHours
)
from src.domain.enums import AppointmentStatus, WeekDay
from src.domain.exceptions import (
    DoctorNotFoundError, PatientNotFoundError, AppointmentNotFoundError,
    ValidationError, AppointmentTimeUnavailableError, AppointmentLimitExceededError,
    AppointmentCancellationError, PatientHasNoShowError,
    InvalidWorkingHoursError, DuplicatePatientError, DomainError
)
from src.repositories.base import DoctorRepository, PatientRepository, AppointmentRepository
from src.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class ClinicService:
    """Сервис управления клиникой"""
    
    # Конфигурация
    MAX_APPOINTMENTS_PER_DAY = 10
    MIN_CANCELLATION_HOURS = 2  # Минимальное время для отмены (за 2 часа)
    FINE_FOR_LATE_CANCEL = 500.0  # Штраф за позднюю отмену
    FINE_FOR_NO_SHOW = 1000.0  # Штраф за неявку
    ALLOWED_NO_SHOWS_BEFORE_BLOCK = 2  # Максимальное количество пропусков до блокировки
    
    def __init__(
        self,
        doctor_repo: DoctorRepository,
        patient_repo: PatientRepository,
        appointment_repo: AppointmentRepository,
        notification_service: NotificationService
    ):
        self.doctor_repo = doctor_repo
        self.patient_repo = patient_repo
        self.appointment_repo = appointment_repo
        self.notification_service = notification_service
    
    # ========== Управление врачами ==========
    
    def add_doctor(self, doctor_data: dict) -> Doctor:
        """Добавление нового врача"""
        logger.info(f"Добавление врача: {doctor_data.get('full_name')}")
        try:
            doctor_create = DoctorCreate(**doctor_data)
        except Exception as e:
            logger.warning(f"Ошибка валидации данных врача: {e}")
            raise ValidationError(f"Некорректные данные врача: {e}")
        
        new_doctor = self.doctor_repo.add(doctor_create)
        logger.info(f"Врач добавлен: {new_doctor.full_name} (ID: {new_doctor.id})")
        return new_doctor
    
    def get_doctor(self, doctor_id: int) -> Doctor:
        """Получение информации о враче"""
        doctor = self.doctor_repo.get_by_id(doctor_id)
        if not doctor:
            raise DoctorNotFoundError(doctor_id)
        return doctor
    
    def get_doctors_by_specialization(self, specialization: str) -> List[Doctor]:
        """Получение списка врачей по специализации"""
        return self.doctor_repo.get_by_specialization(specialization)
    
    def get_all_doctors(self) -> List[Doctor]:
        """Получение списка всех врачей"""
        return self.doctor_repo.get_all()
    
    # ========== Управление пациентами ==========
    
    def register_patient(self, patient_data: dict) -> Patient:
        """Регистрация нового пациента"""
        logger.info(f"Регистрация пациента: {patient_data.get('full_name')}")
        try:
            patient_create = PatientCreate(**patient_data)
        except Exception as e:
            logger.warning(f"Ошибка валидации данных пациента: {e}")
            raise ValidationError(f"Некорректные данные пациента: {e}")
        
        # Проверка на дубликат по телефону
        existing_patient = self.patient_repo.get_by_phone(patient_create.phone)
        if existing_patient:
            raise DuplicatePatientError(patient_create.phone)
        
        new_patient = self.patient_repo.add(patient_create)
        logger.info(f"Пациент зарегистрирован: {new_patient.full_name} (ID: {new_patient.id})")
        return new_patient
    
    def get_patient(self, patient_id: int) -> Patient:
        """Получение информации о пациенте"""
        patient = self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise PatientNotFoundError(patient_id)
        return patient
    
    # ========== Управление записями ==========
    
    def _check_working_hours(self, doctor: Doctor, appointment_date: date, appointment_time: time) -> bool:
        """Проверка, входит ли время в рабочие часы врача"""
        week_day = WeekDay(appointment_date.strftime("%A").upper())
        if week_day not in doctor.working_hours:
            raise InvalidWorkingHoursError(doctor.id, f"{appointment_date} {appointment_time}")
        
        working_hours = doctor.working_hours[week_day]
        
        # Проверка времени начала
        if appointment_time < working_hours.start_time:
            raise InvalidWorkingHoursError(doctor.id, f"{appointment_time} (до начала работы)")
        
        # Проверка времени окончания (с учетом длительности)
        end_time = appointment_time
        minutes = 30  # Стандартная длительность приема
        total_seconds = appointment_time.hour * 3600 + appointment_time.minute * 60 + minutes * 60
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        end_time = time(hour=int(hours), minute=int(minutes))
        
        if end_time > working_hours.end_time:
            raise InvalidWorkingHoursError(doctor.id, f"{appointment_time} (после окончания работы)")
        
        # Проверка обеденного перерыва
        if working_hours.lunch_start and working_hours.lunch_end:
            if working_hours.lunch_start <= appointment_time < working_hours.lunch_end:
                raise InvalidWorkingHoursError(doctor.id, f"{appointment_time} (обеденный перерыв)")
            if working_hours.lunch_start < end_time <= working_hours.lunch_end:
                raise InvalidWorkingHoursError(doctor.id, f"{appointment_time} (затрагивает обеденный перерыв)")
        
        return True
    
    def _check_appointment_availability(self, doctor_id: int, appointment_date: date, appointment_time: time) -> bool:
        """Проверка доступности времени для записи"""
        # Получаем все записи на эту дату
        existing_appointments = self.appointment_repo.get_by_doctor_and_date(doctor_id, appointment_date)
        
        # Проверяем, не занято ли конкретное время
        for appointment in existing_appointments:
            # Проверяем пересечение по времени
            start1 = datetime.combine(appointment_date, appointment_time)
            end1 = datetime.combine(appointment_date, appointment_time) + timedelta(minutes=30)
            start2 = datetime.combine(appointment_date, appointment.appointment_time)
            end2 = datetime.combine(appointment_date, appointment.appointment_time) + timedelta(minutes=appointment.duration_minutes)
            
            if start1 < end2 and end1 > start2:
                raise AppointmentTimeUnavailableError(doctor_id, appointment_date, appointment_time)
        
        # Проверяем лимит записей на день
        if len(existing_appointments) >= self.MAX_APPOINTMENTS_PER_DAY:
            raise AppointmentLimitExceededError(doctor_id, appointment_date, self.MAX_APPOINTMENTS_PER_DAY)
        
        return True
    
    def _check_patient_eligibility(self, patient_id: int) -> bool:
        """Проверка, может ли пациент записаться на прием"""
        patient = self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise PatientNotFoundError(patient_id)
        
        if patient.no_show_count >= self.ALLOWED_NO_SHOWS_BEFORE_BLOCK:
            raise PatientHasNoShowError(patient_id)
        
        return True
    
    def create_appointment(self, appointment_data: dict) -> Appointment:
        """Создание записи на прием"""
        logger.info(f"Создание записи для пациента: {appointment_data.get('patient_id')}")
        
        try:
            appointment_create = AppointmentCreate(**appointment_data)
        except Exception as e:
            logger.warning(f"Ошибка валидации данных записи: {e}")
            raise ValidationError(f"Некорректные данные записи: {e}")
        
        # 1. Проверяем существование врача
        doctor = self.doctor_repo.get_by_id(appointment_create.doctor_id)
        if not doctor:
            raise DoctorNotFoundError(appointment_create.doctor_id)
        
        # 2. Проверяем существование пациента и его право на запись
        patient = self.patient_repo.get_by_id(appointment_create.patient_id)
        if not patient:
            raise PatientNotFoundError(appointment_create.patient_id)
        self._check_patient_eligibility(patient.id)
        
        # 3. Проверяем рабочие часы
        self._check_working_hours(doctor, appointment_create.appointment_date, appointment_create.appointment_time)
        
        # 4. Проверяем доступность времени
        self._check_appointment_availability(
            appointment_create.doctor_id,
            appointment_create.appointment_date,
            appointment_create.appointment_time
        )
        
        # 5. Создаем запись (транзакция)
        try:
            new_appointment = self.appointment_repo.add(appointment_create)
            logger.info(f"Запись создана: ID {new_appointment.id} для пациента {patient.full_name}")
            
            # 6. Отправляем уведомление
            self.notification_service.send_appointment_reminder(
                patient.phone,
                doctor.full_name,
                new_appointment.appointment_date.strftime("%d.%m.%Y"),
                new_appointment.appointment_time.strftime("%H:%M")
            )
            
            return new_appointment
        except Exception as e:
            logger.error(f"Ошибка при создании записи: {e}")
            raise DomainError(f"Не удалось создать запись: {e}") from e
    
    def cancel_appointment(self, appointment_id: int, reason: Optional[str] = None) -> dict:
        """Отмена записи на прием"""
        logger.info(f"Отмена записи ID: {appointment_id}")
        
        appointment = self.appointment_repo.get_by_id(appointment_id)
        if not appointment:
            raise AppointmentNotFoundError(appointment_id)
        
        if appointment.status != AppointmentStatus.SCHEDULED:
            raise AppointmentCancellationError(appointment_id, "Запись уже отменена или завершена")
        
        # Проверяем, можно ли отменить без штрафа (за 2 часа до приема)
        now = datetime.now()
        appointment_datetime = appointment.appointment_datetime
        hours_diff = (appointment_datetime - now).total_seconds() / 3600
        
        fine = 0.0
        if hours_diff < self.MIN_CANCELLATION_HOURS:
            fine = self.FINE_FOR_LATE_CANCEL
            logger.info(f"Назначен штраф {fine} за позднюю отмену (за {hours_diff:.1f} часов до приема)")
        
        # Транзакция обновления
        try:
            updated_appointment = self.appointment_repo.update(
                appointment_id,
                {
                    "status": AppointmentStatus.CANCELLED,
                    "cancellation_reason": reason,
                    "updated_at": now,
                    "fine_amount": fine
                }
            )
            
            if not updated_appointment:
                raise DomainError("Не удалось обновить запись")
            
            # Получаем данные пациента и врача для уведомления
            patient = self.patient_repo.get_by_id(appointment.patient_id)
            doctor = self.doctor_repo.get_by_id(appointment.doctor_id)
            
            if patient and doctor:
                self.notification_service.send_cancellation_confirmation(
                    patient.phone,
                    appointment.appointment_date.strftime("%d.%m.%Y"),
                    appointment.appointment_time.strftime("%H:%M")
                )
            
            logger.info(f"Запись {appointment_id} отменена. Штраф: {fine}")
            
            return {
                "appointment": updated_appointment,
                "fine": fine,
                "message": f"Запись отменена. {'Штраф: ' + str(fine) if fine > 0 else 'Штрафа нет.'}"
            }
        except Exception as e:
            logger.error(f"Ошибка при отмене записи: {e}")
            raise DomainError(f"Не удалось отменить запись: {e}") from e
    
    def mark_no_show(self, appointment_id: int) -> dict:
        """Отметка о неявке пациента"""
        logger.info(f"Отметка неявки для записи ID: {appointment_id}")
        
        appointment = self.appointment_repo.get_by_id(appointment_id)
        if not appointment:
            raise AppointmentNotFoundError(appointment_id)
        
        if appointment.status != AppointmentStatus.SCHEDULED:
            raise AppointmentCancellationError(appointment_id, "Запись уже отменена или завершена")
        
        # Транзакция
        try:
            # Обновляем статус записи
            updated_appointment = self.appointment_repo.update(
                appointment_id,
                {
                    "status": AppointmentStatus.NO_SHOW,
                    "updated_at": datetime.now(),
                    "fine_amount": self.FINE_FOR_NO_SHOW
                }
            )
            
            if not updated_appointment:
                raise DomainError("Не удалось обновить запись")
            
            # Увеличиваем счетчик неявок у пациента
            patient = self.patient_repo.increment_no_show(appointment.patient_id)
            if not patient:
                raise PatientNotFoundError(appointment.patient_id)
            
            logger.info(f"Запись {appointment_id} отмечена как неявка. Штраф: {self.FINE_FOR_NO_SHOW}")
            
            return {
                "appointment": updated_appointment,
                "fine": self.FINE_FOR_NO_SHOW,
                "patient_no_show_count": patient.no_show_count
            }
        except Exception as e:
            logger.error(f"Ошибка при отметке неявки: {e}")
            raise DomainError(f"Не удалось отметить неявку: {e}") from e
    
    def complete_appointment(self, appointment_id: int) -> Appointment:
        """Завершение приема"""
        logger.info(f"Завершение приема для записи ID: {appointment_id}")
        
        appointment = self.appointment_repo.get_by_id(appointment_id)
        if not appointment:
            raise AppointmentNotFoundError(appointment_id)
        
        if appointment.status != AppointmentStatus.SCHEDULED:
            raise AppointmentCancellationError(appointment_id, "Запись уже отменена или завершена")
        
        try:
            updated_appointment = self.appointment_repo.update(
                appointment_id,
                {
                    "status": AppointmentStatus.COMPLETED,
                    "updated_at": datetime.now()
                }
            )
            
            if not updated_appointment:
                raise DomainError("Не удалось обновить запись")
            
            logger.info(f"Прием {appointment_id} завершен")
            return updated_appointment
        except Exception as e:
            logger.error(f"Ошибка при завершении приема: {e}")
            raise DomainError(f"Не удалось завершить прием: {e}") from e
    
    def get_doctor_appointments(self, doctor_id: int, date: date) -> List[Appointment]:
        """Получение записей врача на конкретную дату"""
        doctor = self.doctor_repo.get_by_id(doctor_id)
        if not doctor:
            raise DoctorNotFoundError(doctor_id)
        
        return self.appointment_repo.get_by_doctor_and_date(doctor_id, date)
    
    def get_patient_appointments(self, patient_id: int) -> List[Appointment]:
        """Получение истории записей пациента"""
        patient = self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise PatientNotFoundError(patient_id)
        
        return self.appointment_repo.get_by_patient(patient_id)
    
    def get_available_times(self, doctor_id: int, appointment_date: date) -> List[time]:
        """Получение доступных временных слотов для врача на дату"""
        doctor = self.doctor_repo.get_by_id(doctor_id)
        if not doctor:
            raise DoctorNotFoundError(doctor_id)
        
        # Проверяем рабочие часы на этот день
        week_day = WeekDay(appointment_date.strftime("%A").upper())
        if week_day not in doctor.working_hours:
            return []
        
        working_hours = doctor.working_hours[week_day]
        
        # Получаем уже занятые слоты
        existing_appointments = self.appointment_repo.get_by_doctor_and_date(doctor_id, appointment_date)
        busy_times = set()
        for app in existing_appointments:
            busy_times.add(app.appointment_time)
            # Также блокируем время с учетом длительности приема
            current_time = app.appointment_time
            for _ in range(app.duration_minutes // 30):
                total_seconds = current_time.hour * 3600 + current_time.minute * 60 + 30 * 60
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                next_time = time(hour=int(hours), minute=int(minutes))
                busy_times.add(next_time)
                current_time = next_time
        
        # Генерируем все возможные слоты с шагом 30 минут
        available_times = []
        current_time = working_hours.start_time
        
        # Обеденный перерыв
        lunch_start = working_hours.lunch_start
        lunch_end = working_hours.lunch_end
        
        while current_time < working_hours.end_time:
            # Проверяем, не попадает ли время в обед
            if lunch_start and lunch_end and lunch_start <= current_time < lunch_end:
                # Перемещаем время на конец обеда
                current_time = lunch_end
                continue
            
            # Проверяем, не занято ли время
            if current_time not in busy_times:
                available_times.append(current_time)
            
            # Перемещаемся на 30 минут вперед
            total_seconds = current_time.hour * 3600 + current_time.minute * 60 + 30 * 60
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            current_time = time(hour=int(hours), minute=int(minutes))
        
        return available_times