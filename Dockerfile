FROM python:3.9-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование файлов проекта
COPY . .

# Переменные окружения
ENV FLASK_APP=app.web
ENV PYTHONUNBUFFERED=1

# Открываем порты для Flask и FastAPI
EXPOSE 5000
EXPOSE 8000

# Запуск приложения
CMD ["python", "run.py"] 