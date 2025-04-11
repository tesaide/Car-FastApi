# Auto Marketplace API

API для доступу до даних про автомобілі, зібрані з auto.ria.com. Проєкт включає веб-скрапер для збору даних про автомобілі, REST API для роботи з цими даними та простий веб-інтерфейс для перегляду.


## Технології

- **Python 3.8+**
- **FastAPI** - для створення API
- **MongoDB** - для зберігання даних
- **Motor** - асинхронний драйвер MongoDB для Python
- **BeautifulSoup4** + **aiohttp** - для скрапінгу даних
- **Docker** + **Docker Compose** - для контейнеризації
- **Bootstrap** - для веб-інтерфейсу

## Структура проєкту

```
app/
├── api/               # API ендпоінти та моделі
├── db/                # Налаштування бази даних
├── scraper/           # Веб-скрапер для auto.ria.com
├── static/            # Статичні файли (CSS, JS, HTML)
├── config.py          # Конфігурація додатку
└── main.py            # Головний файл FastAPI додатку
logs/                  # Логи додатку
tests/                 # Тести
compose.yaml           # Конфігурація Docker
Dockerfile             # Інструкції для збірки Docker-образу
requirements.txt       # Залежності Python
```

## Налаштування та запуск

### Запуск за допомогою Docker Compose

1. cd car_marketplace_api

2. Запустіть контейнери:
   
   docker-compose up -d
  
3. Відкрийте у браузері: http://localhost:8000/
   Зверху справа є кнопка для переходу в Api Docs


## Документація по API

### Основні ендпоінти

| Ендпоінт                   | Метод | Опис |
|----------                  |-------|------|
| `/api/v1/cars`             | GET   | Отримати список автомобілів з пагінацією та фільтрацією |
| `/api/v1/cars/{car_id}`    | GET   | Отримати інформацію про конкретний автомобіль |
| `/api/v1/cars/make/{make}` | GET   | Отримати автомобілі за маркою |
| `/api/v1/cars/year/{year}` | GET   | Отримати автомобілі за роком випуску |
| `/api/v1/cars`             | POST  | Додати новий автомобіль |
| `/api/v1/cars/{car_id}`    | PUT   | Оновити інформацію про автомобіль |
| `/api/v1/cars/{car_id}`    | DELETE| Видалити автомобіль |
| `/api/v1/scraper/run`      | POST  | Запустити скрапер |
| `/api/v1/cars/stats`       | GET   | Отримати статистику по автомобілях |

### Параметри запитів

#### GET /api/v1/cars

| Параметр | Тип | Опис | Приклад |
|----------|-----|------|---------|
| `page` | int | Номер сторінки (≥1) | `?page=2` |
| `limit` | int | К-сть елементів на сторінці (1-100) | `?limit=20` |
| `sort_by` | string | Поле для сортування | `?sort_by=price` |
| `sort_order` | int | Порядок сортування (1 або -1) | `?sort_order=-1` |
| `min_price` | int | Мінімальна ціна | `?min_price=5000` |
| `max_price` | int | Максимальна ціна | `?max_price=20000` |
| `min_year` | int | Мінімальний рік | `?min_year=2015` |
| `max_year` | int | Максимальний рік | `?max_year=2020` |
| `make` | string | Марка автомобіля | `?make=BMW` |

## Приклади API-запитів

### Отримання списку автомобілів

```bash
curl -X GET "http://localhost:8000/api/v1/cars?page=1&limit=10&sort_by=price&sort_order=-1&min_price=10000&max_price=50000&min_year=2015"
```

