from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
import uvicorn
import os
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from app.db.database import get_database, init_db, close_db
from app.scraper.auto_ria import AutoRiaScraper

# Налаштування логування
os.makedirs("logs", exist_ok=True)
logger.add("logs/app.log", rotation="100 MB", level="INFO")

# Створення FastAPI додатку
app = FastAPI(
    title="Авто Маркетплейс API",
    description="API для доступу до даних про автомобілі, зібрані з auto.ria.com",
    version="0.1.0",
)

# Додавання CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # У продакшені варто обмежити
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтування статичних файлів
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
async def startup_event():
    """Функція, що виконується при запуску додатку"""
    logger.info("Запуск додатку...")
    await init_db()
    logger.info("База даних успішно ініціалізована")

@app.on_event("shutdown")
async def shutdown_event():
    """Функція, що виконується при зупинці додатку"""
    logger.info("Завершення роботи додатку...")
    await close_db()
    logger.info("З'єднання з базою даних закрито")

@app.get("/")
async def root():
    """Базовий маршрут для відображення HTML сторінки"""
    return FileResponse("app/static/index.html")

@app.get("/health")
async def health_check():
    """Ендпоінт для перевірки стану додатку"""
    return {"status": "ok"}

# Допоміжна функція для конвертації документу MongoDB у JSON з ObjectId
def convert_mongo_doc(doc):
    """Конвертує документ MongoDB у JSON-сумісний формат"""
    if doc.get("_id"):
        doc["id"] = str(doc.pop("_id"))
    return doc

# API для роботи з автомобілями
@app.get("/api/v1/cars")
async def get_cars(
    db = Depends(get_database), 
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: int = Query(-1),
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    make: Optional[str] = None,
):
    """Отримати список всіх автомобілів з пагінацією та фільтрацією"""
    try:
        # Переконаємося, що sort_order має допустиме значення (1 або -1)
        if sort_order not in [1, -1]:
            sort_order = -1  # Значення за замовчуванням

        # Створюємо фільтр на основі параметрів
        query = {}
        
        # Фільтр за ціною
        if min_price is not None or max_price is not None:
            query["price"] = {}
            if min_price is not None:
                query["price"]["$gte"] = min_price
            if max_price is not None:
                query["price"]["$lte"] = max_price
                
        # Фільтр за роком
        if min_year is not None or max_year is not None:
            query["year"] = {}
            if min_year is not None:
                query["year"]["$gte"] = min_year
            if max_year is not None:
                query["year"]["$lte"] = max_year
                
        # Фільтр за маркою
        if make:
            query["make"] = {"$regex": make, "$options": "i"}
        
        # Рахуємо загальну кількість документів
        total = await db.cars.count_documents(query)
        
        # Отримуємо документи з бази даних з пагінацією
        cursor = db.cars.find(query).sort(sort_by, sort_order).skip((page - 1) * limit).limit(limit)
        cars = [convert_mongo_doc(car) async for car in cursor]
        
        return {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total // limit) + (1 if total % limit > 0 else 0),
            "data": cars
        }
    except Exception as e:
        logger.error(f"Помилка при отриманні списку автомобілів: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/cars/{car_id}")
async def get_car(car_id: str, db = Depends(get_database)):
    """Отримати інформацію про конкретний автомобіль"""
    try:
        # Перевіряємо валідність ID
        if not ObjectId.is_valid(car_id):
            raise HTTPException(status_code=400, detail="Невірний формат ID")
        
        # Знаходимо автомобіль
        car = await db.cars.find_one({"_id": ObjectId(car_id)})
        
        if not car:
            raise HTTPException(status_code=404, detail="Автомобіль не знайдено")
        
        return convert_mongo_doc(car)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Помилка при отриманні автомобіля: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/cars/make/{make}")
