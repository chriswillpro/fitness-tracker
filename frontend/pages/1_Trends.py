"""Streamlit frontend — trend charts and week/month comparisons."""

from datetime import date, timedelta

import pandas as pd
import requests
import streamlit as st

import api_client as api
from units import kg_to_display

USER_ID = 1

st.set_page_config(page_title="Fitness Tracker — Trends", layout="centered")
st.title("Trends")

try:
    user = api.get_user(USER_ID)
except requests.exceptions.ConnectionError:
    st.error(
        f"Can't reach the API at {api.API_BASE_URL}. "
        "Is the FastAPI server running (`uvicorn app.main:app --reload`)?"
    )
    st.stop()

unit = user["preferred_unit"]
today = date.today()
days = st.slider("Show last N days", min_value=30, max_value=365, value=90, step=30)
range_start = today - timedelta(days=days)

# ---------------------------------------------------------------------
# Body weight
# ---------------------------------------------------------------------
st.subheader("Body weight")

with st.expander("Log today's weight"):
    cols = st.columns(2)
    weight_value = cols[0].number_input("Weight", min_value=0.0, step=0.5, key="bw_value")
    weight_unit = cols[1].selectbox(
        "Unit", options=["lbs", "kg"], index=0 if unit == "lbs" else 1, key="bw_unit"
    )
    if st.button("Save weight"):
        api.add_body_metric(USER_ID, today, weight_value, weight_unit)
        st.rerun()

metrics = api.list_body_metrics(USER_ID, date_from=range_start, date_to=today)
if not metrics:
    st.write("No body weight entries yet.")
else:
    df = pd.DataFrame(metrics)
    df["metric_date"] = pd.to_datetime(df["metric_date"])
    df["weight_display"] = df["weight_kg"].astype(float).apply(lambda kg: kg_to_display(kg, unit))
    st.line_chart(df.set_index("metric_date")["weight_display"])

st.divider()

# ---------------------------------------------------------------------
# Exercise progression
# ---------------------------------------------------------------------
st.subheader("Exercise progression")

exercises = api.list_exercises()
chosen = st.selectbox(
    "Exercise",
    options=exercises,
    format_func=lambda e: f"{e['name']} ({e['category']})",
    key="trend_exercise",
)
progression = api.exercise_progression(
    USER_ID, chosen["id"], date_from=range_start, date_to=today
)
if not progression:
    st.write(f"No logged sets for {chosen['name']} in this range yet.")
else:
    pdf = pd.DataFrame(progression)
    pdf["session_date"] = pd.to_datetime(pdf["session_date"])
    pdf["top_weight_display"] = (
        pdf["top_weight_kg"].astype(float).apply(lambda kg: kg_to_display(kg, unit))
    )
    pdf["volume_display"] = pdf["volume_kg"].astype(float).apply(lambda kg: kg_to_display(kg, unit))

    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"Top set weight ({unit})")
        st.line_chart(pdf.set_index("session_date")["top_weight_display"])
    with col2:
        st.caption(f"Session volume ({unit})")
        st.line_chart(pdf.set_index("session_date")["volume_display"])

st.divider()

# ---------------------------------------------------------------------
# Volume comparison (rolling windows, not calendar week/month — avoids
# comparing a partial current period against a full prior one)
# ---------------------------------------------------------------------
st.subheader("Volume comparison")
st.caption("Rolling windows ending today, not calendar week/month.")

last7_start = today - timedelta(days=6)
prev7_start = last7_start - timedelta(days=7)
prev7_end = last7_start - timedelta(days=1)

last30_start = today - timedelta(days=29)
prev30_start = last30_start - timedelta(days=30)
prev30_end = last30_start - timedelta(days=1)

volume_rows = api.session_volume(USER_ID, date_from=prev30_start, date_to=today)


def window_total(rows, start, end):
    return sum(
        float(r["total_volume_kg"])
        for r in rows
        if start <= date.fromisoformat(r["session_date"]) <= end
    )


this_week_total = window_total(volume_rows, last7_start, today)
last_week_total = window_total(volume_rows, prev7_start, prev7_end)
this_month_total = window_total(volume_rows, last30_start, today)
last_month_total = window_total(volume_rows, prev30_start, prev30_end)

col1, col2 = st.columns(2)
col1.metric(
    "Last 7 days volume",
    f"{kg_to_display(this_week_total, unit):,.0f} {unit}",
    delta=f"{kg_to_display(this_week_total - last_week_total, unit):,.0f} {unit} vs prior 7 days",
)
col2.metric(
    "Last 30 days volume",
    f"{kg_to_display(this_month_total, unit):,.0f} {unit}",
    delta=f"{kg_to_display(this_month_total - last_month_total, unit):,.0f} {unit} vs prior 30 days",
)
