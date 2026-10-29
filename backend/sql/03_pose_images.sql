-- Ссылки на картинки поз. Файлы лежат в Images/, сервис s3 заливает их
-- в MinIO под тем же именем, а бэкенд отдаёт по GET /api/images/{имя файла}.
-- Применяется при каждом старте бэкенда, UPDATE можно повторять сколько угодно.
-- Для поз без картинки image_url остаётся NULL.

UPDATE poses AS p
SET image_url = '/api/images/' || m.file
FROM (
    VALUES
        ('Eagle Pose', 'Eagle Pose.jpg'),
        ('Bridge Pose', 'Bridge Pose.jpg'),
        ('Cobra Pose', 'Cobra Pose.jpg'),
        ('Bow Pose', 'Bow Pose.jpg'),
        ('Upward-Facing Dog', 'Upward-Facing Dog.jpg'),
        ('Happy Baby Pose', 'Happy Baby Pose.jpg'),
        ('Pigeon Pose', 'Pigeon Pose.jpg'),
        ('Camel Pose', 'Camel Pose.jpg'),
        ('Shoulderstand', 'Shoulderstand.jpg'),
        ('Plow Pose', 'Plow Pose.jpg'),
        ('Fish Pose', 'Fish Pose.jpg'),
        ('Half Moon Pose', 'Half Moon Pose.jpg'),
        ('Supine Twist', 'Supine Twist.jpg'),
        ('Wind-Relieving Pose', 'Wind-Relieving Pose.jpg'),
        ('Corpse Pose', 'Corpse Pose.jpg'),
        ('Warrior I', 'Воин 1.png'),
        ('Warrior II', 'Воин 2.png'),
        ('Cat-Cow Pose', 'Кошка-корова.png'),
        ('Standing Forward Bend', 'Наклон вперед стоя.png'),
        ('Mountain Pose', 'Поза горы.png'),
        ('Tree Pose', 'Поза дерева.png'),
        ('Boat Pose', 'Поза лодки.png'),
        ('Staff Pose', 'Поза посоха.png'),
        ('Child''s Pose', 'Поза ребенка.png'),
        ('Chair Pose', 'Поза стула.png'),
        ('Triangle Pose', 'Поза треугольника.png'),
        ('Downward-Facing Dog', 'Собака мордой вниз.png')
) AS m (name_en, file)
WHERE p.name_en = m.name_en;
