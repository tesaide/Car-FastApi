import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
import asyncio
from bson import ObjectId
from datetime import datetime
import pytest_asyncio

from app.main import app
from app.db.database import get_database

# Фікстура для створення клієнта тестування
@pytest.fixture
def test_client():
    return TestClient(app)

# Фікстура для створення асинхронного клієнта
@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

# Фікстура для отримання тестової бази даних
@pytest_asyncio.fixture
async def test_db():
    db = await get_database()
    # Очищаємо тестову колекцію перед кожним тестом
    # (в реальному додатку краще використовувати окрему тестову базу)
    # await db.cars_test.delete_many({})
    yield db
    # Після тестів можна очистити тестову колекцію
    # await db.cars_test.delete_many({})

# Тестовий автомобіль для API тестів
@pytest.fixture
def test_car():
    return {
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
        "url": f"https://auto.ria.com/uk/auto_bmw_x5_{str(ObjectId())}.html"
    }

# Тести ендпоінту health-check
def test_health_check(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# Тести ендпоінту отримання списку автомобілів
@pytest.mark.asyncio
async def test_get_cars(async_client):
    response = await async_client.get("/api/v1/cars")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert "total_pages" in data

# Тести фільтрації автомобілів
@pytest.mark.asyncio
async def test_filter_cars(async_client):
    # Фільтрація за ціною
    response = await async_client.get("/api/v1/cars?min_price=10000&max_price=50000")
    assert response.status_code == 200
    data = response.json()
    for car in data["data"]:
        assert car["price"] >= 10000
        assert car["price"] <= 50000

    # Фільтрація за роком
    response = await async_client.get("/api/v1/cars?min_year=2015&max_year=2022")
    assert response.status_code == 200
    data = response.json()
    for car in data["data"]:
        assert car["year"] >= 2015
        assert car["year"] <= 2022

    # Фільтрація за маркою
    response = await async_client.get("/api/v1/cars?make=BMW")
    assert response.status_code == 200
    data = response.json()
    for car in data["data"]:
        assert "BMW" in car["make"]

# Тест отримання автомобіля за ID
@pytest.mark.asyncio
async def test_get_car_by_id(async_client, test_db):
    # Спершу отримаємо якийсь існуючий автомобіль
    cars = await test_db.cars.find().to_list(1)
    if cars:
        car_id = str(cars[0]["_id"])
        response = await async_client.get(f"/api/v1/cars/{car_id}")
        assert response.status_code == 200
        car = response.json()
        assert car["id"] == car_id
    else:
        # Пропускаємо тест, якщо немає автомобілів
        pytest.skip("Немає автомобілів для тестування")

# Тест з невалідним ID
@pytest.mark.asyncio
async def test_get_car_invalid_id(async_client):
    response = await async_client.get("/api/v1/cars/invalid_id")
    assert response.status_code == 400
    assert "Невірний формат ID" in response.json()["detail"]

# Тест отримання неіснуючого автомобіля
@pytest.mark.asyncio
async def test_get_nonexistent_car(async_client):
    fake_id = str(ObjectId())  # Створюємо валідний, але неіснуючий ID
    response = await async_client.get(f"/api/v1/cars/{fake_id}")
    assert response.status_code == 404
    assert "Автомобіль не знайдено" in response.json()["detail"]

# Тест отримання автомобілів за маркою
@pytest.mark.asyncio
async def test_get_cars_by_make(async_client):
    response = await async_client.get("/api/v1/cars/make/BMW")
    assert response.status_code == 200
    data = response.json()
    for car in data["data"]:
        assert car["make"].lower() == "bmw".lower()

# Тест отримання автомобілів за роком
@pytest.mark.asyncio
async def test_get_cars_by_year(async_client):
    response = await async_client.get("/api/v1/cars/year/2020")
    assert response.status_code == 200
    data = response.json()
    for car in data["data"]:
        assert car["year"] == 2020

# Тест створення автомобіля (потребує автентифікації)
@pytest.mark.asyncio
async def test_create_car(async_client, test_car):
    # Отримуємо токен для автентифікації
    auth_response = await async_client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "adminpassword"}
    )
    assert auth_response.status_code == 200
    token = auth_response.json()["access_token"]
    
    # Створюємо автомобіль
    headers = {"Authorization": f"Bearer {token}"}
    response = await async_client.post("/api/v1/cars", json=test_car, headers=headers)
    assert response.status_code == 200
    car = response.json()
    assert car["make"] == test_car["make"]
    assert car["model"] == test_car["model"]
    assert car["year"] == test_car["year"]
    
    # Прибираємо створений тестовий автомобіль
    car_id = car["id"]
    delete_response = await async_client.delete(f"/api/v1/cars/{car_id}", headers=headers)
    assert delete_response.status_code == 200

# Тест оновлення автомобіля (потребує автентифікації)
@pytest.mark.asyncio
async def test_update_car(async_client, test_db, test_car):
    # Отримуємо токен для автентифікації
    auth_response = await async_client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "adminpassword"}
    )
    assert auth_response.status_code == 200
    token = auth_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Спершу створюємо автомобіль для оновлення
    response = await async_client.post("/api/v1/cars", json=test_car, headers=headers)
    assert response.status_code == 200
    car = response.json()
    car_id = car["id"]
    
    # Оновлюємо автомобіль
    update_data = {"price": 60000, "mileage": 30000}
    update_response = await async_client.put(f"/api/v1/cars/{car_id}", json=update_data, headers=headers)
    assert update_response.status_code == 200
    updated_car = update_response.json()
    assert updated_car["price"] == 60000
    assert updated_car["mileage"] == 30000
    
    # Прибираємо створений тестовий автомобіль
    delete_response = await async_client.delete(f"/api/v1/cars/{car_id}", headers=headers)
    assert delete_response.status_code == 200

# Тест видалення автомобіля (потребує автентифікації)
@pytest.mark.asyncio
async def test_delete_car(async_client, test_db, test_car):
    # Отримуємо токен для автентифікації
    auth_response = await async_client.post(
        "/api/v1/auth/token",
        data={"username": "admin", "password": "adminpassword"}
    )
    assert auth_response.status_code == 200
    token = auth_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Спершу створюємо автомобіль для видалення
    response = await async_client.post("/api/v1/cars", json=test_car, headers=headers)
    assert response.status_code == 200
    car = response.json()
    car_id = car["id"]
    
    # Видаляємо автомобіль
    delete_response = await async_client.delete(f"/api/v1/cars/{car_id}", headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "success"
    
    # Перевіряємо, що автомобіль справді видалено
    get_response = await async_client.get(f"/api/v1/cars/{car_id}")
    assert get_response.status_code == 404