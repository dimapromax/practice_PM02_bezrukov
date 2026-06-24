class DomainError(Exception):
    """Базовое исключение для доменных ошибок."""
    pass

class DoctorNotFoundError(DomainError):
    def __init__(self, doctor_id: int):
        super().__init__(f"Врач с ID '{doctor_id}' не найден.")

class PatientNotFoundError(DomainError):
    def __init__(self, patient_id: int):
        super().__init__(f"Пациент с ID '{patient_id}' не найден.")

class AppointmentNotFoundError(DomainError):
    def __init__(self, appointment_id: int):
        super().__init__(f"Запись с ID '{appointment_id}' не найдена.")

class ValidationError(DomainError):
    pass

class AppointmentTimeUnavailableError(DomainError):
    def __init__(self, doctor_id: int, date, time):
        super().__init__(f"Время {date} {time} для врача ID '{doctor_id}' уже занято.")

class AppointmentLimitExceededError(DomainError):
    def __init__(self, doctor_id: int, date, max_limit: int):
        super().__init__(f"Превышен лимит записей ({max_limit}) для врача ID '{doctor_id}' на {date}.")

class AppointmentCancellationError(DomainError):
    def __init__(self, appointment_id: int, reason: str):
        super().__init__(f"Невозможно отменить запись ID '{appointment_id}': {reason}")

class PatientHasNoShowError(DomainError):
    def __init__(self, patient_id: int):
        super().__init__(f"Пациент ID '{patient_id}' имеет неоплаченные пропуски.")

class InvalidWorkingHoursError(DomainError):
    def __init__(self, doctor_id: int, time):
        super().__init__(f"Время {time} не входит в рабочие часы врача ID '{doctor_id}'.")

class DuplicatePatientError(DomainError):
    def __init__(self, phone: str):
        super().__init__(f"Пациент с телефоном '{phone}' уже зарегистрирован.")