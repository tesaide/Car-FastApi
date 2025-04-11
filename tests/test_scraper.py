import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from bs4 import BeautifulSoup
import pytest_asyncio

from app.scraper.auto_ria import AutoRiaScraper

# Фікстура для створення скрапера
@pytest.fixture
def scraper():
    return AutoRiaScraper()

# Тестові HTML дані
@pytest.fixture
def sample_html():
    return """
    <div class="content-bar">
        <a class="m-link-ticket" href="https://auto.ria.com/uk/auto_bmw_x5_123.html"></a>
        <div class="ticket-photo">
            <img src="https://example.com/bmw_x5.jpg">
        </div>
        <div class="head-ticket">
            <span class="blue bold">BMW X5</span>
            2020
        </div>
        <div class="price-ticket" data-main-price="50000">
            50 000 $
        </div>
        <div class="definition-data">
            3.0 дизель • 25 тис. км • автомат • повний
        </div>
        <div class="region">
            Київ
        </div>
    </div>
    """

# Тестові детальні HTML дані
@pytest.fixture
def sample_details_html():
    return """
    <div class="auto-content">
        <div class="item_inner">
            <span>Місто</span>
            <strong>Київ</strong>
        </div>
        <div class="item_inner">
            <span>Привід</span>
            <strong>Повний</strong>
        </div>
    </div>
    """

# Тест ініціалізації скрапера
def test_scraper_init(scraper):
    assert scraper.base_url == "https://auto.ria.com/uk/legkovie/"
    assert scraper.session is None
    assert scraper.db is None

# Тест витягування місцезнаходження
def test_extract_location(scraper):
    assert scraper._extract_location("Київ") == "Київ"
    assert scraper._extract_location(" Львів ") == "Львів"
    assert scraper._extract_location("") == "Невідоме місцезнаходження"
    assert scraper._extract_location(None) == "Невідоме місцезнаходження"

# Тест витягування типу приводу
def test_extract_drive_type(scraper):
    assert scraper._extract_drive_type("повний привід") == "повний"
    assert scraper._extract_drive_type("4wd") == "повний"
    assert scraper._extract_drive_type("задній привід") == "задній"
    assert scraper._extract_drive_type("передній") == "передній"
    assert scraper._extract_drive_type("") == "передній"
    assert scraper._extract_drive_type(None) == "передній"

# Тест отримання даних про автомобілі
@pytest.mark.asyncio
async def test_get_car_links(scraper, sample_html, sample_details_html):
    # Підмінюємо метод _fetch_page, щоб він повертав наші тестові дані
    with patch.object(scraper, '_fetch_page', new_callable=AsyncMock) as mock_fetch:
        # Перший виклик повертає сторінку пошуку, другий - деталі авто
        mock_fetch.side_effect = [sample_html, sample_details_html]
        
        car_items = await scraper._get_car_links(1)
        
        # Перевіряємо результати
        assert len(car_items) == 1
        car = car_items[0]
        assert car["make"] == "BMW"
        assert car["model"] == "X5"
        assert car["year"] == 2020
        assert car["price"] == 50000
        assert car["mileage"] == 25000
        assert car["engine_type"] == "дизель"
        assert car["engine_volume"] == 3.0
        assert car["transmission"] == "автомат"
        assert car["drive_type"] == "повний"
        assert car["location"] == "Київ"
        assert car["image_url"] == "https://example.com/bmw_x5.jpg"
        assert car["url"] == "https://auto.ria.com/uk/auto_bmw_x5_123.html"

