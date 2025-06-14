# Використовуємо офіційний образ Python
FROM python:3.12-slim

# Встановлюємо робочу директорію
WORKDIR /app

# Встановлюємо системні залежності
RUN apt-get update && apt-get install -y gcc libpq-dev

# Копіюємо файли проекту (залежності)
COPY pyproject.toml poetry.lock* /app/

# Встановлюємо Poetry та залежності
RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --only main

# Копіюємо весь проєкт
COPY . /app

# Вказуємо порт
EXPOSE 8000

# Команда запуску FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]