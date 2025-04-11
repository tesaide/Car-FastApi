import aiohttp
import asyncio
from bs4 import BeautifulSoup
from loguru import logger
from datetime import datetime
from typing import Dict, List, Any, Optional
import re
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.database import get_database

class AutoRiaScraper:
    """
    Скрапер для збору даних про автомобілі з сайту auto.ria.com
    """
    
    def __init__(self):
        self.base_url = "https://auto.ria.com/uk/legkovie/"
        self.session = None
        self.db = None
    
    async def _get_db(self):
        """Отримує з'єднання з базою даних"""
        if self.db is None:
            self.db = await get_database()
        return self.db
    
    async def _init_session(self):
        """Ініціалізує асинхронну сесію"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
            )
        return self.session
    
    async def _close_session(self):
        """Закриває асинхронну сесію"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _fetch_page(self, url: str) -> Optional[str]:
        """Отримує HTML-контент сторінки"""
        session = await self._init_session()
        try:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.error(f"Помилка запиту до {url}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Помилка при отриманні сторінки {url}: {e}")
            return None
    
    async def _get_car_links(self, page_num: int) -> List[Dict[str, Any]]:
        """
        Отримує дані про автомобілі з сторінки пошуку
        Повертає список словників з базовою інформацією та посиланнями
        """
        url = f"{self.base_url}?page={page_num}"
        logger.info(f"Отримання списку автомобілів зі сторінки: {url}")
        html = await self._fetch_page(url)
        
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        car_items = []
        
        # Пошук блоків з автомобілями (content-bar)
        car_blocks = soup.select('div.content-bar')
        
        for car_block in car_blocks:
            try:
                # Отримуємо URL оголошення
                link_elem = car_block.select_one('a.m-link-ticket')
                car_url = link_elem.get('href') if link_elem else None
                
                if not car_url:
                    continue
                
                # Отримуємо URL зображення
                photo_elem = car_block.select_one('div.ticket-photo img')
                image_url = photo_elem.get('src') if photo_elem else None
                
                if not image_url and photo_elem:
                    # Перевіряємо альтернативні атрибути для зображення
                    image_url = photo_elem.get('data-src') or photo_elem.get('data-srcset')
                
                # Отримуємо заголовок (марка, модель)
                title_elem = car_block.select_one('div.head-ticket span.blue.bold')
                title_text = title_elem.text.strip() if title_elem else ""
                
                # Розділяємо заголовок на марку і модель
                parts = title_text.split(' ', 1)
                make = parts[0] if parts else ""
                model = parts[1] if len(parts) > 1 else ""
                
                # Отримуємо рік
                year_elem = car_block.select_one('div.head-ticket')
                year_text = year_elem.text if year_elem else ""
                year_match = re.search(r'\b(19|20)\d{2}\b', year_text)
                year = int(year_match.group(0)) if year_match else 0
                
                # Отримуємо ціну
                price_elem = car_block.select_one('div.price-ticket')
                price = 0
                if price_elem:
                    price_attr = price_elem.get('data-main-price')
                    if price_attr:
                        price = int(price_attr)
                    else:
                        price_text = price_elem.text.strip()
                        price_digits = ''.join(filter(str.isdigit, price_text))
                        price = int(price_digits) if price_digits else 0
                
                # Отримуємо інформацію про двигун
                engine_elem = car_block.select_one('div.definition-data')
                engine_text = engine_elem.text.strip() if engine_elem else ""
                
                # Шукаємо об'єм двигуна
                engine_volume_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:л|AT|MT)', engine_text)
                engine_volume = float(engine_volume_match.group(1)) if engine_volume_match else 0.0
                
                # Визначаємо тип двигуна
                engine_type = "бензин"  # За замовчуванням
                if "дизель" in engine_text.lower():
                    engine_type = "дизель"
                elif "газ" in engine_text.lower():
                    engine_type = "газ"
                elif "електро" in engine_text.lower():
                    engine_type = "електро"
                elif "гібрид" in engine_text.lower():
                    engine_type = "гібрид"
                
                # Визначаємо тип трансмісії
                transmission = "механіка"  # За замовчуванням
                if "автомат" in engine_text.lower():
                    transmission = "автомат"
                elif "AT" in engine_text:
                    transmission = "автомат"
                elif "MT" in engine_text:
                    transmission = "механіка"
                
                # Отримуємо пробіг
                mileage_match = re.search(r'(\d+)\s*тис\.?\s*км', engine_text)
                mileage = int(mileage_match.group(1)) * 1000 if mileage_match else 0
                
                # Отримуємо розташування
                location_elem = car_block.select_one('div.region')
                location = location_elem.text.strip() if location_elem else "Невідоме місцезнаходження"
                
                # Формуємо дані про автомобіль
                car_data = {
                    "make": make,
                    "model": model,
                    "year": year,
                    "price": price,
                    "mileage": mileage,
                    "engine_type": engine_type,
                    "engine_volume": engine_volume,
                    "transmission": transmission,
                    "location": location,
                    "image_url": image_url,
                    "url": car_url
                }
                
                car_items.append(car_data)
                logger.info(f"Знайдено автомобіль: {make} {model} {year}")
                
            except Exception as e:
                logger.error(f"Помилка при обробці картки автомобіля: {e}")
                continue
        
        logger.info(f"Знайдено {len(car_items)} автомобілів на сторінці {page_num}")
        return car_items
    
    async def _save_car_to_db(self, car_data: Dict[str, Any]) -> bool:
        """Зберігає дані про автомобіль в базу даних"""
        db = await self._get_db()
        
        try:
            # Додаємо дату створення запису
            car_data["created_at"] = datetime.utcnow()
            
            # Перевіряємо наявність дублікатів за URL
            existing_car = await db.cars.find_one({"url": car_data["url"]})
            
            if existing_car:
                # Оновлюємо існуючий запис
                car_data["updated_at"] = datetime.utcnow()
                result = await db.cars.update_one(
                    {"url": car_data["url"]},
                    {"$set": car_data}
                )
                logger.info(f"Оновлено існуючий запис: {car_data['make']} {car_data['model']} {car_data['year']}")
                return result.modified_count > 0
            else:
                # Створюємо новий запис
                result = await db.cars.insert_one(car_data)
                logger.info(f"Додано новий автомобіль: {car_data['make']} {car_data['model']} {car_data['year']}")
                return result.inserted_id is not None
                
        except Exception as e:
            logger.error(f"Помилка при збереженні даних в базу: {e}")
            return False
    
    async def scrape_cars(self, pages: int = 5) -> int:
        """
        Основний метод для скрапінгу автомобілів з auto.ria.com
        
        Args:
            pages: Кількість сторінок для скрапінгу
            
        Returns:
            Кількість успішно збережених автомобілів
        """
        if pages < 1:
            pages = 1
        if pages > 20:
            # Обмежуємо кількість сторінок для запобігання надмірному навантаженню на сайт
            pages = 20
        
        saved_count = 0
        
        try:
            logger.info(f"Початок скрапінгу {pages} сторінок з auto.ria.com")
            
            # Обробляємо вказану кількість сторінок
            for page in range(1, pages + 1):
                logger.info(f"Обробка сторінки {page} з {pages}")
                
                # Отримуємо дані про автомобілі зі сторінки пошуку
                car_items = await self._get_car_links(page)
                
                # Зберігаємо кожен автомобіль в базу даних
                for i, car_data in enumerate(car_items):
                    logger.info(f"Обробка автомобіля {i+1}/{len(car_items)}: {car_data['make']} {car_data['model']}")
                    
                    success = await self._save_car_to_db(car_data)
                    if success:
                        saved_count += 1
                
                # Затримка між запитами для дотримання етики скрапінгу
                await asyncio.sleep(2)
                
            logger.info(f"Скрапінг завершено. Збережено {saved_count} автомобілів.")
            
        except Exception as e:
            logger.error(f"Помилка при скрапінгу: {e}")
        
        finally:
            # Закриваємо сесію після завершення
            await self._close_session()
            
        return saved_count