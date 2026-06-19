import pytest
from datetime import date, datetime

from src.uow.unit_of_work import UnitOfWork
from src.services.pricing_service import PricingService
from src.services.booking_service import BookingService
from src.services.waitlist_service import WaitlistService
from src.domain.models import Hotel, Room, Booking, BookingStatus


@pytest.fixture
def uow():
    """Unit of Work для тестов"""
    return UnitOfWork()


@pytest.fixture
def pricing_service():
    """Pricing Service для тестов"""
    return PricingService()


@pytest.fixture
def booking_service(uow, pricing_service):
    """Booking Service для тестов"""
    return BookingService(uow, pricing_service)


@pytest.fixture
def waitlist_service(uow, booking_service):
    """Waitlist Service для тестов"""
    return WaitlistService(uow, booking_service)


@pytest.fixture
def test_hotel(uow):
    """Тестовый отель"""
    hotel = Hotel(
        id=None,
        name="Test Hotel",
        address="123 Test St",
        phone="+7 999 123-45-67",
        rating=4.5
    )
    saved = uow.hotels.add(hotel)
    uow.commit()
    return saved


@pytest.fixture
def test_rooms(uow, test_hotel):
    """Тестовые номера"""
    rooms = []
    for i in range(1, 4):
        room = Room(
            id=None,
            hotel_id=test_hotel.id,
            number=f"{i}01",
            capacity=2 if i < 3 else 4,
            price_per_night=100.0 + i * 50,
            room_type="standard" if i < 3 else "deluxe"
        )
        saved = uow.rooms.add(room)
        rooms.append(saved)

    uow.commit()
    return rooms