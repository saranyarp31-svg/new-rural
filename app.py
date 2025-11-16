import streamlit as st
from deep_translator import GoogleTranslator
from TTS.api import TTS
import pandas as pd
import os
from datetime import datetime
import re

from legal_db import LEGAL_DB

st.set_page_config(page_title="Rural ACT - Tamil Legal Translator", layout="wide")

# ---------------------------------------
# Load TTS Model (Cache to avoid reloading)
# ---------------------------------------

@st.cache_resource
def load_tts_model():
    return TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")

tts_model = load_tts_model()


# ---------------------------------------
# Save user feedback
# ---------------------------------------

def save_feedback(original, tamil, section, fb_type, fb_detail=""):
    data = {
        "timestamp": [datetime.now()],
        "english_input": [original],
        "tamil_output": [tamil],
        "legal_section": [section],
        "feedback_type": [fb_type],
        "feedback_detail": [fb_detail]
    }

    df = pd.DataFrame(data)

    if os.path.exists("user_feedback.csv"):
        df.to_csv("user_feedback.csv", mode="a", header=False, index=False)
    else:
        df.to_csv("user_feedback.csv", index=False)


# ---------------------------------------
# Detect legal section based on keywords
# ---------------------------------------

def detect_legal_section(text):
    text = text.lower()
    for keyword, info in LEGAL_DB.items():
        if keyword in text:
            return info
    return None


# ---------------------------------------
# Generate Tamil Speech Offline
# ---------------------------------------

def generate_audio(text):
    file_path = "tamil_audio.wav"
    try:
        tts_model.tts_to_file(
            text=text,
            file_path=file_path,
            speaker_wav=None,
            language="ta"
        )
        return file_path
    except Exception as e:
        return None



# ---------------------------------------
# STREAMLIT UI
# ---------------------------------------

st.title("🌾 Rural ACT – AI Tamil Legal Awareness System")
st.write("Instant English → Tamil Translation + Legal Alert + Offline Tamil Audio")


user_input = st.text_area("Enter the English message here:", height=150)


if st.button("Translate & Analyze"):
    if not user_input.strip():
        st.warning("⚠️ Please enter some text.")
        st.stop()

    # Translation
    tamil_text = GoogleTranslator(source="en", target="ta").translate(user_input)

    st.subheader("📌 Tamil Translation")
    st.success(tamil_text)

    # Tamil Voice Output
    audio_file = generate_audio(tamil_text)

    if audio_file:
        st.audio(audio_file)
    else:
        st.warning("⚠️ Voice generation unavailable. Try again later.")

    # Legal Section Detection
    legal = detect_legal_section(user_input)

    st.subheader("⚖️ Legal Awareness")

    if legal:
        st.write(f"**Section:** {legal['section']}")
        st.write(f"**Explanation (Tamil):** {legal['tamil']}")
        st.write(f"**Punishment:** {legal['punishment']}")
        st.write(f"**Helpline:** {legal['helpline']}")
        st.info(f"Example: {legal['example']}")

        section_name = legal["section"]
    else:
        st.info("No legal issues detected in this message.")
        section_name = "None"

    # Feedback Section
    st.subheader("📝 User Feedback")

    col1, col2 = st.columns(2)

    if col1.button("✅ Understand"):
        save_feedback(user_input, tamil_text, section_name, "Understand")
        st.success("Feedback saved. Thank you!")

    if col2.button("❌ Not Understand"):
        choice = st.radio("What do you need more?", ["Text", "Voice", "Both"])
        save_feedback(user_input, tamil_text, section_name, "Not Understand", choice)
        st.error("We will improve this. Feedback saved.")


