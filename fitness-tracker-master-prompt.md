# Fitness Tracker — Project Master Prompt & Scope

## 1. What this is
A personal fitness-tracking web app (workouts + body metrics) built for daily personal use, that doubles as a portfolio piece demonstrating data modeling, backend/API design, and data analysis/visualization skills. The core insight driving the product: people already track this in spreadsheets because paid apps aren't worth it — this app should beat "a spreadsheet," not "MyFitnessPal."

## 2. Goals (in priority order)
1. **Utility first** — must be something the builder actually opens and uses daily.
2. **Skill growth** — first project that goes beyond querying/analyzing existing data into building something that *captures and stores* data (schema design, API layer). Stays close to Python/SQL rather than pivoting into a new language stack.
3. **Portfolio evidence** — needs to produce a live, clickable demo link recruiters can use, backed by clean, documented code.

## 3. Constraints
- Solo builder, currently comfortable with SQL querying and Python (pandas) analysis on pre-existing datasets — **not yet experienced building an app/backend/schema from scratch.** Treat this as a growth area, not an assumed skill.
- Timeline: as fast as possible, but "no shortcuts" — must be functionally complete, not a throwaway demo.
- Tech preference: stay close to Python/SQL. Avoid front-loading a new frontend framework (e.g., React) before the data layer is solid.
- Budget: free/near-free hosting preferred.

## 4. Users
- Just the builder, for now. Design the data model so it's not painful to add multi-user support later (e.g., include a `user_id` from day one even with a single hardcoded user), but don't build auth/multi-tenancy yet.

## 5. Core features (v1 — MVP)

### Workout logging
- Two logging modes, user-selectable: **Basic** (sets, reps, weight) and **Advanced** (adds notes, RPE/effort, rest time).
- Exercise library/categories (push/pull/legs, or similar) to organize logged exercises — supports future analysis (e.g., volume by muscle group).

### Body metrics
- Body weight over time.
- Progress photos (stored with timestamp, associated with a weight entry).

### Analysis / visualization (must exist from day one, not bolted on later)
- Trend charts: weight over time, volume/strength progression per exercise over time.
- Basic comparisons: this week vs. last week, this month vs. last month.
- This is the layer where existing SQL/Python analysis skills get directly applied — treat it as a first-class feature, not a stretch goal.

## 6. Explicit non-goals (for v1)
- No native iOS/Android app (see stack notes — PWA path instead).
- No multi-user auth system.
- No social features, no integrations with wearables/other trackers (revisit later if desired).

## 7. Recommended technical approach
- **Backend**: Python + FastAPI — RESTful API over the data, teaches schema/API design while staying in Python.
- **Database**: PostgreSQL (hosted free on Neon or Supabase).
- **Frontend (v1)**: Streamlit — fastest path to a usable, demoable UI without learning a JS framework first.
- **Frontend (v2, stretch)**: Migrate/add a PWA (installable on phone home screen) once data model + API are stable — gets "feels like a mobile app" without App Store overhead or a new language.
- **Hosting**: Render or Railway (backend, free tier) + Neon/Supabase (DB, free tier) + Streamlit Community Cloud (frontend demo link).
- **Photos**: store in object storage (e.g., Supabase Storage or Cloudinary free tier) rather than the DB directly; store the URL/reference in Postgres.

## 8. Suggested build order
1. Design the database schema (users, exercises, workout_logs, body_metrics, photos) — this is the highest-leverage learning step and worth doing carefully.
2. Build the FastAPI backend with core CRUD endpoints.
3. Build the Streamlit frontend for logging (basic/advanced toggle) and viewing trend charts.
4. Deploy (free tiers) and get a live demo link working end-to-end.
5. Polish: docs, README, clean code, maybe a short write-up of design decisions (good portfolio narrative material).
6. Stretch: PWA migration for a "real app" feel.

## 9. Portfolio deliverable
- Public GitHub repo with clean code and a solid README (problem framed as "beat the spreadsheet," design decisions explained).
- Live demo link (Streamlit Community Cloud or similar) that recruiters can click without setup.

## 10. Open questions to revisit as the project develops
- Exact exercise library taxonomy (how granular should categories be?).
- Whether "advanced" mode fields (RPE, rest time) should be configurable per-exercise or global per-session.
- When/whether to prioritize the PWA migration vs. adding more analysis features.
