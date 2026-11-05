import json
import logging
import uuid
from typing import Any
from unittest.mock import MagicMock

import main
import pytest
from analytics import MAX_BODY_BYTES
from fastapi.testclient import TestClient

client = TestClient(main.app)

WORKOUT_ID = str(uuid.uuid4())


def event(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_type": event_type,
        "user_id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "payload": payload,
    }


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Подменяет БД: проверяем, что и с какими параметрами записалось."""
    connection = MagicMock()
    monkeypatch.setattr(main, "get_db_connection", lambda: connection)
    return connection


def executed_params(connection: MagicMock) -> tuple[Any, ...]:
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.execute.assert_called_once()
    params: tuple[Any, ...] = cursor.execute.call_args.args[1]
    return params


FRONTEND_EVENTS = [
    event(
        "workout_started",
        {
            "workout_id": WORKOUT_ID,
            "duration_min": 10,
            "level": "beginner",
            "focus": "full_body",
        },
    ),
    event("workout_completed", {"workout_id": WORKOUT_ID, "poses_count": 12}),
    event("workout_abandoned", {"workout_id": WORKOUT_ID, "current_pose_index": 3}),
    event(
        "pose_viewed",
        {"workout_id": WORKOUT_ID, "pose_name": "Mountain Pose", "pose_index": 0},
    ),
]


@pytest.mark.parametrize("body", FRONTEND_EVENTS, ids=lambda b: b["event_type"])
def test_frontend_events_are_saved(body: dict[str, Any], db: MagicMock) -> None:
    response = client.post("/api/analytics/track", json=body)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    event_type, user_id, session_id, payload = executed_params(db)
    assert event_type == body["event_type"]
    assert user_id == body["user_id"]
    assert session_id == body["session_id"]
    assert json.loads(payload) == body["payload"]
    db.commit.assert_called_once_with()
    db.close.assert_called_once_with()


def test_too_large_event_is_rejected_with_413(db: MagicMock) -> None:
    body = event(
        "pose_viewed",
        {"workout_id": WORKOUT_ID, "pose_name": "x" * MAX_BODY_BYTES, "pose_index": 0},
    )

    response = client.post("/api/analytics/track", json=body)

    assert response.status_code == 413
    db.cursor.assert_not_called()


@pytest.mark.parametrize(
    "body",
    [
        pytest.param(
            event(
                "pose_viewed",
                {
                    "workout_id": WORKOUT_ID,
                    "pose_name": "Mountain Pose",
                    "pose_index": 0,
                    "junk": "лишнее поле",
                },
            ),
            id="extra-field-in-payload",
        ),
        pytest.param(
            {**event("workout_completed", {"workout_id": WORKOUT_ID}), "junk": 1},
            id="extra-top-level-field",
        ),
        pytest.param(
            event(
                "workout_completed",
                {"workout_id": WORKOUT_ID, "pose_name": "x", "pose_index": 0},
            ),
            id="payload-of-another-event",
        ),
    ],
)
def test_unknown_fields_are_rejected(body: dict[str, Any], db: MagicMock) -> None:
    response = client.post("/api/analytics/track", json=body)

    assert response.status_code == 422
    db.cursor.assert_not_called()


@pytest.mark.parametrize(
    "body",
    [
        pytest.param(
            event(
                "workout_started",
                {
                    "workout_id": WORKOUT_ID,
                    "duration_min": "десять",
                    "level": "beginner",
                    "focus": "back",
                },
            ),
            id="duration-not-a-number",
        ),
        pytest.param(
            event("pose_viewed", {"workout_id": WORKOUT_ID, "pose_name": "x"}),
            id="required-field-missing",
        ),
        pytest.param(
            event("workout_completed", {"workout_id": "не-uuid"}),
            id="workout-id-not-uuid",
        ),
        pytest.param(
            {**event("workout_completed", {"workout_id": WORKOUT_ID}), "user_id": "1"},
            id="user-id-not-uuid",
        ),
    ],
)
def test_wrong_types_are_rejected(body: dict[str, Any], db: MagicMock) -> None:
    response = client.post("/api/analytics/track", json=body)

    assert response.status_code == 422
    db.cursor.assert_not_called()


def test_unknown_event_type_is_rejected(db: MagicMock) -> None:
    body = event("user_hacked", {"workout_id": WORKOUT_ID})

    response = client.post("/api/analytics/track", json=body)

    assert response.status_code == 422
    db.cursor.assert_not_called()


def test_payload_is_not_logged(db: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    body = event(
        "pose_viewed",
        {"workout_id": WORKOUT_ID, "pose_name": "Secret Pose", "pose_index": 7},
    )

    response = client.post("/api/analytics/track", json=body)

    assert response.status_code == 200
    assert "pose_viewed" in caplog.text
    assert "Secret Pose" not in caplog.text
    assert WORKOUT_ID not in caplog.text