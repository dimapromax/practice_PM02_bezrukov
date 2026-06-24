from datetime import date, time, datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from src.domain.enums import DoctorSpecialization, AppointmentStatus, WeekDay

class WorkingHours(BaseModel):
    """Рабочие часы врача на конкретный день недели"""
    day: WeekDay
    start_time: time
    end_time: time
    lunch_start: Optional[time] = None
    lunch_end: Optional[time] = None
    
    @model_validator(mode='after')
    def validate_times(self):
        if self.start_time >= self.end_time:
            raise ValueError("Время начала должно быть раньше времени окончания")
        if self.lunch_start and self.lunch_end and self.lunch_start >= self.lunch_end:
            raise ValueError("Обеденное время указано некорректно")
        return self

class DoctorCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    specialization: DoctorSpecialization
    cabinet: str = Field(..., min_length=1, max_length=10)
    phone: str = Field(..., pattern=r'^\+?[0-9]{10,15}$')
    email: Optional[EmailStr] = None
    working_hours: Dict[WeekDay, WorkingHours]  # Расписание по дням недели
    
    @field_validator('working_hours')
    def validate_working_hours(cls, v):
        if not v:
            raise ValueError("Должно быть указано хотя бы одно рабочее время")
        return v

class Doctor(DoctorCreate):
    id: int
    created_at: datetime = Field(default_factory=datetime.now)

class PatientCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    birth_date: date
    phone: str = Field(..., pattern=r'^\+?[0-9]{10,15}$')
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    medical_notes: Optional[str] = None
    
    @field_validator('birth_date')
    def validate_birth_date(cls, v):
        if v > date.today():
            raise ValueError("Дата рождения не может быть в будущем")
        return v

class Patient(PatientCreate):
    id: int
    created_at: datetime = Field(default_factory=datetime.now)
    no_show_count: int = 0  # Количество пропусков без предупреждения

class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_id: int
    appointment_date: date
    appointment_time: time
    duration_minutes: int = Field(default=30, ge=15, le=120)
    notes: Optional[str] = None

class Appointment(AppointmentCreate):
    id: int
    status: AppointmentStatus = Field(default=AppointmentStatus.SCHEDULED)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    cancellation_reason: Optional[str] = None
    fine_amount: float = 0.0  # Штраф за позднюю отмену или пропуск
    
    @property
    def appointment_datetime(self) -> datetime:
        """Полная дата и время приема"""
        return datetime.combine(self.appointment_date, self.appointment_time)
    
    @property
    def end_time(self) -> time:
        """Время окончания приема"""
        minutes = self.duration_minutes
        total_seconds = self.appointment_time.hour * 3600 + self.appointment_time.minute * 60 + minutes * 60
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return time(hour=int(hours), minute=int(minutes))

class Notification(BaseModel):
    """Модель для уведомления"""
    recipient: str  # Телефон или email
    message: str
    send_time: datetime = Field(default_factory=datetime.now)
    sent: bool = False