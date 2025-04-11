from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TransmissionType(str, Enum):
    """Типи трансмісії автомобіля"""
    MANUAL = "механіка"
    AUTOMATIC = "автомат"
    SEMI_AUTOMATIC = "напівавтомат"
    VARIATOR = "варіатор"
    ROBOT = "робот"


class FuelType(str, Enum):
    """Типи палива автомобіля"""
    GASOLINE = "бензин"
    DIESEL = "дизель"
    GAS = "газ"
    ELECTRIC = "електро"
    HYBRID = "гібрид"
    PLUGIN_HYBRID = "гібрид плагін"


class CarBase(BaseModel):
    """Базова модель для даних про автомобіль"""
    make: str = Field(..., description="Марка автомобіля")
    model: str = Field(..., description="Модель автомобіля")
    year: int = Field(..., description="Рік випуску", ge=1900, le=datetime.now().year)
    price: int = Field(..., description="Ціна у доларах США", ge=0)
    mileage: int = Field(..., description="Пробіг у кілометрах", ge=0)
    engine_type: FuelType = Field(..., description="Тип палива")
    engine_volume: float = Field(..., description="Об'єм двигуна у літрах", ge=0)
    transmission: TransmissionType = Field(..., description="Тип трансмісії")
    location: str = Field(..., description="Місцезнаходження")
    image_url: HttpUrl = Field(..., description="URL зображення автомобіля")
    url: HttpUrl = Field(..., description="URL оголошення")


class CarCreate(CarBase):
    """Модель для створення нового автомобіля"""
    pass


class CarUpdate(BaseModel):
    """Модель для оновлення даних про автомобіль"""
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = Field(None, ge=1900, le=datetime.now().year)
    price: Optional[int] = Field(None, ge=0)
    mileage: Optional[int] = Field(None, ge=0)
    engine_type: Optional[FuelType] = None
    engine_volume: Optional[float] = Field(None, ge=0)
    transmission: Optional[TransmissionType] = None
    location: Optional[str] = None
    image_url: Optional[HttpUrl] = None
    url: Optional[HttpUrl] = None


class Car(CarBase):
    """Модель автомобіля з додатковими полями від бази даних"""
    id: str = Field(..., description="ID автомобіля в базі даних")
    created_at: datetime = Field(..., description="Дата створення запису")
    updated_at: Optional[datetime] = Field(None, description="Дата останнього оновлення")

    class Config:
        orm_mode = True


class PaginatedCars(BaseModel):
    """Пагінований список автомобілів"""
    page: int = Field(..., description="Поточна сторінка")
    limit: int = Field(..., description="Кількість елементів на сторінці")
    total: int = Field(..., description="Загальна кількість автомобілів")
    total_pages: int = Field(..., description="Загальна кількість сторінок")
    data: List[Car] = Field(..., description="Список автомобілів")