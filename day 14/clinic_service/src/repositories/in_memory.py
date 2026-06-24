from typing import List, Optional, Dict, Any
from datetime import date, datetime
from copy import deepcopy

from src.repositories.base import DoctorRepository, PatientRepository, AppointmentRepository
from src.domain.entities import Doctor, Patient, Appointment
from src.domain.enums import AppointmentStatus
from src.domain.exceptions import DoctorNotFoundError, PatientNotFoundError

class InMemoryDoctorRepository(DoctorRepository):
    def __init__(self):
        self._doctors: Dict[int, Doctor] = {}
        self._next_id = 1
    
    def add(self, doctor: Doctor) -> Doctor:
        doctor_id = self._next_id
        self._next_id += 1
        new_doctor = doctor.model_copy(update={"id": doctor_id})
        self._doctors[doctor_id] = new_doctor
        return new_doctor
    
    def get_by_id(self, doctor_id: int) -> Optional[Doctor]:
        return self._doctors.get(doctor_id)
    
    def get_by_specialization(self, specialization: str) -> List[Doctor]:
        return [d for d in self._doctors.values() if d.specialization.value == specialization]
    
    def update(self, doctor_id: int, data: Dict[str, Any]) -> Optional[Doctor]:
        doctor = self._doctors.get(doctor_id)
        if not doctor:
            return None
        updated_doctor = doctor.model_copy(update=data)
        self._doctors[doctor_id] = updated_doctor
        return updated_doctor
    
    def get_all(self) -> List[Doctor]:
        return list(self._doctors.values())

class InMemoryPatientRepository(PatientRepository):
    def __init__(self):
        self._patients: Dict[int, Patient] = {}
        self._next_id = 1
    
    def add(self, patient: Patient) -> Patient:
        patient_id = self._next_id
        self._next_id += 1
        new_patient = patient.model_copy(update={"id": patient_id})
        self._patients[patient_id] = new_patient
        return new_patient
    
    def get_by_id(self, patient_id: int) -> Optional[Patient]:
        return self._patients.get(patient_id)
    
    def get_by_phone(self, phone: str) -> Optional[Patient]:
        for patient in self._patients.values():
            if patient.phone == phone:
                return patient
        return None
    
    def update(self, patient_id: int, data: Dict[str, Any]) -> Optional[Patient]:
        patient = self._patients.get(patient_id)
        if not patient:
            return None
        updated_patient = patient.model_copy(update=data)
        self._patients[patient_id] = updated_patient
        return updated_patient
    
    def increment_no_show(self, patient_id: int) -> Optional[Patient]:
        patient = self._patients.get(patient_id)
        if not patient:
            return None
        updated_patient = patient.model_copy(update={"no_show_count": patient.no_show_count + 1})
        self._patients[patient_id] = updated_patient
        return updated_patient

class InMemoryAppointmentRepository(AppointmentRepository):
    def __init__(self):
        self._appointments: Dict[int, Appointment] = {}
        self._next_id = 1
    
    def add(self, appointment: Appointment) -> Appointment:
        appointment_id = self._next_id
        self._next_id += 1
        new_appointment = appointment.model_copy(update={"id": appointment_id})
        self._appointments[appointment_id] = new_appointment
        return new_appointment
    
    def get_by_id(self, appointment_id: int) -> Optional[Appointment]:
        return self._appointments.get(appointment_id)
    
    def get_by_doctor_and_date(self, doctor_id: int, date: date) -> List[Appointment]:
        return [
            a for a in self._appointments.values()
            if a.doctor_id == doctor_id and a.appointment_date == date and a.status == AppointmentStatus.SCHEDULED
        ]
    
    def get_by_patient(self, patient_id: int) -> List[Appointment]:
        return [a for a in self._appointments.values() if a.patient_id == patient_id]
    
    def get_by_date_range(self, start_date: date, end_date: date) -> List[Appointment]:
        return [
            a for a in self._appointments.values()
            if start_date <= a.appointment_date <= end_date
        ]
    
    def update(self, appointment_id: int, data: Dict[str, Any]) -> Optional[Appointment]:
        appointment = self._appointments.get(appointment_id)
        if not appointment:
            return None
        updated_appointment = appointment.model_copy(update=data)
        self._appointments[appointment_id] = updated_appointment
        return updated_appointment
    
    def get_active_appointments(self) -> List[Appointment]:
        return [
            a for a in self._appointments.values()
            if a.status == AppointmentStatus.SCHEDULED
        ]