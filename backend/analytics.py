import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MAX_BODY_BYTES = 2048

MAX_POSES = 1000


class _Strict(BaseModel):
    # Неизвестное поле — ошибка 422, а не молча сохранённый мусор
    model_config = ConfigDict(extra="forbid")


class WorkoutStartedPayload(_Strict):
    workout_id: uuid.UUID
    duration_min: int = Field(ge=1, le=180)
    level: str = Field(max_length=32)
    focus: str = Field(max_length=32)


class WorkoutCompletedPayload(_Strict):
    workout_id: uuid.UUID
    poses_count: int | None = Field(default=None, ge=0, le=MAX_POSES)


class WorkoutAbandonedPayload(_Strict):
    workout_id: uuid.UUID
    current_pose_index: int | None = Field(default=None, ge=0, le=MAX_POSES)
    reason: str | None = Field(default=None, max_length=100)


class PoseViewedPayload(_Strict):
    workout_id: uuid.UUID
    pose_name: str = Field(max_length=100)
    pose_index: int = Field(ge=0, le=MAX_POSES)


class _EventBase(_Strict):
    user_id: uuid.UUID
    session_id: uuid.UUID


class WorkoutStartedEvent(_EventBase):
    event_type: Literal["workout_started"]
    payload: WorkoutStartedPayload


class WorkoutCompletedEvent(_EventBase):
    event_type: Literal["workout_completed"]
    payload: WorkoutCompletedPayload


class WorkoutAbandonedEvent(_EventBase):
    event_type: Literal["workout_abandoned"]
    payload: WorkoutAbandonedPayload


class PoseViewedEvent(_EventBase):
    event_type: Literal["pose_viewed"]
    payload: PoseViewedPayload


AnalyticsEvent = (
    WorkoutStartedEvent
    | WorkoutCompletedEvent
    | WorkoutAbandonedEvent
    | PoseViewedEvent
)