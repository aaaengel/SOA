FROM python:3.10-slim

WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Копируем все файлы проекта (включая модули для работы с БД, схемы и т.д.)
COPY . .

EXPOSE 5001

# Запускаем приложение. Обратите внимание, что в коде используется запуск через uvicorn с модулем App.UserService:app
CMD ["uvicorn", "App.UserService:app", "--host", "0.0.0.0", "--port", "5001"]