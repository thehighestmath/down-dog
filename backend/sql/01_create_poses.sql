--это первая миграция, создает таблицу с заданными столбцами
CREATE TABLE IF NOT EXISTS poses (
    id SERIAL PRIMARY KEY,
    name_ru VARCHAR(255) NOT NULL,
    name_sanskrit VARCHAR(255),
    name_en VARCHAR(255),
    category VARCHAR(100),
    difficulty VARCHAR(50),
    focus_areas TEXT,
    contraindications TEXT,
    description TEXT,
    image_url VARCHAR(512),
    audio_url VARCHAR(512)
);