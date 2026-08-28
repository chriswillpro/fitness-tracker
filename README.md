# Fitness Tracker

A personal workout and body-metrics tracker, built to beat "a spreadsheet" — not to compete with MyFitnessPal. It's a daily-use app for logging lifts and bodyweight, with trend analysis as a first-class feature rather than something bolted on later.

This is also a portfolio project: the first one that goes beyond querying/analyzing existing data into designing a schema and building the API/app that captures it.

## Why

People already track workouts in spreadsheets because most fitness apps aren't worth the friction (accounts, ads, subscriptions, features you don't need). A spreadsheet's real weaknesses are: no structured history to query, no charts without manual pivot-tabling, and no easy way to answer "am I actually progressing on this lift?" This app keeps the spreadsheet's simplicity — log a set, log your weight — while making the analysis free.

## Features

- **Workout logging** — two modes per exercise: *Basic* (reps/weight) and *Advanced* (adds RPE, rest time, notes), so you're not filling out fields you don't care about that day.
- **Exercise library** — categorized (push/pull/legs/core), extensible with custom exercises, so volume can be rolled up by category or muscle group.
- **Body metrics** — bodyweight over time, with progress photos optionally linked to a same-day weigh-in.
- **Trends & analysis** — weight-over-time chart, per-exercise progression (top set + volume), and rolling 7-day/30-day volume comparisons. Backed by SQL aggregation, not client-side spreadsheet math.

## Design decisions

- **Basic/advanced logging is a mode flag, not two tables.** `session_exercises.mode` tells the UI which fields to render; `exercise_sets` just has nullable advanced-only columns (`rpe`, `rest_seconds`, `notes`). Avoids a parallel schema for what's really a UI concern.
- **Weight is stored as entered *and* normalized.** Every weight column keeps `weight_value` + `weight_unit` (what you actually typed) alongside a `GENERATED ALWAYS AS` `weight_kg` column. Analysis always reads `weight_kg`, so mixing lbs/kg days never corrupts a chart, but the original entry is never lossy-converted.
- **`user_id` everywhere, from day one.** There's exactly one hardcoded user right now, but every table is scoped by `user_id` so multi-user support later is a migration, not a redesign.
- **Photo storage is decoupled from the schema.** `progress_photos.photo_url` is just a text reference. The current implementation writes uploads to local disk and serves them via FastAPI static files; swapping in Supabase Storage or Cloudinary later means changing the upload endpoint, not the data model.
- **Hierarchy:** `workout_sessions` (a day) → `session_exercises` (an exercise performed that day) → `exercise_sets` (individual sets). This is what makes "progressive overload on Bench Press over time" a straightforward `GROUP BY`, not a nested spreadsheet formula.

## Tech stack

- **Backend:** FastAPI + SQLAlchemy 2.0 (ORM mirrors `schema.sql`, which is the source of truth for DDL)
- **Database:** PostgreSQL (hosted on [Neon](https://neon.tech))
- **Frontend:** Streamlit (multipage: workout logging, trends, progress photos)
- **Analysis:** SQL aggregation in the API layer, pandas for shaping chart data in the frontend

## Project structure

```
app/
  main.py              FastAPI app, router registration, static media mount
  database.py          Engine/session setup
  models.py             SQLAlchemy ORM models
  schemas.py           Pydantic request/response schemas
  routers/             One router per resource (users, exercises, workout_sessions,
                        session_exercises, exercise_sets, body_metrics,
                        progress_photos, analytics)
frontend/
  app.py               Workout logging page (basic/advanced mode)
  api_client.py         Thin wrapper around the FastAPI backend
  units.py              lbs/kg display conversion
  pages/
    1_Trends.py         Weight chart, exercise progression, volume comparisons
    2_Progress_Photos.py Photo upload + gallery
schema.sql              Database DDL (source of truth) + starter exercise seed data
```

## Running locally

**1. Database**

Create a Postgres database (a free [Neon](https://neon.tech) or [Supabase](https://supabase.com) project works well) and run `schema.sql` against it. Copy `.env.example` to `.env` and set `DATABASE_URL` to your connection string.

**2. Backend**

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs (Swagger UI) are then available at `http://127.0.0.1:8000/docs`.

**3. Frontend**

```bash
cd frontend
streamlit run app.py
```

Streamlit reads `API_BASE_URL` from the environment (defaults to `http://127.0.0.1:8000`).

## Status / roadmap

MVP feature set (logging, body metrics, progress photos, trend analysis) is complete and running against a live database. Not yet done:

- Deployment (Render/Railway for the API, Streamlit Community Cloud for the frontend) — no live demo link yet.
- Cloud object storage for progress photos (currently local disk, fine for single-user local use).
- Stretch: PWA migration for an installable, phone-friendly frontend.
