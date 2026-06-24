from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import date, time
from src.domain.entities import Doctor, Patient, Appointment
from src.domain.enums import AppointmentStatus

class DoctorRepository(ABC):
    @abstractmethod
    def add(self, doctor: Doctor) -> Doctor:
        pass
    
    @abstractmethod
    def get_by_id(self, doctor_id: int) -> Optional[Doctor]:
        pass
    
    @abstractmethod
    def get_by_specialization(self, specialization: str) -> List[Doctor]:
        pass
    
    @abstractmethod
    def update(self, doctor_id: int, data: Dict[str, Any]) -> Optional[Doctor]:
        pass
    
    @abstractmethod
    def get_all(self) -> List[Doctor]:
        pass

class PatientRepository(ABC):
    @abstractmethod
    def add(self, patient: Patient) -> Patient:
        pass
    
    @abstractmethod
    def get_by_id(self, patient_id: int) -> Optional[Patient]:
        pass
    
    @abstractmethod
    def get_by_phone(self, phone: str) -> Optional[Patient]:
        pass
    
    @abstractmethod
    def update(self, patient_id: int, data: Dict[str, Any]) -> Optional[Patient]:
        pass
    
    @abstractmethod
    def increment_no_show(self, patient_id: int) -> Optional[Patient]:
        pass

class AppointmentRepository(ABC):
    @abstractmethod
    def add(self, appointment: Appointment) -> Appointment:
        pass
    
    @abstractmethod
    def get_by_id(self, appointment_id: int) -> Optional[Appointment]:
        pass
    
    @abstractmethod
    def get_by_doctor_and_date(self, doctor_id: int, date: date) -> List[Appointment]:
        pass
    
    @abstractmethod
    def get_by_patient(self, patient_id: int) -> List[Appointment]:
        pass
    
    @abstractmethod
    def get_by_date_range(self, start_date: date, end_date: date) -> List[Appointment]:
        pass
    
    @abstractmethod
    def update(self, appointment_id: int, data: Dict[str, Any]) -> Optional[Appointment]:
        pass
    
    @abstractmethod
    def get_active_appointments(self) -> List[Appointment]:
        """Получить все активные (запланированные) записи"""
        pass