async def get_cars_by_make(
    make: str, 
    db = Depends(get_database),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: int = Query(-1)
):
    """Отримати список автомобілів за маркою"""
    try:
        # Переконаємося, що sort_order має допустиме значення (1 або -1)
        if sort_order not in [1, -1]:
            sort_order = -1  # Значення за замовчуванням

        # Створюємо регулярний вираз для пошуку нечутливого до регістру
        query = {"make": {"$regex": f"^{make}$", "$options": "i"}}
        
        # Рахуємо загальну кількість документів
        total = await db.cars.count_documents(query)
        
        # Отримуємо документи з бази даних з пагінацією
        cursor = db.cars.find(query).sort(sort_by, sort_order).skip((page - 1) * limit).limit(limit)
        cars = [convert_mongo_doc(car) async for car in cursor]
        
        return {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total // limit) + (1 if total % limit > 0 else 0),
            "data": cars
        }
    except Exception as e:
        logger.error(f"Помилка при отриманні автомобілів за маркою: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/cars/year/{year}")
async def get_cars_by_year(
    year: int, 
    db = Depends(get_database),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: int = Query(-1)
):
    """Отримати список автомобілів за роком випуску"""
    try:
        # Переконаємося, що sort_order має допустиме значення (1 або -1)
        if sort_order not in [1, -1]:
            sort_order = -1  # Значення за замовчуванням

        # Створюємо запит
        query = {"year": year}
        
        # Рахуємо загальну кількість документів
        total = await db.cars.count_documents(query)
        
        # Отримуємо документи з бази даних з пагінацією
        cursor = db.cars.find(query).sort(sort_by, sort_order).skip((page - 1) * limit).limit(limit)
        cars = [convert_mongo_doc(car) async for car in cursor]
        
        return {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total // limit) + (1 if total % limit > 0 else 0),
            "data": cars
        }
    except Exception as e:
        logger.error(f"Помилка при отриманні автомобілів за роком: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/cars")
async def create_car(car_data: dict, db = Depends(get_database)):
    """Додати новий автомобіль в базу даних"""
    try:
        # Додаємо дату створення
        car_data["created_at"] = datetime.utcnow()
        
        # Перевіряємо обов'язкові поля
        required_fields = ["make", "model", "year", "price", "mileage", "engine_type", "engine_volume", "transmission", "location", "image_url", "url"]
        for field in required_fields:
            if field not in car_data:
                raise HTTPException(status_code=400, detail=f"Відсутнє обов'язкове поле: {field}")
        
        # Перевіряємо, чи вже існує автомобіль з таким URL
        existing_car = await db.cars.find_one({"url": car_data["url"]})
        if existing_car:
            raise HTTPException(status_code=400, detail="Автомобіль з таким URL вже існує")
        
        # Додаємо автомобіль
        result = await db.cars.insert_one(car_data)
        
        # Отримуємо доданий автомобіль
        inserted_car = await db.cars.find_one({"_id": result.inserted_id})
        
        return convert_mongo_doc(inserted_car)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Помилка при створенні автомобіля: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/cars/{car_id}")
async def update_car(car_id: str, car_data: dict, db = Depends(get_database)):
    """Оновити інформацію про автомобіль"""
    try:
        # Перевіряємо валідність ID
        if not ObjectId.is_valid(car_id):
            raise HTTPException(status_code=400, detail="Невірний формат ID")
        
        # Перевіряємо чи існує автомобіль
        existing_car = await db.cars.find_one({"_id": ObjectId(car_id)})
        if not existing_car:
            raise HTTPException(status_code=404, detail="Автомобіль не знайдено")
        
        # Додаємо дату оновлення
        car_data["updated_at"] = datetime.utcnow()
        
        # Оновлюємо автомобіль
        await db.cars.update_one({"_id": ObjectId(car_id)}, {"$set": car_data})
        
        # Отримуємо оновлений автомобіль
        updated_car = await db.cars.find_one({"_id": ObjectId(car_id)})
        
        return convert_mongo_doc(updated_car)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Помилка при оновленні автомобіля: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/cars/{car_id}")
