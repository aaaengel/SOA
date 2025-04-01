FROM python:3.10-slim

WORKDIR /app

# Копируем список зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Копируем исходный код сервиса
COPY . .

EXPOSE 5000

# Запускаем приложение через uvicorn
CMD ["uvicorn", "ApiGateway:app", "--host", "0.0.0.0", "--port", "5000"]