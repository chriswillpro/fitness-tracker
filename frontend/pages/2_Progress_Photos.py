"""Streamlit frontend — progress photo upload and gallery."""

from datetime import date, datetime

import requests
import streamlit as st

import api_client as api

USER_ID = 1

st.set_page_config(
    page_title="Fitness Tracker — Progress photos",
    page_icon=":material/photo_camera:",
    layout="centered",
)
st.title(":material/photo_camera: Progress photos")

try:
    api.get_user(USER_ID)
except requests.exceptions.ConnectionError:
    st.error(
        f"Can't reach the API at {api.API_BASE_URL}. "
        "Is the FastAPI server running (`uvicorn app.main:app --reload`)?",
        icon=":material/error:",
    )
    st.stop()

with st.container(border=True):
    st.subheader("Add a photo", divider="orange")

    photo_date = st.date_input("Date taken", value=date.today())
    uploaded = st.file_uploader("Photo", type=["jpg", "jpeg", "png", "webp"])

    metrics_on_date = api.list_body_metrics(USER_ID, date_from=photo_date, date_to=photo_date)
    linked_metric = metrics_on_date[0] if metrics_on_date else None
    if linked_metric:
        st.caption(
            f":material/link: Will link to your {photo_date} weigh-in: "
            f"{linked_metric['weight_value']} {linked_metric['weight_unit']}"
        )
    else:
        st.caption(f"No weigh-in logged for {photo_date} — photo will be saved without a linked weight.")

    if st.button(
        "Upload photo", type="primary", icon=":material/upload:", disabled=uploaded is None
    ):
        taken_at = datetime.combine(photo_date, datetime.now().time())
        api.upload_progress_photo(
            USER_ID,
            filename=uploaded.name,
            content_type=uploaded.type,
            file_bytes=uploaded.getvalue(),
            body_metric_id=linked_metric["id"] if linked_metric else None,
            taken_at=taken_at,
        )
        st.success("Photo uploaded", icon=":material/check_circle:")
        st.rerun()

st.subheader("Gallery", divider="orange")

photos = api.list_progress_photos(USER_ID)
if not photos:
    st.caption("No progress photos yet — add one above to get started.")
else:
    cols = st.columns(3)
    for i, photo in enumerate(photos):
        with cols[i % 3]:
            with st.container(border=True):
                st.image(api.API_BASE_URL + photo["photo_url"], width="stretch")
                caption = photo["taken_at"][:10]
                if photo["body_metric_id"]:
                    caption += " · linked to weigh-in"
                st.caption(caption)
                if st.button(
                    "Delete", key=f"delphoto_{photo['id']}", type="tertiary", icon=":material/delete:"
                ):
                    api.delete_progress_photo(photo["id"])
                    st.rerun()
