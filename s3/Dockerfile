FROM python:3.14-slim

WORKDIR /down-dog

# Build context is the repo root (see docker-compose.yml): Images/ lives there
COPY s3/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY s3/s3.py .
COPY Images ./Images
COPY audio ./audio

# Run as an unprivileged user: if the app is compromised, the attacker
# does not get root inside the container
RUN useradd --no-log-init --no-create-home --uid 10001 app
USER 10001

CMD ["python", "s3.py"]
