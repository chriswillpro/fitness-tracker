"""Streamlit frontend — workout logging flow (basic/advanced mode)."""

from datetime import date

import requests
import streamlit as st

import api_client as api

USER_ID = 1  # single hardcoded user for now — see master prompt section 4

CATEGORY_ICONS = {
    "push": ":material/fitness_center:",
    "pull": ":material/rowing:",
    "legs": ":material/directions_walk:",
    "core": ":material/self_improvement:",
}
MODE_COLOR = {"basic": "blue", "advanced": "violet"}

st.set_page_config(
    page_title="Fitness Tracker — Log workout",
    page_icon=":material/fitness_center:",
    layout="centered",
)
st.title(":material/fitness_center: Log workout")

try:
    user = api.get_user(USER_ID)
except requests.exceptions.ConnectionError:
    st.error(
        f"Can't reach the API at {api.API_BASE_URL}. "
        "Is the FastAPI server running (`uvicorn app.main:app --reload`)?",
        icon=":material/error:",
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
    st.caption("No workout logged for this date yet.")
    notes = st.text_area("Notes (optional)", value=st.session_state.session_notes)
    if st.button("Start workout", type="primary", icon=":material/play_arrow:"):
        session = api.create_session(USER_ID, selected_date, notes or None)
        st.session_state.session_id = session["id"]
        st.session_state.session_notes = notes
        st.rerun()
    st.stop()

session_id = st.session_state.session_id

with st.expander("Session notes", icon=":material/edit_note:"):
    notes = st.text_area(
        "Notes", value=st.session_state.session_notes, key="notes_input", label_visibility="collapsed"
    )
    if st.button("Save notes", icon=":material/save:"):
        api.update_session_notes(session_id, notes or None)
        st.session_state.session_notes = notes
        st.toast("Notes saved", icon=":material/check:")

st.subheader("Add an exercise", divider="orange")

exercises = api.list_exercises()
exercise_by_id = {e["id"]: e for e in exercises}

with st.container(horizontal=True, vertical_alignment="bottom"):
    chosen = st.selectbox(
        "Exercise",
        options=exercises,
        format_func=lambda e: f"{e['name']} ({e['category']})",
    )
    mode = st.segmented_control("Mode", options=["basic", "advanced"], default="basic", required=True)
    if st.button("Add to session", type="primary", icon=":material/add:"):
        existing_session_exercises = api.list_session_exercises(session_id)
        api.add_session_exercise(session_id, chosen["id"], mode, len(existing_session_exercises))
        st.rerun()

st.subheader("This session", divider="orange")

session_exercises = api.list_session_exercises(session_id)
if not session_exercises:
    st.caption("No exercises added yet — add one above to get started.")

for se in session_exercises:
    exercise = exercise_by_id.get(se["exercise_id"], {"name": "Unknown exercise", "category": None})
    icon = CATEGORY_ICONS.get(exercise.get("category"), ":material/sports_gymnastics:")

    with st.container(border=True):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.markdown(f"**{icon} {exercise['name']}**")
            st.badge(se["mode"], color=MODE_COLOR[se["mode"]])

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
            column_config = None
            if se["mode"] == "advanced":
                column_config = {
                    "RPE": st.column_config.ProgressColumn("RPE", min_value=0, max_value=10, format="%.1f")
                }
            st.dataframe(rows, hide_index=True, column_config=column_config)

        st.markdown("**Add set**")
        with st.container(horizontal=True):
            reps = st.number_input("Reps", min_value=1, step=1, key=f"reps_{se['id']}")
            weight_value = st.number_input(
                "Weight", min_value=0.0, step=2.5, key=f"weight_{se['id']}"
            )
            weight_unit = st.selectbox(
                "Unit",
                options=["lbs", "kg"],
                index=0 if user["preferred_unit"] == "lbs" else 1,
                key=f"unit_{se['id']}",
            )

        rpe = rest_seconds = set_notes = None
        if se["mode"] == "advanced":
            with st.container(horizontal=True):
                rpe = st.number_input(
                    "RPE", min_value=0.0, max_value=10.0, step=0.5, key=f"rpe_{se['id']}"
                )
                rest_seconds = st.number_input(
                    "Rest (seconds)", min_value=0, step=15, key=f"rest_{se['id']}"
                )
                set_notes = st.text_input("Set notes", key=f"setnotes_{se['id']}")

        with st.container(horizontal=True, horizontal_alignment="distribute"):
            if st.button("Add set", key=f"addset_{se['id']}", type="primary", icon=":material/add:"):
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
                st.toast(f"Set {len(sets) + 1} added", icon=":material/check:")
                st.rerun()

            if st.button(
                "Remove exercise", key=f"removeex_{se['id']}", type="tertiary", icon=":material/delete:"
            ):
                api.delete_session_exercise(se["id"])
                st.rerun()
