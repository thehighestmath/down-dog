import os
import boto3
from botocore.client import Config

# Настройки подключения к MinIO
MINIO_ENDPOINT = 'http://localhost:9000'
ACCESS_KEY = 'minioadmin'
SECRET_KEY = 'minioadmin'
BUCKET_NAME = 'yogaimages-2'  # имя корзины

# Создаем клиент
s3 = boto3.client(
    's3',
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    config=Config(signature_version='s3v4'),
    region_name='us-east-1'
)

# 1. Создаем bucket (если его нет)
try:

    s3.create_bucket(Bucket=BUCKET_NAME)
    print(f'✅ Бакет "{BUCKET_NAME}" создан')
except Exception as e:
    print(f'ℹ️ Бакет уже существует или ошибка: {e}')

# 2. Загружаем изображения
images_folder = './Картинки с позами/'  # папка с вашими картинками
for filename in os.listdir(images_folder):
    if filename.lower().endswith(('.svg', '.png', '.jpg', '.jpeg')):
        file_path = os.path.join(images_folder, filename)
        try:
            s3.upload_file(file_path, BUCKET_NAME, filename)
            print(f'✅ Загружено: {filename}')
        except Exception as e:
            print(f'❌ Ошибка загрузки {filename}: {e}')

# 3. (Опционально) Загружаем JSON-файл в S3 (если хотите хранить его там)
json_file = './seed_data/poses.json'
if os.path.exists(json_file):
    try:
        s3.upload_file(json_file, BUCKET_NAME, 'poses.json')
        print(f'✅ JSON-файл загружен как poses.json')
    except Exception as e:
        print(f'❌ Ошибка загрузки JSON: {e}')
else:
    print('ℹ️ JSON-файл не найден, пропускаем')

print('🎉 Готово!')