from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from typing import List, Optional
from loguru import logger
from bson import ObjectId
from datetime import datetime

from app.api.models import (
    Car, CarCreate, CarUpdate, PaginatedCars, 
    FuelType, TransmissionType, SearchParams
)
from app.db.database import get_database
from app.config import settings

router = APIRouter(tags=["cars"])

# Допоміжна функція для перетворення документа MongoDB у модель Pydantic
def convert_to_car_model(car_doc) -> Car:
    """Перетворює документ MongoDB у модель Car"""
    car_doc["id"] = str(car_doc.pop("_id"))
    return Car(**car_doc)

@router.get("/cars", response_model=PaginatedCars)
async def get_cars(
    db=Depends(get_database),
    page: int = Query(1, ge=1, description="Номер сторінки"),
    size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="Кількість елементів на сторінці"),
    sort_by: str = Query("created_at", description="Поле для сортування"),
    sort_order: int = Query(-1, ge=-1, le=1, description="Порядок сортування: -1 (спадання) або 1 (зростання)"),
):
    """
    Отримання списку всіх автомобілів з пагінацією
    """
    try:
        # Рахуємо загальну кількість записів
        total = await db.cars.count_documents({})
        
        # Отримуємо дані з пагінацією
        cursor = db.cars.find({}) \
            .sort(sort_by, sort_order) \
            .skip((page - 1) * size) \
            .limit(size)
        
        # Конвертуємо у список моделей
        cars = [convert_to_car_model(car) for car in await cursor.to_list(length=size)]
        
        return PaginatedCars(
            total=total,
            page=page,
            size=size,
            items=cars
        )
    except Exception as e:
        logger.error(f"Помилка при отриманні списку автомобілів: {e}")
        raise HTTPException(status_code=500, detail=f"Помилка сервера: {str(e)}")

@router.get("/cars/{car_id}", response_model=Car)
async def get_car(
    car_id: str = Path(..., description="ID автомобіля"),
    db=Depends(get_database)
):
    """
    Отримання інформації про конкретний автомобіль за ID
    """
    try:
        # Перевіряємо формат ID
        if not ObjectId.is_valid(car_id):
            raise HTTPException(status_code=400, detail="Невірний формат ID")
        
        # Шукаємо автомобіль
        car = await db.cars.find_one({"_id": ObjectId(car_id)})
        
        if not car:
            raise HTTPException(status_code=404, detail="Автомобіль не знайдено")
        
        return convert_to_car_model(car)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Помилка при отриманні автомобіля: {e}")
        raise HTTPException(status_code=500, detail=f"Помилка сервера: {str(e)}")

@router.get("/cars/make/{make}", response_model=PaginatedCars)
async def get_cars_by_make(
    make: str = Path(..., description="Марка автомобіля"),
    db=Depends(get_database),
    page: int = Query(1, ge=1, description="Номер сторінки"),
    size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="Кількість елементів на сторінці"),
    sort_by: str = Query("created_at", description="Поле для сортування"),
    sort_order: int = Query(-1, ge=-1, le=1, description="Порядок сортування: -1 (спадання) або 1 (зростання)"),
):
    """
    Отримання списку автомобілів за маркою
    """
    try:
        # Рахуємо загальну кількість записів за маркою
        total = await db.cars.count_documents({"make": {"$regex": f"^{make}$", "$options": "i"}})
        
        # Отримуємо дані з пагінацією
        cursor = db.cars.find({"make": {"$regex": f"^{make}$", "$options": "i"}}) \
            .sort(sort_by, sort_order) \
            .skip((page - 1) * size) \
            .limit(size)
        
        # Конвертуємо у список моделей
        cars = [convert_to_car_model(car) for car in await cursor.to_list(length=size)]
        
        return PaginatedCars(
            total=total,
            page=page,
            size=size,
            items=cars
        )
    except Exception as e:
        logger.error(f"Помилка при отриманні автомобілів за маркою: {e}")
        raise HTTPException(status_code=500, detail=f"Помилка сервера: {str(e)}")

@router.get("/cars/year/{year}", response_model=PaginatedCars)
async def get_cars_by_year(
    year: int = Path(..., ge=1900, le=datetime.now().year, description="Рік випуску"),
    db=Depends(get_database),
    page: int = Query(1, ge=1, description="Номер сторінки"),
    size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="Кількість елементів на сторінці"),
    sort_by: str = Query("created_at", description="Поле для сортування"),
    sort_order: int = Query(-1, ge=-1, le=1, description="Порядок сортування: -1 (спадання) або 1 (зростання)"),
):
    """
    Отримання списку автомобілів за роком випуску
    """
    try:
        # Рахуємо загальну кількість записів за роком
        total = await db.cars.count_documents({"year": year})
        
        # Отримуємо дані з пагінацією
        cursor = db.cars.find({"year": year}) \
            .sort(sort_by, sort_order) \
            .skip((page - 1) * size) \
            .limit(size)
        
        # Конвертуємо у список моделей
        cars = [convert_to_car_model(car) for car in await cursor.to_list(length=size)]
        
        return PaginatedCars(
            total=total,
            page=page,
            size=size,
            items=cars
        )
    except Exception as e:
        logger.error(f"Помилка при отриманні автомобілів за роком: {e}")
        raise HTTPException(status_code=500, detail=f"Помилка сервера: {str(e)}")

