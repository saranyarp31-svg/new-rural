import streamlit as st
from deep_translator import GoogleTranslator
from gtts import gTTS
import pandas as pd
import re
import os
from datetime import datetime

from legal_db import LEGAL_DB

st.set_page_config(page_title="Rural ACT - Tamil Legal Translator", layout="wide")

# -----------------------
# Utility: Save Feedback
# -----------------------

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

# -----------------------
# Legal Keyword Detection
# -----------------------

def detect_legal_section(text):
    text = text.lower()
    for keyword, info in LEGAL_DB.items():
        if keyword in text:
            return info
    return None

# -----------------------
# Tamil TTS Generator
# -----------------------

def generate_audio(text):
    tts = gTTS(text=text, lang="ta")
    file_path = "audio_output.mp3"
    tts.save(file_path)
    return file_path

# -----------------------
# Streamlit UI
# -----------------------

st.title("🌾 Rural ACT – AI Powered Tamil Legal Awareness Translator")
st.write("Translate English → Tamil + Detect Legal Sections + Voice Output")

user_input = st.text_area("Enter the English message here:")

if st.button("Translate & Analyze"):
    if user_input.strip() == "":
        st.warning("Please enter some text.")
        st.stop()

    # Translation
    tamil_text = GoogleTranslator(source="auto", target="ta").translate(user_input)

    st.subheader("📌 Tamil Translation")
    st.success(tamil_text)

    # Audio
    audio_file = generate_audio(tamil_text)
    st.audio(audio_file)

    # Legal Detection
    legal = detect_legal_section(user_input)

    if legal:
        st.subheader("⚖️ Legal Awareness Detected")
        st.write(f"**Section:** {legal['section']}")
        st.write(f"**Explanation (Tamil):** {legal['tamil']}")
        st.write(f"**Punishment:** {legal['punishment']}")
        st.write(f"**Helpline:** {legal['helpline']}")
        st.info(f"Example: {legal['example']}")

        section_name = legal['section']
    else:
        st.info("No legal issues detected.")
        section_name = "None"

    # Feedback
    st.subheader("📝 User Feedback")
    col1, col2 = st.columns(2)

    if col1.button("✅ Understand"):
        save_feedback(user_input, tamil_text, section_name, "Understand")
        st.success("Thank you! Feedback saved.")

    if col2.button("❌ Not Understand"):
        choice = st.radio("What do you need?", ["Text", "Voice", "Both"])

        save_feedback(user_input, tamil_text, section_name, "Not Understand", choice)
        st.error("Feedback saved. We will improve the explanation.")

