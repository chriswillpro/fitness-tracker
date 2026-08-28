"""Thin wrapper around the FastAPI backend's HTTP API."""

import os

import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


def _url(path: str) -> str:
    return f"{API_BASE_URL}{path}"


def get_user(user_id: int) -> dict:
    r = requests.get(_url(f"/users/{user_id}"))
    r.raise_for_status()
    return r.json()


def list_exercises() -> list[dict]:
    r = requests.get(_url("/exercises"))
    r.raise_for_status()
    return r.json()


def find_session_for_date(user_id: int, session_date) -> dict | None:
    r = requests.get(
        _url("/workout-sessions"),
        params={"user_id": user_id, "date_from": session_date, "date_to": session_date},
    )
    r.raise_for_status()
    sessions = r.json()
    return sessions[0] if sessions else None


def create_session(user_id: int, session_date, notes: str | None = None) -> dict:
    r = requests.post(
        _url("/workout-sessions"),
        json={"user_id": user_id, "session_date": str(session_date), "notes": notes},
    )
    r.raise_for_status()
    return r.json()


def update_session_notes(session_id: int, notes: str | None) -> dict:
    r = requests.patch(_url(f"/workout-sessions/{session_id}"), json={"notes": notes})
    r.raise_for_status()
    return r.json()


def list_session_exercises(session_id: int) -> list[dict]:
    r = requests.get(_url("/session-exercises"), params={"session_id": session_id})
    r.raise_for_status()
    return r.json()


def add_session_exercise(session_id: int, exercise_id: int, mode: str, order_index: int) -> dict:
    r = requests.post(
        _url("/session-exercises"),
        json={
            "session_id": session_id,
            "exercise_id": exercise_id,
            "mode": mode,
            "order_index": order_index,
        },
    )
    r.raise_for_status()
    return r.json()


def delete_session_exercise(session_exercise_id: int) -> None:
    r = requests.delete(_url(f"/session-exercises/{session_exercise_id}"))
    r.raise_for_status()


def list_sets(session_exercise_id: int) -> list[dict]:
    r = requests.get(_url("/exercise-sets"), params={"session_exercise_id": session_exercise_id})
    r.raise_for_status()
    return r.json()


def add_set(
    session_exercise_id: int,
    set_number: int,
    reps: int,
    weight_value: float,
    weight_unit: str,
    rpe: float | None = None,
    rest_seconds: int | None = None,
    notes: str | None = None,
) -> dict:
    payload = {
        "session_exercise_id": session_exercise_id,
        "set_number": set_number,
        "reps": reps,
        "weight_value": weight_value,
        "weight_unit": weight_unit,
        "rpe": rpe,
        "rest_seconds": rest_seconds,
        "notes": notes,
    }
    r = requests.post(_url("/exercise-sets"), json=payload)
    r.raise_for_status()
    return r.json()


def delete_set(set_id: int) -> None:
    r = requests.delete(_url(f"/exercise-sets/{set_id}"))
    r.raise_for_status()


def list_body_metrics(user_id: int, date_from=None, date_to=None) -> list[dict]:
    params = {"user_id": user_id}
    if date_from is not None:
        params["date_from"] = date_from
    if date_to is not None:
        params["date_to"] = date_to
    r = requests.get(_url("/body-metrics"), params=params)
    r.raise_for_status()
    return r.json()


def add_body_metric(user_id: int, metric_date, weight_value: float, weight_unit: str) -> dict:
    r = requests.post(
        _url("/body-metrics"),
        json={
            "user_id": user_id,
            "metric_date": str(metric_date),
            "weight_value": weight_value,
            "weight_unit": weight_unit,
        },
    )
    r.raise_for_status()
    return r.json()


def list_progress_photos(user_id: int) -> list[dict]:
    r = requests.get(_url("/progress-photos"), params={"user_id": user_id})
    r.raise_for_status()
    return r.json()


def upload_progress_photo(
    user_id: int,
    filename: str,
    content_type: str,
    file_bytes: bytes,
    body_metric_id: int | None = None,
    taken_at=None,
) -> dict:
    data = {"user_id": user_id}
    if body_metric_id is not None:
        data["body_metric_id"] = body_metric_id
    if taken_at is not None:
        data["taken_at"] = taken_at.isoformat()
    files = {"file": (filename, file_bytes, content_type or "application/octet-stream")}
    r = requests.post(_url("/progress-photos/upload"), data=data, files=files)
    r.raise_for_status()
    return r.json()


def delete_progress_photo(photo_id: int) -> None:
    r = requests.delete(_url(f"/progress-photos/{photo_id}"))
    r.raise_for_status()


def exercise_progression(user_id: int, exercise_id: int, date_from=None, date_to=None) -> list[dict]:
    params = {"user_id": user_id, "exercise_id": exercise_id}
    if date_from is not None:
        params["date_from"] = date_from
    if date_to is not None:
        params["date_to"] = date_to
    r = requests.get(_url("/analytics/exercise-progression"), params=params)
    r.raise_for_status()
    return r.json()


def session_volume(user_id: int, date_from=None, date_to=None) -> list[dict]:
    params = {"user_id": user_id}
    if date_from is not None:
        params["date_from"] = date_from
    if date_to is not None:
        params["date_to"] = date_to
    r = requests.get(_url("/analytics/session-volume"), params=params)
    r.raise_for_status()
    return r.json()