@router.post("/cars", response_model=Car, status_code=status.HTTP_201_CREATED)
async def create_car(
    car: CarCreate = Body(...),
    db=Depends(get_database)
):
    """
    Створення нового оголошення про автомобіль
    """
    try:
        # Підготовка даних для вставки
        car_data = car.dict()
        car_data["created_at"] = datetime.utcnow()
        car_data["updated_at"] = car_data["created_at"]
        
        # Вставка в БД
        result = await db.cars.insert_one(car_data)
        
        # Отримання створеного документа
        created_car = await db.cars.find_one({"_id": result.inserted_id})
        
        return convert_to_car_model(created_car)
    except Exception as e:
        logger.error(f"Помилка при створенні автомобіля: {e}")
        raise HTTPException(status_code=500, detail=f"Помилка сервера: {str(e)}")

@router.put("/cars/{car_id}", response_model=Car)
async def update_car(
    car_id: str = Path(..., description="ID автомобіля"),
    car_update: CarUpdate = Body(...),
    db=Depends(get_database)
):
    """
    Оновлення існуючого оголошення про автомобіль
    """
    try:
        # Перевіряємо формат ID
        if not ObjectId.is_valid(car_id):
            raise HTTPException(status_code=400, detail="Невірний формат ID")
        
        # Перевіряємо наявність автомобіля
        car = await db.cars.find_one({"_id": ObjectId(car_id)})
        if not car:
            raise HTTPException(status_code=404, detail="Автомобіль не знайдено")
        
        # Підготовка даних для оновлення
        update_data = car_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        if not update_data:
            # Якщо немає даних для оновлення, повертаємо існуючий автомобіль
            return convert_to_car_model(car)
        
        # Оновлення документа
        await db.cars.update_one(
            {"_id": ObjectId(car_id)},
            {"$set": update_data}
        )
        
        # Отримання оновленого документа
        updated_car = await db.cars.find_one({"_id": ObjectId(car_id)})
        
        return convert_to_car_model(updated_car)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Помилка при оновленні автомобіля: {e}")
        raise HTTPException(status_code=500, detail=f"Помилка сервера: {str(e)}")

@router.delete("/cars/{car_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_car(
    car_id: str = Path(..., description="ID автомобіля"),
    db=Depends(get_database)
):
    """
    Видалення оголошення про автомобіль
    """
    try:
        # Перевіряємо формат ID
        if not ObjectId.is_valid(car_id):
            raise HTTPException(status_code=400, detail="Невірний формат ID")
        
        # Перевіряємо наявність автомобіля
        car = await db.cars.find_one({"_id": ObjectId(car_id)})
        if not car:
            raise HTTPException(status_code=404, detail="Автомобіль не знайдено")
        
        # Видалення документа
        await db.cars.delete_one({"_id": ObjectId(car_id)})
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Помилка при видаленні автомобіля: {e}")
        raise HTTPException(status_code=500, detail=f"Помилка сервера: {str(e)}")

# Додаткові ендпоінти для розширеного пошуку (бонусне завдання)
@router.post("/cars/search", response_model=PaginatedCars)
async def search_cars(
    search_params: SearchParams = Body(...),
    db=Depends(get_database),
    page: int = Query(1, ge=1, description="Номер сторінки"),
    size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="Кількість елементів на сторінці"),
    sort_by: str = Query("created_at", description="Поле для сортування"),
    sort_order: int = Query(-1, ge=-1, le=1, description="Порядок сортування: -1 (спадання) або 1 (зростання)"),
):
    """
    Розширений пошук автомобілів за різними параметрами
    """
    try:
        # Будуємо фільтр для пошуку
        filter_query = {}
        
        # Додаємо фільтри до запиту, якщо вони вказані
        if search_params.make:
            filter_query["make"] = {"$regex": search_params.make, "$options": "i"}
        
        if search_params.model:
            filter_query["model"] = {"$regex": search_params.model, "$options": "i"}
        
        year_filter = {}
        if search_params.year_from:
            year_filter["$gte"] = search_params.year_from
        if search_params.year_to:
            year_filter["$lte"] = search_params.year_to
        if year_filter:
            filter_query["year"] = year_filter
        
        price_filter = {}
        if search_params.price_from:
            price_filter["$gte"] = search_params.price_from
        if search_params.price_to:
            price_filter["$lte"] = search_params.price_to
        if price_filter:
            filter_query["price"] = price_filter
        
        mileage_filter = {}
        if search_params.mileage_from:
            mileage_filter["$gte"] = search_params.mileage_from
        if search_params.mileage_to:
            mileage_filter["$lte"] = search_params.mileage_to
        if mileage_filter:
            filter_query["mileage"] = mileage_filter
        
        if search_params.engine_type:
            filter_query["engine_type"] = search_params.engine_type
        
        if search_params.transmission_type:
            filter_query["transmission_type"] = search_params.transmission_type
        
        if search_params.location:
            filter_query["location"] = {"$regex": search_params.location, "$options": "i"}
        
        # Рахуємо загальну кількість записів за фільтром
        total = await db.cars.count_documents(filter_query)
        
        # Отримуємо дані з пагінацією
        cursor = db.cars.find(filter_query) \
            .sort(sort_by, sort_order) \
            .skip((page - 1) * size) \
            .limit(size)
        
        # Конвертуємо у список моделей
        cars = [convert_to_car_model(car) for car in await cursor.to_list(length=size)]
        
        return PaginatedCars(
            total=total,
            page=page,
            size=size,
            items=cars
        )
    except Exception as e:
        logger.error(f"Помилка при пошуку автомобілів: {e}")
        raise HTTPException(status_code=500, detail=f"Помилка сервера: {str(e)}")