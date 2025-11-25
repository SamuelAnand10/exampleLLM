"""
Streamlit wrapper for an external Gradio app (center-only version).

This version:
- Shows ONLY the embedded Gradio app in the main column.
- Removes the entire right-hand API proxy / uploader section.
"""

import streamlit as st
from streamlit.components.v1 import html
import urllib.parse

# === Configuration ===
GRADIO_URL = "https://fde6743ee03d00eada.gradio.live/"  # your Gradio share link
DEFAULT_HEIGHT = 800

# === Page setup ===
st.set_page_config(page_title="Gradio in Streamlit", layout="wide")
st.title("Gradio App Embedded in Streamlit")

st.markdown(
    "This is a simple embed of your Gradio app inside Streamlit. "
    "Use the sidebar to adjust the frame height or open the app in a new tab."
)

# === Sidebar ===
with st.sidebar:
    st.header("Controls")
    height = st.slider("Iframe height (px)", 400, 2000, value=DEFAULT_HEIGHT, step=50)
    show_frame_border = st.checkbox("Show frame border", value=False)

    if st.button("Open Gradio in new tab"):
        js = f"window.open('{GRADIO_URL}', '_blank').focus();"
        st.markdown(f"<script>{js}</script>", unsafe_allow_html=True)

    st.markdown("---")
    st.code(GRADIO_URL, language="url")

# === Embedded iframe only (center UI) ===
frame_border_style = "1px solid #ddd" if show_frame_border else "none"

iframe_html = (
    f'<iframe src="{urllib.parse.quote(GRADIO_URL, safe=":/?#[]@!$&\'()*+,;=%")}" '
    f'style="width:100%;height:{height}px;border:{frame_border_style};border-radius:8px;" '
    f'allowfullscreen></iframe>'
)

html(iframe_html, height=height + 20)

# Optional embed code section
st.markdown("---")
st.subheader("Embed HTML")
st.code(iframe_html, language="html")

st.caption("If you'd like, I can convert your Falcon LoRA model to a native Streamlit chat UI instead of using Gradio.")
