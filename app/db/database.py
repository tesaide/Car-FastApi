from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger
import os
from typing import Optional

# Параметри підключення до MongoDB
MONGO_URL = os.getenv("MONGODB_URL", "mongodb://mongodb:27017")
MONGO_DB_NAME = os.getenv("MONGODB_DB_NAME", "car_marketplace")

# Глобальна змінна для зберігання клієнта бази даних
client: Optional[AsyncIOMotorClient] = None

async def get_database():
    """
    Функція-залежність для отримання об'єкту бази даних.
    Використовується з FastAPI Depends для ін'єкції залежностей.
    """
    if client is None:
        # Якщо клієнт не створений, автоматично ініціалізуємо його
        await init_db()
    
    # Повертаємо об'єкт бази даних
    return client[MONGO_DB_NAME]

async def init_db():
    """
    Ініціалізує підключення до бази даних MongoDB.
    """
    global client
    try:
        # Створюємо асинхронного клієнта MongoDB
        client = AsyncIOMotorClient(MONGO_URL)
        
        # Перевіряємо підключення
        await client.admin.command('ping')
        
        # Отримуємо базу даних
        db = client[MONGO_DB_NAME]
        
        # Створюємо індекси для колекції автомобілів
        # Індекс по URL для запобігання дублікатів
        await db.cars.create_index("url", unique=True)
        
        # Інші корисні індекси
        await db.cars.create_index("make")
        await db.cars.create_index("model")
        await db.cars.create_index("year")
        await db.cars.create_index("price")
        
        logger.info(f"Успішно підключено до MongoDB: {MONGO_URL}, база даних: {MONGO_DB_NAME}")
        
    except Exception as e:
        logger.error(f"Помилка підключення до MongoDB: {e}")
        raise

async def close_db():
    """
    Закриває підключення до бази даних MongoDB.
    """
    global client
    if client:
        client.close()
        client = None
        logger.info("Підключення до MongoDB закрито")