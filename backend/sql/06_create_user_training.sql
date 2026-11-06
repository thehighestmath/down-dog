CREATE TABLE IF NOT EXISTS workouts (
    id UUID PRIMARY KEY,
    duration_min SMALLINT NOT NULL CHECK (duration_min IN (5, 10, 15, 20, 30)),
    level VARCHAR(20) NOT NULL CHECK (
        level IN ('beginner', 'intermediate', 'advanced')
    ),
    focus VARCHAR(30) NOT NULL CHECK (
        focus IN ('back', 'neck', 'legs', 'full_body', 'relaxation')
    ),
    poses JSONB NOT NULL CHECK (jsonb_typeof(poses) = 'array'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE workouts IS 'Сгенерированные тренировки';
COMMENT ON COLUMN workouts.poses IS 'Упорядоченный JSON-массив названий поз (name_en)';
