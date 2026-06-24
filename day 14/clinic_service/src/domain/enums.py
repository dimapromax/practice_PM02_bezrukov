from enum import Enum

class DoctorSpecialization(str, Enum):
    THERAPIST = "Терапевт"
    CARDIOLOGIST = "Кардиолог"
    NEUROLOGIST = "Невролог"
    DERMATOLOGIST = "Дерматолог"
    OPHTHALMOLOGIST = "Офтальмолог"
    SURGEON = "Хирург"
    PEDIATRICIAN = "Педиатр"

class AppointmentStatus(str, Enum):
    SCHEDULED = "Запланирован"
    COMPLETED = "Завершен"
    CANCELLED = "Отменен"
    NO_SHOW = "Не явился"

class WeekDay(str, Enum):
    MONDAY = "Понедельник"
    TUESDAY = "Вторник"
    WEDNESDAY = "Среда"
    THURSDAY = "Четверг"
    FRIDAY = "Пятница"
    SATURDAY = "Суббота"
    SUNDAY = "Воскресенье"
