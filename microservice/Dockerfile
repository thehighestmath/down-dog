FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY simple_microservice.py .

# Создаем группу и пользователя с конкретными числовыми ID (1000)
RUN groupadd -g 1000 appgroup && useradd -u 1000 -g appgroup -m appuser && \
    chown -R appuser:appgroup /app

# Переключаемся на числовой ID (Hadolint это одобряет)
USER 1000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "-k", "uvicorn.workers.UvicornWorker", "simple_microservice:api"]
