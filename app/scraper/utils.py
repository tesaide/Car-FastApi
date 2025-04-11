import re
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from app.api.models import FuelType, TransmissionType


def parse_price(price_text: str) -> int:
    """
    Парсить текст ціни у числове значення
    
    Args:
        price_text: Текст ціни, наприклад "12 500 $" або "456 789 грн"
        
    Returns:
        Ціна в числовому форматі (в USD)
    """
    # Видаляємо всі нецифрові символи, крім крапок і ком
    digits_only = re.sub(r'[^\d.,]', '', price_text)
    
    # Конвертуємо у ціле число
    try:
        # Замінюємо коми на крапки, потім відкидаємо дробову частину
        price = int(float(digits_only.replace(',', '.')))
        
        # Якщо ціна вказана в гривнях, конвертуємо у долари (приблизний курс)
        if 'грн' in price_text.lower():
            # Припускаємо курс 1 USD = 40 грн (приблизно)
            price = int(price / 40)
            
        return price
    except (ValueError, TypeError):
        return 0


def parse_mileage(mileage_text: str) -> int:
    """
    Парсить текст пробігу у числове значення (кілометри)
    
    Args:
        mileage_text: Текст пробігу, наприклад "150 тис. км"
        
    Returns:
        Пробіг в кілометрах
    """
    # Видаляємо всі нецифрові символи
    digits_only = ''.join(filter(str.isdigit, mileage_text))
    
    try:
        mileage = int(digits_only)
        
        # Якщо пробіг вказаний у тисячах кілометрів
        if 'тис' in mileage_text:
            mileage *= 1000
            
        return mileage
    except (ValueError, TypeError):
        return 0


def parse_engine_info(engine_text: str) -> Tuple[float, FuelType]:
    """
    Парсить інформацію про двигун
    
    Args:
        engine_text: Текст інформації про двигун, наприклад "2.0 дизель"
        
    Returns:
        Кортеж (об'єм двигуна, тип палива)
    """
    # Отримуємо об'єм двигуна
    volume_match = re.search(r'(\d+(?:\.\d+)?)', engine_text)
    volume = float(volume_match.group(1)) if volume_match else 0.0
    
    # Визначаємо тип двигуна
    engine_type = FuelType.GASOLINE  # значення за замовчуванням
    
    lower_text = engine_text.lower()
    if 'газ' in lower_text:
        engine_type = FuelType.GAS
    elif 'дизель' in lower_text:
        engine_type = FuelType.DIESEL
    elif 'електро' in lower_text:
        engine_type = FuelType.ELECTRIC
    elif 'гібрид' in lower_text:
        if 'плагін' in lower_text:
            engine_type = FuelType.PLUGIN_HYBRID
        else:
            engine_type = FuelType.HYBRID
    
    return volume, engine_type


def parse_transmission(transmission_text: str) -> TransmissionType:
    """
    Парсить тип трансмісії
    
    Args:
        transmission_text: Текст типу трансмісії
        
    Returns:
        Тип трансмісії
    """
    lower_text = transmission_text.lower()
    
    if 'автомат' in lower_text:
        return TransmissionType.AUTOMATIC
    elif 'варіатор' in lower_text:
        return TransmissionType.VARIATOR
    elif 'робот' in lower_text:
        return TransmissionType.ROBOT
    elif 'напівавтомат' in lower_text:
        return TransmissionType.SEMI_AUTOMATIC
    else:
        return TransmissionType.MANUAL  # значення за замовчуванням


def clean_text(text: str) -> str:
    """
    Очищує текст від зайвих пробілів і переносів рядків
    
    Args:
        text: Вхідний текст
        
    Returns:
        Очищений текст
    """
    if not text:
        return ""
    
    # Замінюємо всі послідовності пробільних символів на один пробіл
    cleaned = re.sub(r'\s+', ' ', text)
    
    # Прибираємо пробіли з початку та кінця рядка
    return cleaned.strip()