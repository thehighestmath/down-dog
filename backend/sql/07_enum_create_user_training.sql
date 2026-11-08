-- ============================================================
-- Миграция workouts: level/focus VARCHAR+CHECK -> ENUM
-- ============================================================

-- 1. Проверка существующих значений
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM workouts
        WHERE level NOT IN ('beginner', 'intermediate', 'advanced')
    ) THEN
        RAISE EXCEPTION
            'Invalid values in workouts.level, migration aborted';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM workouts
        WHERE focus NOT IN (
            'back', 'neck', 'legs', 'full_body', 'relaxation'
        )
    ) THEN
        RAISE EXCEPTION
            'Invalid values in workouts.focus, migration aborted';
    END IF;
END $$;

-- 2. Создание ENUM-типов
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

-- 3. Удаление старых CHECK-ограничений
ALTER TABLE workouts
    DROP CONSTRAINT IF EXISTS workouts_level_check;

ALTER TABLE workouts
    DROP CONSTRAINT IF EXISTS workouts_focus_check;

-- 4. Преобразование колонок в ENUM
ALTER TABLE workouts
    ALTER COLUMN level TYPE workout_level
        USING level::text::workout_level,
    ALTER COLUMN focus TYPE workout_focus
        USING focus::text::workout_focus;

-- 5. Комментарии
COMMENT ON TABLE workouts
    IS 'Сгенерированные тренировки';

COMMENT ON COLUMN workouts.poses
    IS 'Упорядоченный JSON-массив названий поз (name_en)';