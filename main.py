"""
Streamlit wrapper for an external Gradio app (one-file).

This version adds:
- An iframe embed of your Gradio share link (as before).
- A small "API proxy" that attempts to POST prompts to the Gradio app's `/api/predict/` endpoint (works if the Gradio app exposes it).
- File upload UI: uploads a local file to the Gradio API if the remote app accepts files as the first argument in the `data` array. (This is a best-effort helper — many Gradio apps will accept JSON posts to `/api/predict/` but some are locked or require CORS/auth.)
- Clear error messages and fallbacks (open in new tab, copy embed HTML).

How to run
-----------
1. Save this file as `streamlit_gradio_app.py`.
2. Install dependencies:
   pip install streamlit requests
3. Run:
   streamlit run streamlit_gradio_app.py

Limitations / Notes
-------------------
- If the Gradio share server blocks embedding or API calls (CORS, X-Frame-Options, or no `/api/predict/`), the iframe may be blank and the API proxy will fail. In that case use "Open in new tab" or run the model locally in Colab and expose an API.
- The POST format to `/api/predict/` is `{"data": [ ...inputs in order... ]}`. This code assumes the Gradio app takes exactly [prompt, max_new_tokens, temperature, top_p] (matching your Colab script). If the remote Gradio app expects different input ordering or file types, change the `build_payload` function accordingly.
"""

import streamlit as st
from streamlit.components.v1 import html
import urllib.parse
import requests
import json
import base64

# === Configuration ===
GRADIO_URL = "https://fde6743ee03d00eada.gradio.live/"  # your Gradio share link
GRADIO_API_PREDICT = urllib.parse.urljoin(GRADIO_URL, "api/predict/")
DEFAULT_HEIGHT = 800

st.set_page_config(page_title="Gradio in Streamlit (with proxy)", layout="wide")
st.title("Streamlit wrapper for Gradio (embed + API proxy)")
st.markdown("This page embeds your Gradio app and — when possible — will attempt to call the Gradio `/api/predict/` endpoint directly from Streamlit.")

# Sidebar controls
with st.sidebar:
    st.header("Controls & debug")
    height = st.slider("Iframe height (px)", 400, 2000, value=DEFAULT_HEIGHT, step=50)
    show_frame_border = st.checkbox("Show frame border", value=False)
    if st.button("Open Gradio app in new tab"):
        js = f"window.open('{GRADIO_URL}', '_blank').focus();"
        st.markdown(f"<script>{js}</script>", unsafe_allow_html=True)
    st.markdown("---")
    st.write("Gradio URL:")
    st.code(GRADIO_URL, language="url")
    st.write("Gradio predict endpoint (attempt):")
    st.code(GRADIO_API_PREDICT, language="url")
    st.markdown("**Note:** If API calls fail, the remote Gradio server may not allow programmatic access or may expect different input ordering/types.")

# Main layout: left = embed, right = quick proxy form
col1, col2 = st.columns([2,1])

with col1:
    st.subheader("Embedded Gradio app")
    frame_border_style = "1px solid #ddd" if show_frame_border else "none"
    iframe_html = f'<iframe src="{urllib.parse.quote(GRADIO_URL, safe=":/?#[]@!$&'()*+,;=%")}" style="width:100%;height:{height}px;border:{frame_border_style};border-radius:8px;" allowfullscreen></iframe>'
    html(iframe_html, height=height + 20)

    st.markdown("---")
    st.subheader("Embed HTML (copy-paste)")
    st.code(iframe_html, language="html")

with col2:
    st.subheader("Quick proxy: call Gradio /api/predict/")
    st.markdown("(Best-effort — works if the remote Gradio instance exposes the predict API and accepts the inputs in the expected order.)")

    # Inputs matching your Colab Gradio signature: [prompt, max_new_tokens, temperature, top_p]
    prompt = st.text_area("Prompt", value="Hello, how are you?", height=120)
    max_new_tokens = st.number_input("max_new_tokens", min_value=1, max_value=1024, value=128)
    temperature = st.number_input("temperature", min_value=0.01, max_value=2.0, value=0.7, format="%.2f")
    top_p = st.number_input("top_p", min_value=0.01, max_value=1.0, value=0.95, format="%.2f")
    st.markdown("**Optional:** upload a file to forward to the Gradio app (if it expects a file input).")
    uploaded_file = st.file_uploader("Upload file (optional)")

    def build_payload(prompt_text, mt, temp_val, top_p_val, uploaded=None):
        # Default payload assumes the Gradio app inputs were defined in this order:
        # [prompt, max_new_tokens, temperature, top_p]
        # If a file is present and the remote app expects a file as first argument,
        # insert the file as base64 string (Gradio may accept a URL or raw bytes depending on server).
        data = [prompt_text, int(mt), float(temp_val), float(top_p_val)]
        if uploaded is not None:
            # convert file to base64 and prepend to data array — this might or might not match the remote app's expectation
            contents = uploaded.read()
            b64 = base64.b64encode(contents).decode('utf-8')
            # Commonly Gradio file inputs expect either a URL or a dict with name/data. We'll send a dict as best-effort.
            file_placeholder = {"name": uploaded.name, "data": b64}
            # Put the file as first argument
            data = [file_placeholder] + data
        return {"data": data}

    if st.button("Send to Gradio predict API"):
        payload = build_payload(prompt, max_new_tokens, temperature, top_p, uploaded_file)
        st.write("POST ->", GRADIO_API_PREDICT)
        st.write("Payload preview:")
        st.text(json.dumps(payload, indent=2)[:1000] + ("..." if len(json.dumps(payload))>1000 else ""))
        try:
            resp = requests.post(GRADIO_API_PREDICT, json=payload, timeout=30)
            st.write("Status:", resp.status_code)
            try:
                j = resp.json()
                st.subheader("Response JSON")
                st.json(j)
                # If the standard Gradio /api/predict/ returns {'data': [<return values...>]}
                if isinstance(j, dict) and 'data' in j and isinstance(j['data'], list):
                    st.markdown("**Interpreted model outputs (first item shown):**")
                    st.write(j['data'][0])
            except Exception as e:
                st.error("Failed to parse JSON response: " + str(e))
                st.text(resp.text[:2000])
        except Exception as e:
            st.error("Request failed: " + str(e))
            st.info("If this fails, try opening the Gradio app in a new tab or run the model locally in Colab. Common causes: remote server blocks programmatic access, CORS or the endpoint path is different.")

st.markdown("---")
st.caption("If you want, I can: (1) add a reverse-proxy example (Flask/NGINX) to rehost the Gradio app with permissive headers, (2) convert your Colab Gradio script into a Streamlit app that runs the model locally, or (3) generate a requirements.txt and deployment steps for a cloud VM. Tell me which and I'll produce the code.")
