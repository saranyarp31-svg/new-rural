import streamlit as st
from deep_translator import GoogleTranslator
import pandas as pd
import os
import requests
from datetime import datetime
from legal_db import LEGAL_DB

st.set_page_config(page_title="Rural ACT - Tamil Legal Translator", layout="wide")

# -------------------------
# Helper: Save feedback CSV
# -------------------------
def save_feedback(original, tamil, section, fb_type, fb_detail=""):
    data = {
        "timestamp": [datetime.now().isoformat()],
        "english_input": [original],
        "tamil_output": [tamil],
        "legal_section": [section],
        "feedback_type": [fb_type],
        "feedback_detail": [fb_detail]
    }
    df = pd.DataFrame(data)
    fname = "user_feedback.csv"
    if os.path.exists(fname):
        df.to_csv(fname, mode="a", header=False, index=False)
    else:
        df.to_csv(fname, index=False)

# -------------------------
# Keyword-based legal detect
# -------------------------
def detect_legal_section(text):
    text_lower = text.lower()
    for k, info in LEGAL_DB.items():
        if k in text_lower:
            return info
    return None

# -------------------------
# Hugging Face TTS via inference API
# -------------------------
def generate_tts_hf(text, model="google/mattts-tts-tamil", out_path="tamil_audio.wav"):
    """
    Generates audio using HuggingFace Inference API.
    Requires HF token stored in Streamlit secrets as HF_TOKEN.
    Returns path to saved audio or None on error.
    """
    if "HF_TOKEN" not in st.secrets:
        st.error("HuggingFace token not found in Streamlit secrets. Add HF_TOKEN first.")
        return None

    api_url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    payload = {"inputs": text}

    try:
        # POST request (binary audio returned)
        resp = requests.post(api_url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200 and resp.content:
            with open(out_path, "wb") as f:
                f.write(resp.content)
            return out_path
        else:
            # Helpful debug info in app logs for developer
            st.warning(f"TTS request failed (status {resp.status_code}).")
            return None
    except Exception as e:
        st.warning("TTS request error: " + str(e))
        return None

# -------------------------
# Streamlit UI
# -------------------------
st.title("🌾 Rural ACT – Tamil Legal Awareness Translator")
st.write("Enter an English message, get Tamil translation + legal awareness + Tamil audio (via HuggingFace).")

input_text = st.text_area("Enter English message:", height=160)

if st.button("Translate & Analyze"):
    if not input_text.strip():
        st.warning("Please write or paste the English message.")
        st.stop()

    # Translate English -> Tamil
    try:
        tamil_text = GoogleTranslator(source="auto", target="ta").translate(input_text)
    except Exception as e:
        st.error("Translation failed: " + str(e))
        tamil_text = ""

    st.subheader("📌 Tamil Translation")
    if tamil_text:
        st.success(tamil_text)
    else:
        st.info("Translation returned empty.")

    # Try generate TTS using HuggingFace
    tts_path = generate_tts_hf(tamil_text)

    if tts_path:
        st.audio(tts_path)
    else:
        st.info("Voice output not available. You can still read the Tamil text.")

    # Legal detection
    legal = detect_legal_section(input_text)
    st.subheader("⚖️ Legal Awareness")
    if legal:
        st.write(f"**Section:** {legal['section']}")
        st.write(f"**Explanation (Tamil):** {legal['tamil']}")
        st.write(f"**Punishment:** {legal['punishment']}")
        st.write(f"**Helpline:** {legal['helpline']}")
        st.info(f"Example: {legal['example']}")
        section_name = legal["section"]
    else:
        st.info("No legal keywords detected.")
        section_name = "None"

    # Feedback UI
    st.subheader("📝 Feedback")
    col1, col2 = st.columns(2)
    if col1.button("✅ Understand"):
        save_feedback(input_text, tamil_text, section_name, "Understand")
        st.success("Thanks — feedback saved.")
    if col2.button("❌ Not Understand"):
        fb_choice = st.radio("Would you like clarification via:", ["Text", "Voice", "Both"])
        save_feedback(input_text, tamil_text, section_name, "Not Understand", fb_choice)
        st.error("Feedback saved. We'll improve the explanation.")

# Show stored feedback (developer convenience)
if st.checkbox("Show feedback CSV (developer)"):
    if os.path.exists("user_feedback.csv"):
        df = pd.read_csv("user_feedback.csv")
        st.dataframe(df.tail(50))
    else:
        st.info("No feedback yet.")



