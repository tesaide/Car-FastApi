FROM python:3.8-slim

WORKDIR /app

# Встановлюємо залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо код проекту
COPY . .

# Створюємо директорії для файлів логів
RUN mkdir -p logs

# Команда для запуску
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]