# Тест збереження автомобіля в базу даних
@pytest.mark.asyncio
async def test_save_car_to_db(scraper):
    # Підготовка тестових даних
    car_data = {
        "make": "BMW",
        "model": "X5",
        "year": 2020,
        "price": 50000,
        "mileage": 25000,
        "engine_type": "дизель",
        "engine_volume": 3.0,
        "transmission": "автомат",
        "drive_type": "повний",
        "location": "Київ",
        "image_url": "https://example.com/bmw_x5.jpg",
        "url": "https://auto.ria.com/uk/auto_bmw_x5_123.html"
    }
    
    # Підмінюємо методи для доступу до бази даних
    mock_db = MagicMock()
    mock_db.cars = AsyncMock()
    mock_db.cars.find_one = AsyncMock(return_value=None)  # Припускаємо, що автомобіля ще немає в базі
    mock_db.cars.insert_one = AsyncMock(return_value=MagicMock(inserted_id="test_id"))
    
    with patch.object(scraper, '_get_db', return_value=mock_db):
        result = await scraper._save_car_to_db(car_data)
        
        # Перевіряємо результат
        assert result is True
        mock_db.cars.find_one.assert_called_once_with({"url": car_data["url"]})
        mock_db.cars.insert_one.assert_called_once()
        
        # Перевіряємо, що дата створення додана
        assert "created_at" in mock_db.cars.insert_one.call_args[0][0]

# Тест оновлення існуючого автомобіля
@pytest.mark.asyncio
async def test_update_existing_car(scraper):
    # Підготовка тестових даних
    car_data = {
        "make": "BMW",
        "model": "X5",
        "year": 2020,
        "price": 50000,
        "mileage": 25000,
        "engine_type": "дизель",
        "engine_volume": 3.0,
        "transmission": "автомат",
        "drive_type": "повний",
        "location": "Київ",
        "image_url": "https://example.com/bmw_x5.jpg",
        "url": "https://auto.ria.com/uk/auto_bmw_x5_123.html"
    }
    
    # Підмінюємо методи для доступу до бази даних
    mock_db = MagicMock()
    mock_db.cars = AsyncMock()
    mock_db.cars.find_one = AsyncMock(return_value={"_id": "existing_id", **car_data})  # Автомобіль вже існує
    mock_db.cars.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    
    with patch.object(scraper, '_get_db', return_value=mock_db):
        result = await scraper._save_car_to_db(car_data)
        
        # Перевіряємо результат
        assert result is True
        mock_db.cars.find_one.assert_called_once_with({"url": car_data["url"]})
        mock_db.cars.update_one.assert_called_once()
        
        # Перевіряємо, що дата оновлення додана
        assert "updated_at" in mock_db.cars.update_one.call_args[0][1]["$set"]

# Тест основного методу скрапінгу
@pytest.mark.asyncio
async def test_scrape_cars(scraper):
    # Підмінюємо необхідні методи
    with patch.object(scraper, '_get_car_links', new_callable=AsyncMock) as mock_get_links, \
         patch.object(scraper, '_save_car_to_db', new_callable=AsyncMock) as mock_save_car, \
         patch.object(scraper, '_close_session', new_callable=AsyncMock) as mock_close_session:
        
        # Налаштування моків
        mock_get_links.return_value = [
            {"make": "BMW", "model": "X5"},
            {"make": "Audi", "model": "Q7"}
        ]
        mock_save_car.return_value = True
        
        # Викликаємо метод скрапінгу для 1 сторінки
        saved_count = await scraper.scrape_cars(1)
        
        # Перевіряємо результати
        assert saved_count == 2
        assert mock_get_links.call_count == 1
        assert mock_save_car.call_count == 2
        mock_close_session.assert_called_once()

# Тест обмеження кількості сторінок
@pytest.mark.asyncio
async def test_scrape_cars_limit_pages(scraper):
    with patch.object(scraper, '_get_car_links', new_callable=AsyncMock) as mock_get_links, \
         patch.object(scraper, '_save_car_to_db', new_callable=AsyncMock) as mock_save_car, \
         patch.object(scraper, '_close_session', new_callable=AsyncMock) as mock_close_session:
        
        # Налаштування моків
        mock_get_links.return_value = []
        mock_save_car.return_value = True
        
        # Перевірка обмеження мінімальної кількості сторінок
        await scraper.scrape_cars(0)  # Має стати 1
        assert mock_get_links.call_count == 1
        
        # Скидаємо лічильники викликів
        mock_get_links.reset_mock()
        
        # Перевірка обмеження максимальної кількості сторінок
        await scraper.scrape_cars(30)  # Має стати 20
        assert mock_get_links.call_count == 20