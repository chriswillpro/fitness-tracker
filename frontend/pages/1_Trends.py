"""Streamlit frontend — trend charts and week/month comparisons."""

from datetime import date, timedelta

import altair as alt
import pandas as pd
import requests
import streamlit as st

import api_client as api
from units import kg_to_display

USER_ID = 1

# Slots 1-3 of the app's validated dark categorical palette (.streamlit/config.toml
# chartCategoricalColors) — reused directly since Altair charts don't inherit theme colors.
BLUE = "#3987e5"
ORANGE = "#d95926"
AQUA = "#199e70"

st.set_page_config(page_title="Fitness Tracker — Trends", page_icon=":material/query_stats:", layout="centered")
st.title(":material/query_stats: Trends")

try:
    user = api.get_user(USER_ID)
except requests.exceptions.ConnectionError:
    st.error(
        f"Can't reach the API at {api.API_BASE_URL}. "
        "Is the FastAPI server running (`uvicorn app.main:app --reload`)?",
        icon=":material/error:",
    )
    st.stop()

unit = user["preferred_unit"]
today = date.today()
days = st.slider("Show last N days", min_value=30, max_value=365, value=90, step=30)
range_start = today - timedelta(days=days)


def timeseries_chart(df: pd.DataFrame, x: str, y: str, y_title: str, color: str) -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X(f"{x}:T", title="Date"),
            y=alt.Y(f"{y}:Q", title=y_title),
            color=alt.value(color),
            tooltip=[
                alt.Tooltip(f"{x}:T", title="Date", format="%b %d, %Y"),
                alt.Tooltip(f"{y}:Q", title=y_title, format=".1f"),
            ],
        )
    )


# ---------------------------------------------------------------------
# Body weight
# ---------------------------------------------------------------------
with st.container(border=True):
    st.subheader(":material/monitor_weight: Body weight", divider="orange")

    with st.expander("Log today's weight", icon=":material/add_circle:"):
        with st.container(horizontal=True):
            weight_value = st.number_input("Weight", min_value=0.0, step=0.5, key="bw_value")
            weight_unit = st.selectbox(
                "Unit", options=["lbs", "kg"], index=0 if unit == "lbs" else 1, key="bw_unit"
            )
        if st.button("Save weight", type="primary", icon=":material/save:"):
            api.add_body_metric(USER_ID, today, weight_value, weight_unit)
            st.toast("Weight saved", icon=":material/check:")
            st.rerun()

    metrics = api.list_body_metrics(USER_ID, date_from=range_start, date_to=today)
    if not metrics:
        st.caption("No body weight entries yet.")
    else:
        df = pd.DataFrame(metrics)
        df["metric_date"] = pd.to_datetime(df["metric_date"])
        df["weight_display"] = df["weight_kg"].astype(float).apply(lambda kg: kg_to_display(kg, unit))
        st.altair_chart(timeseries_chart(df, "metric_date", "weight_display", f"Weight ({unit})", BLUE))

# ---------------------------------------------------------------------
# Exercise progression
# ---------------------------------------------------------------------
with st.container(border=True):
    st.subheader(":material/trending_up: Exercise progression", divider="orange")

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
        st.caption(f"No logged sets for {chosen['name']} in this range yet.")
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
            st.altair_chart(
                timeseries_chart(pdf, "session_date", "top_weight_display", f"Top weight ({unit})", ORANGE)
            )
        with col2:
            st.caption(f"Session volume ({unit})")
            st.altair_chart(
                timeseries_chart(pdf, "session_date", "volume_display", f"Volume ({unit})", AQUA)
            )

# ---------------------------------------------------------------------
# Volume comparison (rolling windows, not calendar week/month — avoids
# comparing a partial current period against a full prior one)
# ---------------------------------------------------------------------
with st.container(border=True):
    st.subheader(":material/bar_chart: Volume comparison", divider="orange")
    st.caption("Rolling windows ending today, not calendar week/month.")

    last7_start = today - timedelta(days=6)
    prev7_start = last7_start - timedelta(days=7)
    prev7_end = last7_start - timedelta(days=1)

    last30_start = today - timedelta(days=29)
    prev30_start = last30_start - timedelta(days=30)
    prev30_end = last30_start - timedelta(days=1)

    volume_rows = api.session_volume(USER_ID, date_from=prev30_start, date_to=today)
    daily_kg = {r["session_date"]: float(r["total_volume_kg"]) for r in volume_rows}

    def window_total(start, end):
        return sum(
            kg for d, kg in daily_kg.items() if start <= date.fromisoformat(d) <= end
        )

    def daily_series(start, end):
        d, values = start, []
        while d <= end:
            values.append(kg_to_display(daily_kg.get(d.isoformat(), 0.0), unit))
            d += timedelta(days=1)
        return values

    this_week_total = window_total(last7_start, today)
    last_week_total = window_total(prev7_start, prev7_end)
    this_month_total = window_total(last30_start, today)
    last_month_total = window_total(prev30_start, prev30_end)

    with st.container(horizontal=True):
        st.metric(
            "Last 7 days volume",
            f"{kg_to_display(this_week_total, unit):,.0f} {unit}",
            delta=f"{kg_to_display(this_week_total - last_week_total, unit):,.0f} {unit} vs prior 7 days",
            border=True,
            chart_data=daily_series(last7_start, today),
            chart_type="bar",
        )
        st.metric(
            "Last 30 days volume",
            f"{kg_to_display(this_month_total, unit):,.0f} {unit}",
            delta=f"{kg_to_display(this_month_total - last_month_total, unit):,.0f} {unit} vs prior 30 days",
            border=True,
            chart_data=daily_series(last30_start, today),
            chart_type="bar",
        )
