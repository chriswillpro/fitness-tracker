from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import (
    analytics,
    body_metrics,
    exercise_sets,
    exercises,
    progress_photos,
    session_exercises,
    users,
    workout_sessions,
)

app = FastAPI(title="Fitness Tracker API")

# progress_photos router creates media/progress_photos/ on import, so
# media/ already exists by the time this mount runs.
app.mount("/media", StaticFiles(directory="media"), name="media")

app.include_router(users.router)
app.include_router(exercises.router)
app.include_router(workout_sessions.router)
app.include_router(session_exercises.router)
app.include_router(exercise_sets.router)
app.include_router(body_metrics.router)
app.include_router(progress_photos.router)
app.include_router(analytics.router)


@app.get("/health")
def health():
    return {"status": "ok"}
