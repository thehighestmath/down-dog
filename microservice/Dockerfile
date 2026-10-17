FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Сначала копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости из файла (именно так просит hadolint)
RUN python -m pip install --no-cache-dir --requirement requirements.txt

# Копируем код
COPY simple_microservice.py .

CMD ["gunicorn", "-b", "0.0.0.0:8000", "-k", "uvicorn.workers.UvicornWorker", "simple_microservice:api"]