async def delete_car(car_id: str, db = Depends(get_database)):
    """Видалити автомобіль"""
    try:
        # Перевіряємо валідність ID
        if not ObjectId.is_valid(car_id):
            raise HTTPException(status_code=400, detail="Невірний формат ID")
        
        # Перевіряємо чи існує автомобіль
        existing_car = await db.cars.find_one({"_id": ObjectId(car_id)})
        if not existing_car:
            raise HTTPException(status_code=404, detail="Автомобіль не знайдено")
        
        # Видаляємо автомобіль
        await db.cars.delete_one({"_id": ObjectId(car_id)})
        
        return {"status": "success", "message": "Автомобіль успішно видалено"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Помилка при видаленні автомобіля: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Запуск скрапера як фонової задачі
async def run_scraper_task(pages: int):
    """Запускає скрапер як фонову задачу"""
    scraper = AutoRiaScraper()
    await scraper.scrape_cars(pages)

@app.post("/api/v1/scraper/run")
async def run_scraper(background_tasks: BackgroundTasks, pages: int = Query(1, ge=1, le=10)):
    """Запускає скрапер у фоновому режимі для збору даних з auto.ria.com"""
    try:
        # Додаємо задачу скрапінгу у фоновий режим
        background_tasks.add_task(run_scraper_task, pages)
        
        return {
            "status": "success",
            "message": f"Скрапер запущено для обробки {pages} сторінок. Результати будуть доступні через API."
        }
    except Exception as e:
        logger.error(f"Помилка при запуску скрапера: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/cars/stats")
async def get_cars_stats(db = Depends(get_database)):
    """Отримати статистику по автомобілях в базі даних"""
    try:
        # Отримуємо загальну кількість автомобілів
        total_cars = await db.cars.count_documents({})
        
        # Агрегація для отримання середньої ціни
        avg_price_pipeline = [
            {"$match": {"price": {"$gt": 0}}},  # Фільтруємо лише автомобілі з ціною
            {"$group": {"_id": None, "avg_price": {"$avg": "$price"}}}
        ]
        avg_price_result = await db.cars.aggregate(avg_price_pipeline).to_list(1)
        avg_price = int(avg_price_result[0]["avg_price"]) if avg_price_result else 0
        
        # Агрегація для отримання середнього року
        avg_year_pipeline = [
            {"$match": {"year": {"$gt": 1900}}},  # Фільтруємо валідні роки
            {"$group": {"_id": None, "avg_year": {"$avg": "$year"}}}
        ]
        avg_year_result = await db.cars.aggregate(avg_year_pipeline).to_list(1)
        avg_year = int(avg_year_result[0]["avg_year"]) if avg_year_result else 0
        
        # Агрегація для отримання середнього пробігу
        avg_mileage_pipeline = [
            {"$match": {"mileage": {"$gt": 0}}},  # Фільтруємо валідний пробіг
            {"$group": {"_id": None, "avg_mileage": {"$avg": "$mileage"}}}
        ]
        avg_mileage_result = await db.cars.aggregate(avg_mileage_pipeline).to_list(1)
        avg_mileage = int(avg_mileage_result[0]["avg_mileage"]) if avg_mileage_result else 0
        
        # Агрегація для отримання популярних марок
        popular_makes_pipeline = [
            {"$group": {"_id": "$make", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        popular_makes = await db.cars.aggregate(popular_makes_pipeline).to_list(5)
        popular_makes = [{"make": item["_id"], "count": item["count"]} for item in popular_makes]
        
        return {
            "total_cars": total_cars,
            "avg_price": avg_price,
            "avg_year": avg_year,
            "avg_mileage": avg_mileage,
            "popular_makes": popular_makes
        }
    except Exception as e:
        logger.error(f"Помилка при отриманні статистики: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Запуск сервера для локальної розробки
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)