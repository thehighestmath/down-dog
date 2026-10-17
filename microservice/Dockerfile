FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY simple_microservice.py .

# 1. Создаем группу и пользователя (с флагом -r для системного пользователя)
# 2. Меняем владельца папки /app на нашего нового пользователя
RUN groupadd -r appgroup && useradd -r -g appgroup appuser && \
    chown -R appuser:appgroup /app

# 3. Переключаемся на этого пользователя (Trivy ищет именно эту строчку)
USER appuser

CMD ["gunicorn", "-b", "0.0.0.0:8000", "-k", "uvicorn.workers.UvicornWorker", "simple_microservice:api"]