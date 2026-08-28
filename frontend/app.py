"""Streamlit frontend — workout logging flow (basic/advanced mode)."""

from datetime import date

import requests
import streamlit as st

import api_client as api

USER_ID = 1  # single hardcoded user for now — see master prompt section 4

st.set_page_config(page_title="Fitness Tracker — Log Workout", layout="centered")
st.title("Log Workout")

try:
    user = api.get_user(USER_ID)
except requests.exceptions.ConnectionError:
    st.error(
        f"Can't reach the API at {api.API_BASE_URL}. "
        "Is the FastAPI server running (`uvicorn app.main:app --reload`)?"
    )
    st.stop()

st.caption(f"Logging as **{user['name']}** — preferred unit: {user['preferred_unit']}")

selected_date = st.date_input("Workout date", value=date.today())

if st.session_state.get("session_date") != selected_date:
    existing = api.find_session_for_date(USER_ID, selected_date)
    st.session_state.session_date = selected_date
    st.session_state.session_id = existing["id"] if existing else None
    st.session_state.session_notes = existing["notes"] or "" if existing else ""

if st.session_state.session_id is None:
    st.info("No workout logged for this date yet.")
    notes = st.text_area("Notes (optional)", value=st.session_state.session_notes)
    if st.button("Start workout", type="primary"):
        session = api.create_session(USER_ID, selected_date, notes or None)
        st.session_state.session_id = session["id"]
        st.session_state.session_notes = notes
        st.rerun()
    st.stop()

session_id = st.session_state.session_id

with st.expander("Session notes"):
    notes = st.text_area("Notes", value=st.session_state.session_notes, key="notes_input")
    if st.button("Save notes"):
        api.update_session_notes(session_id, notes or None)
        st.session_state.session_notes = notes
        st.success("Notes saved")

st.divider()
st.subheader("Add an exercise")

exercises = api.list_exercises()
exercise_by_id = {e["id"]: e for e in exercises}

chosen = st.selectbox(
    "Exercise",
    options=exercises,
    format_func=lambda e: f"{e['name']} ({e['category']})",
)
mode = st.radio("Mode", options=["basic", "advanced"], horizontal=True)
if st.button("Add exercise to session"):
    existing_session_exercises = api.list_session_exercises(session_id)
    api.add_session_exercise(session_id, chosen["id"], mode, len(existing_session_exercises))
    st.rerun()

st.divider()
st.subheader("This session")

session_exercises = api.list_session_exercises(session_id)
if not session_exercises:
    st.write("No exercises added yet.")

for se in session_exercises:
    exercise = exercise_by_id.get(se["exercise_id"], {"name": "Unknown exercise"})
    with st.expander(f"{exercise['name']} — {se['mode']}", expanded=True):
        sets = api.list_sets(se["id"])

        if sets:
            rows = []
            for s in sets:
                row = {
                    "Set": s["set_number"],
                    "Reps": s["reps"],
                    "Weight": f"{s['weight_value']} {s['weight_unit']}",
                }
                if se["mode"] == "advanced":
                    row["RPE"] = s["rpe"]
                    row["Rest (s)"] = s["rest_seconds"]
                    row["Notes"] = s["notes"]
                rows.append(row)
            st.table(rows)

        st.markdown("**Add set**")
        cols = st.columns(3)
        reps = cols[0].number_input("Reps", min_value=1, step=1, key=f"reps_{se['id']}")
        weight_value = cols[1].number_input(
            "Weight", min_value=0.0, step=2.5, key=f"weight_{se['id']}"
        )
        weight_unit = cols[2].selectbox(
            "Unit",
            options=["lbs", "kg"],
            index=0 if user["preferred_unit"] == "lbs" else 1,
            key=f"unit_{se['id']}",
        )

        rpe = rest_seconds = set_notes = None
        if se["mode"] == "advanced":
            adv_cols = st.columns(3)
            rpe = adv_cols[0].number_input(
                "RPE", min_value=0.0, max_value=10.0, step=0.5, key=f"rpe_{se['id']}"
            )
            rest_seconds = adv_cols[1].number_input(
                "Rest (seconds)", min_value=0, step=15, key=f"rest_{se['id']}"
            )
            set_notes = adv_cols[2].text_input("Set notes", key=f"setnotes_{se['id']}")

        button_cols = st.columns(2)
        if button_cols[0].button("Add set", key=f"addset_{se['id']}"):
            api.add_set(
                se["id"],
                set_number=len(sets) + 1,
                reps=reps,
                weight_value=weight_value,
                weight_unit=weight_unit,
                rpe=rpe or None,
                rest_seconds=int(rest_seconds) if rest_seconds else None,
                notes=set_notes or None,
            )
            st.rerun()

        if button_cols[1].button("Remove exercise", key=f"removeex_{se['id']}"):
            api.delete_session_exercise(se["id"])
            st.rerun()
