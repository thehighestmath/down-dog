import os

import boto3
from botocore.client import Config
from dotenv import load_dotenv


def create_s3_client():
    load_dotenv()
    # Создаем клиент
    s3 = boto3.client(
        's3',
        endpoint_url=os.getenv('MINIO_ENDPOINT'),
        aws_access_key_id=os.getenv('ACCESS_KEY'),
        aws_secret_access_key=os.getenv('SECRET_KEY'),
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'
    )

    try:

        s3.create_bucket(Bucket=os.getenv('BUCKET_NAME'))
        print(f'✅ Бакет "{os.getenv('BUCKET_NAME')}" создан')
    except Exception as e:
        print(f'ℹ️ Бакет уже существует или ошибка: {e}')

    # 2. Загружаем изображения
    images_folder = './Картинки с позами/'  # папка с картинками
    for filename in os.listdir(images_folder):
        if filename.lower().endswith(('.svg', '.png', '.jpg', '.jpeg')):
            file_path = os.path.join(images_folder, filename)
            try:
                s3.upload_file(file_path, os.getenv('BUCKET_NAME'), filename)
                print(f'✅ Загружено: {filename}')
            except Exception as e:
                print(f'❌ Ошибка загрузки {filename}: {e}')

    print('🎉 Готово!')


create_s3_client()
