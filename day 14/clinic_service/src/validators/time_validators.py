from datetime import time
from typing import List

def is_time_between(current_time: time, start_time: time, end_time: time) -> bool:
    """Проверяет, находится ли время между start_time и end_time"""
    current_seconds = current_time.hour * 3600 + current_time.minute * 60
    start_seconds = start_time.hour * 3600 + start_time.minute * 60
    end_seconds = end_time.hour * 3600 + end_time.minute * 60
    
    return start_seconds <= current_seconds < end_seconds

def get_time_slots(start_time: time, end_time: time, duration_minutes: int = 30) -> List[time]:
    """Генерирует список временных слотов между start_time и end_time"""
    slots = []
    current_seconds = start_time.hour * 3600 + start_time.minute * 60
    end_seconds = end_time.hour * 3600 + end_time.minute * 60
    
    while current_seconds + duration_minutes * 60 <= end_seconds:
        hours = current_seconds // 3600
        minutes = (current_seconds % 3600) // 60
        slots.append(time(hour=int(hours), minute=int(minutes)))
        current_seconds += duration_minutes * 60
    
    return slots

def is_overlapping(start1: time, end1: time, start2: time, end2: time) -> bool:
    """Проверяет, пересекаются ли два временных интервала"""
    start1_seconds = start1.hour * 3600 + start1.minute * 60
    end1_seconds = end1.hour * 3600 + end1.minute * 60
    start2_seconds = start2.hour * 3600 + start2.minute * 60
    end2_seconds = end2.hour * 3600 + end2.minute * 60
    
    return start1_seconds < end2_seconds and end1_seconds > start2_seconds