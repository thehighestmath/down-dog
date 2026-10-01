CREATE TABLE IF NOT EXISTS poses (
    id SERIAL PRIMARY KEY,
    name_ru VARCHAR(255) NOT NULL,
    name_sanskrit VARCHAR(255),
    name_en VARCHAR(255) UNIQUE,
    category VARCHAR(100),
    difficulty VARCHAR(50),
    focus_areas TEXT,
    contraindications TEXT,
    description TEXT,
    image_url VARCHAR(512),
    audio_url VARCHAR(512),
    hold_time_sec INTEGER,
    full_cycle_sec INTEGER
);
