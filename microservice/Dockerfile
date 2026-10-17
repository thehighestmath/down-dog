FROM python:3.11-slim

RUN python -m pip install fastapi httpx scrapy gunicorn uvicorn uvloop httptools

WORKDIR /app

ADD simple_microservice.py simple_microservice.py
