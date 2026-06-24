from datetime import date, time
from src.services.clinic_service import ClinicService
from src.services.notification_service import NotificationService
from src.repositories.in_memory import (
    InMemoryDoctorRepository,
    InMemoryPatientRepository,
    InMemoryAppointmentRepository
)
from src.domain.enums import DoctorSpecialization, WeekDay
from src.domain.entities import WorkingHours
from src.utils.logging_config import setup_logging
import logging

def main():
    # Настройка логирования
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Инициализация зависимостей (DI)
    doctor_repo = InMemoryDoctorRepository()
    patient_repo = InMemoryPatientRepository()
    appointment_repo = InMemoryAppointmentRepository()
    notification_service = NotificationService()
    
    service = ClinicService(
        doctor_repo,
        patient_repo,
        appointment_repo,
        notification_service
    )
    
    try:
        # 1. Добавляем врача
        logger.info("=" * 50)
        logger.info("ШАГ 1: Добавление врача")
        
        doctor = service.add_doctor({
            "full_name": "Анна Петровна Смирнова",
            "specialization": "Терапевт",
            "cabinet": "101",
            "phone": "+79111234567",
            "email": "anna.smirnova@clinic.ru",
            "working_hours": {
                "MONDAY": {
                    "day": "MONDAY",
                    "start_time": "09:00",
                    "end_time": "18:00",
                    "lunch_start": "13:00",
                    "lunch_end": "14:00"
                },
                "WEDNESDAY": {
                    "day": "WEDNESDAY",
                    "start_time": "09:00",
                    "end_time": "18:00",
                    "lunch_start": "13:00",
                    "lunch_end": "14:00"
                },
                "FRIDAY": {
                    "day": "FRIDAY",
                    "start_time": "09:00",
                    "end_time": "18:00",
                    "lunch_start": "13:00",
                    "lunch_end": "14:00"
                }
            }
        })
        logger.info(f"✅ Врач добавлен: {doctor.full_name} (ID: {doctor.id})")
        
        # 2. Регистрируем пациента
        logger.info("=" * 50)
        logger.info("ШАГ 2: Регистрация пациента")
        
        patient = service.register_patient({
            "full_name": "Иван Петрович Сидоров",
            "birth_date": "1990-05-15",
            "phone": "+79221234567",
            "email": "ivan.sidorov@mail.ru",
            "address": "ул. Ленина, д. 1, кв. 5"
        })
        logger.info(f"✅ Пациент зарегистрирован: {patient.full_name} (ID: {patient.id})")
        
        # 3. Получаем доступные слоты
        logger.info("=" * 50)
        logger.info("ШАГ 3: Проверка доступных слотов")
        
        appointment_date = date(2026, 1, 15)  # Понедельник
        available_times = service.get_available_times(doctor.id, appointment_date)
        logger.info(f"✅ Доступные слоты на {appointment_date}:")
        for t in available_times[:5]:  # Показываем первые 5
            logger.info(f"   - {t.strftime('%H:%M')}")
        logger.info(f"   ... и еще {len(available_times) - 5} слотов")
        
        # 4. Создаем запись
        logger.info("=" * 50)
        logger.info("ШАГ 4: Создание записи")
        
        appointment = service.create_appointment({
            "doctor_id": doctor.id,
            "patient_id": patient.id,
            "appointment_date": appointment_date.strftime("%Y-%m-%d"),
            "appointment_time": "10:00",
            "duration_minutes": 30,
            "notes": "Первичный прием"
        })
        logger.info(f"✅ Запись создана: ID {appointment.id} на {appointment.appointment_date} в {appointment.appointment_time}")
        
        # 5. Получаем записи врача на день
        logger.info("=" * 50)
        logger.info("ШАГ 5: Получение записей врача")
        
        doctor_appointments = service.get_doctor_appointments(doctor.id, appointment_date)
        logger.info(f"✅ Записей на {appointment_date}: {len(doctor_appointments)}")
        for app in doctor_appointments:
            patient_info = service.get_patient(app.patient_id)
            logger.info(f"   - {app.appointment_time.strftime('%H:%M')} - {patient_info.full_name}")
        
        # 6. Отменяем запись (для демонстрации)
        logger.info("=" * 50)
        logger.info("ШАГ 6: Отмена записи")
        
        cancel_result = service.cancel_appointment(appointment.id, "Изменились планы")
        logger.info(f"✅ {cancel_result['message']}")
        if cancel_result['fine'] > 0:
            logger.info(f"   Штраф: {cancel_result['fine']} руб.")
        
        # 7. Создаем еще одну запись и отмечаем неявку
        logger.info("=" * 50)
        logger.info("ШАГ 7: Отметка неявки")
        
        appointment2 = service.create_appointment({
            "doctor_id": doctor.id,
            "patient_id": patient.id,
            "appointment_date": appointment_date.strftime("%Y-%m-%d"),
            "appointment_time": "11:00",
            "duration_minutes": 30
        })
        logger.info(f"✅ Создана запись ID {appointment2.id} на 11:00")
        
        no_show_result = service.mark_no_show(appointment2.id)
        logger.info(f"✅ Отмечена неявка. Штраф: {no_show_result['fine']} руб.")
        logger.info(f"   Всего пропусков у пациента: {no_show_result['patient_no_show_count']}")
        
        # 8. Показываем историю пациента
        logger.info("=" * 50)
        logger.info("ШАГ 8: История записей пациента")
        
        patient_appointments = service.get_patient_appointments(patient.id)
        logger.info(f"✅ История пациента {patient.full_name}:")
        for app in patient_appointments:
            doctor_info = service.get_doctor(app.doctor_id)
            status_emoji = {
                "Запланирован": "📅",
                "Завершен": "✅",
                "Отменен": "❌",
                "Не явился": "🚫"
            }
            logger.info(f"   {status_emoji.get(app.status.value, '')} {app.appointment_date} {app.appointment_time} - {doctor_info.full_name} ({app.status.value})")
        
        logger.info("=" * 50)
        logger.info("🎉 Все операции выполнены успешно!")
        
    except Exception as e:
        logger.error(f"❌ Произошла ошибка: {e}", exc_info=True)

if __name__ == "__main__":
    main()