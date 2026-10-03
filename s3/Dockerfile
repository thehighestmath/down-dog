FROM python:3.12-slim

WORKDIR /down-dog

# Build context is the repo root (see docker-compose.yml): Images/ lives there
COPY s3/requirements.txt .
RUN pip install --no-cache-dir \
    --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    -r requirements.txt

COPY s3/s3.py .
COPY Images ./Images

CMD ["python", "s3.py"]
