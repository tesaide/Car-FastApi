import os
from pydantic import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Налаштування додатку"""
    
    # MongoDB налаштування
    MONGO_URL: str = os.getenv("MONGO_URL", "mongodb://mongodb:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "car_marketplace")
    
    # Загальні налаштування додатку
    APP_NAME: str = "Авто Маркетплейс API"
    APP_DESCRIPTION: str = "API для доступу до даних про автомобілі, зібрані з auto.ria.com"
    APP_VERSION: str = "0.1.0"
    
    # Налаштування логування
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILENAME: str = os.getenv("LOG_FILENAME", "logs/app.log")
    
    # Налаштування CORS
    CORS_ORIGINS: list = ["*"]  # У продакшені слід обмежити до конкретних URL
    
    # JWT налаштування (для бонусного завдання)
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key")  # Змінити у продакшені
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_MINUTES: int = 60 * 24  # 24 години
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Створюємо глобальний об'єкт налаштувань
settings = Settings()