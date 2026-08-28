-- =====================================================================
-- Fitness Tracker — Database Schema (PostgreSQL)
-- Companion to: fitness-tracker-master-prompt.md
--
-- Design decisions baked into this schema:
-- 1. Basic/Advanced logging = nullable columns on exercise_sets, not a
--    separate table. `session_exercises.mode` tells the UI what to show.
-- 2. Hierarchy: workout_sessions (a day) -> session_exercises (an
--    exercise performed that day) -> exercise_sets (individual sets).
--    This lets you track progressive overload per exercise, per day.
-- 3. Weight units: stored as entered (weight_value + weight_unit) to
--    preserve what was actually logged, PLUS an auto-computed weight_kg
--    column so all analysis/charts read from one consistent unit
--    regardless of what gym/unit was used that day.
-- 4. `user_id` included everywhere even though there's one hardcoded
--    user for now — keeps multi-user support a non-event later.
-- =====================================================================

-- ---------------------------------------------------------------------
-- USERS
-- ---------------------------------------------------------------------
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    preferred_unit  TEXT NOT NULL DEFAULT 'lbs' CHECK (preferred_unit IN ('lbs', 'kg')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Seed the single hardcoded user for now
INSERT INTO users (name, preferred_unit) VALUES ('me', 'lbs');


-- ---------------------------------------------------------------------
-- EXERCISES (library — seeded with common lifts, extensible by user)
-- ---------------------------------------------------------------------
CREATE TABLE exercises (
    id           SERIAL PRIMARY KEY,
    name         TEXT NOT NULL,
    category     TEXT NOT NULL CHECK (category IN ('push', 'pull', 'legs', 'core', 'other')),
    muscle_group TEXT,                      -- e.g. 'chest', 'quads' — optional, useful for volume analysis later
    is_custom    BOOLEAN NOT NULL DEFAULT FALSE,  -- FALSE = seeded default, TRUE = user-added
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (name)
);


-- ---------------------------------------------------------------------
-- WORKOUT_SESSIONS (a single day's gym visit)
-- ---------------------------------------------------------------------
CREATE TABLE workout_sessions (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id),
    session_date DATE NOT NULL,
    notes        TEXT,                      -- session-level notes, e.g. "felt strong today"
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_workout_sessions_user_date ON workout_sessions (user_id, session_date);


-- ---------------------------------------------------------------------
-- SESSION_EXERCISES (an exercise performed within a session)
-- ---------------------------------------------------------------------
CREATE TABLE session_exercises (
    id          SERIAL PRIMARY KEY,
    session_id  INTEGER NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
    exercise_id INTEGER NOT NULL REFERENCES exercises(id),
    order_index INTEGER NOT NULL DEFAULT 0,   -- order performed within the session
    mode        TEXT NOT NULL CHECK (mode IN ('basic', 'advanced')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_session_exercises_session ON session_exercises (session_id);
CREATE INDEX idx_session_exercises_exercise ON session_exercises (exercise_id);


-- ---------------------------------------------------------------------
-- EXERCISE_SETS (individual sets — this is where progressive overload
-- gets tracked: query this table filtered by exercise_id over time)
-- ---------------------------------------------------------------------
CREATE TABLE exercise_sets (
    id                   SERIAL PRIMARY KEY,
    session_exercise_id  INTEGER NOT NULL REFERENCES session_exercises(id) ON DELETE CASCADE,
    set_number           INTEGER NOT NULL,
    reps                 INTEGER NOT NULL,
    weight_value          NUMERIC(6,2) NOT NULL,
    weight_unit           TEXT NOT NULL CHECK (weight_unit IN ('lbs', 'kg')),
    weight_kg             NUMERIC(6,2) GENERATED ALWAYS AS (
                               CASE WHEN weight_unit = 'lbs' THEN ROUND(weight_value * 0.453592, 2)
                                    ELSE weight_value END
                           ) STORED,          -- normalized column — always use this for charts/analysis
    -- Advanced-mode-only fields (NULL when mode = 'basic')
    rpe           NUMERIC(3,1),               -- e.g. 8.5, rate of perceived exertion
    rest_seconds  INTEGER,
    notes         TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_exercise_sets_session_exercise ON exercise_sets (session_exercise_id);


-- ---------------------------------------------------------------------
-- BODY_METRICS (bodyweight over time — same unit-handling pattern)
-- ---------------------------------------------------------------------
CREATE TABLE body_metrics (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    metric_date   DATE NOT NULL,
    weight_value  NUMERIC(6,2) NOT NULL,
    weight_unit   TEXT NOT NULL CHECK (weight_unit IN ('lbs', 'kg')),
    weight_kg     NUMERIC(6,2) GENERATED ALWAYS AS (
                       CASE WHEN weight_unit = 'lbs' THEN ROUND(weight_value * 0.453592, 2)
                            ELSE weight_value END
                   ) STORED,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, metric_date)             -- one weigh-in per day
);

CREATE INDEX idx_body_metrics_user_date ON body_metrics (user_id, metric_date);


-- ---------------------------------------------------------------------
-- PROGRESS_PHOTOS (stored in object storage; this table just holds refs)
-- ---------------------------------------------------------------------
CREATE TABLE progress_photos (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    body_metric_id  INTEGER REFERENCES body_metrics(id),  -- nullable: photo can exist without a same-day weigh-in
    photo_url       TEXT NOT NULL,             -- URL/reference into object storage (e.g. Supabase Storage)
    taken_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_progress_photos_user ON progress_photos (user_id);


-- ---------------------------------------------------------------------
-- SEED DATA — starter exercise library (extend as needed)
-- ---------------------------------------------------------------------
INSERT INTO exercises (name, category, muscle_group) VALUES
    ('Bench Press', 'push', 'chest'),
    ('Overhead Press', 'push', 'shoulders'),
    ('Incline Dumbbell Press', 'push', 'chest'),
    ('Tricep Pushdown', 'push', 'triceps'),
    ('Deadlift', 'pull', 'back'),
    ('Barbell Row', 'pull', 'back'),
    ('Pull-Up', 'pull', 'back'),
    ('Bicep Curl', 'pull', 'biceps'),
    ('Squat', 'legs', 'quads'),
    ('Leg Press', 'legs', 'quads'),
    ('Romanian Deadlift', 'legs', 'hamstrings'),
    ('Calf Raise', 'legs', 'calves'),
    ('Weighted Sit-Up', 'core', 'abs'),
    ('Cable Woodchopper', 'core', 'obliques');
