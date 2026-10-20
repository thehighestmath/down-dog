CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL CHECK (
        event_type IN (
            'workout_started',
            'workout_completed',
            'workout_abandoned',
            'pose_viewed'
        )
    ),
    user_id UUID NOT NULL,
    session_id UUID NOT NULL,
    payload JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

