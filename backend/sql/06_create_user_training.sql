-- ============================================================
-- Создание таблицы workouts с ENUM-типами
-- ============================================================

-- 1. Создание ENUM-типов
CREATE TYPE workout_level AS ENUM (
    'beginner',
    'intermediate',
    'advanced'
);

CREATE TYPE workout_focus AS ENUM (
    'back',
    'neck',
    'legs',
    'full_body',
    'relaxation'
);

-- 2. Создание таблицы тренировок
CREATE TABLE IF NOT EXISTS workouts (
    id UUID PRIMARY KEY,
    duration_min SMALLINT NOT NULL,
    level workout_level NOT NULL,
    focus workout_focus NOT NULL,
    poses JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Комментарии
COMMENT ON TABLE workouts
    IS 'Сгенерированные тренировки';

COMMENT ON COLUMN workouts.poses
    IS 'Упорядоченный JSON-массив названий поз (name_en)';