Відповідь:
```json
{
  "page": 1,
  "limit": 10,
  "total": 42,
  "total_pages": 5,
  "data": [
    {
      "id": "64a3b5c7890d12e3f456g789",
      "make": "BMW",
      "model": "X5",
      "year": 2019,
      "price": 45000,
      "mileage": 65000,
      "engine_type": "дизель",
      "engine_volume": 3.0,
      "transmission": "автомат",
      "drive_type": "повний",
      "location": "Київ",
      "image_url": "https://example.com/image.jpg",
      "url": "https://auto.ria.com/uk/auto_bmw_x5_12345.html",
      "created_at": "2023-07-15T10:30:00.000Z"
    },
    // інші автомобілі...
  ]
}
```

### Отримання автомобіля за ID

```bash
curl -X GET "http://localhost:8000/api/v1/cars/64a3b5c7890d12e3f456g789"
```

Відповідь:
```json
{
  "id": "64a3b5c7890d12e3f456g789",
  "make": "BMW",
  "model": "X5",
  "year": 2019,
  "price": 45000,
  "mileage": 65000,
  "engine_type": "дизель",
  "engine_volume": 3.0,
  "transmission": "автомат",
  "drive_type": "повний",
  "location": "Київ",
  "image_url": "https://example.com/image.jpg",
  "url": "https://auto.ria.com/uk/auto_bmw_x5_12345.html",
  "created_at": "2023-07-15T10:30:00.000Z"
}
```

### Додавання нового автомобіля

```bash
curl -X POST "http://localhost:8000/api/v1/cars" \
  -H "Content-Type: application/json" \
  -d '{
    "make": "Audi",
    "model": "Q7",
    "year": 2020,
    "price": 55000,
    "mileage": 30000,
    "engine_type": "дизель",
    "engine_volume": 3.0,
    "transmission": "автомат",
    "drive_type": "повний",
    "location": "Львів",
    "image_url": "https://example.com/audi_q7.jpg",
    "url": "https://auto.ria.com/uk/auto_audi_q7_12346.html"
  }'
```

### Оновлення автомобіля

```bash
curl -X PUT "http://localhost:8000/api/v1/cars/64a3b5c7890d12e3f456g789" \
  -H "Content-Type: application/json" \
  -d '{
    "price": 42000,
    "mileage": 68000
  }'
```

### Видалення автомобіля

```bash
curl -X DELETE "http://localhost:8000/api/v1/cars/64a3b5c7890d12e3f456g789"
```

### Запуск скрапера

```bash
curl -X POST "http://localhost:8000/api/v1/scraper/run?pages=3"
```

### Отримання статистики

```bash
curl -X GET "http://localhost:8000/api/v1/cars/stats"
```

Відповідь:
```json
{
  "total_cars": 142,
  "avg_price": 25680,
  "avg_year": 2017,
  "avg_mileage": 85420,
  "popular_makes": [
    {"make": "BMW", "count": 28},
    {"make": "Volkswagen", "count": 24},
    {"make": "Toyota", "count": 19},
    {"make": "Audi", "count": 17},
    {"make": "Mercedes-Benz", "count": 15}
  ]
}
```

## Функціонал скрапера

Скрапер авторинку збирає інформацію з сайту auto.ria.com, включаючи:

- Марка та модель автомобіля
- Рік випуску
- Ціна
- Пробіг
- Тип та об'єм двигуна
- Тип трансмісії
- Тип приводу
- Місцезнаходження
- URL зображення та оголошення

Запустити скрапер можна через API або через веб-інтерфейс, натиснувши кнопку "Оновити дані" на головній сторінці.

## Веб-інтерфейс

Веб-інтерфейс доступний за адресою http://localhost:8000/ і дозволяє:

- Переглядати список автомобілів
- Фільтрувати та сортувати автомобілі
- Переглядати детальну інформацію про автомобіль
- Запускати скрапер для оновлення даних

## Додаткові функції

- **Фільтрація**: за ціною, роком випуску, маркою
- **Сортування**: за ціною, роком, датою додавання
- **Пагінація**: розбиття результатів на сторінки
- **Статистика**: середня ціна, рік, пробіг, популярні марки

## Автор

Олександр Галабурда
