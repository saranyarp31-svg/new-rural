import streamlit as st
from deep_translator import GoogleTranslator
import pandas as pd
import requests
import os
from datetime import datetime
import asyncio
import edge_tts
from legal_db import LEGAL_DB

# ---------------------------------------------------
# Streamlit Page Setup
# ---------------------------------------------------
st.set_page_config(page_title="Rural ACT - Tamil Legal Translator", layout="wide")

st.title("🌾 Rural ACT – Tamil Legal Awareness Translator")
st.write("Translate English → Tamil + Legal Detection + Tamil Voice Output (Edge-TTS)")


# ---------------------------------------------------
# Tamil TTS using Edge-TTS (Works on Streamlit Cloud)
# ---------------------------------------------------
async def create_tts(text):
    try:
        communicate = edge_tts.Communicate(text, "ta-IN-ValluvarNeural")  # Tamil Male voice
        await communicate.save("tamil_voice.mp3")
        return "tamil_voice.mp3"
    except:
        return None

def generate_audio(text):
    try:
        return asyncio.run(create_tts(text))
    except:
        return None


# ---------------------------------------------------
# Save Feedback
# ---------------------------------------------------
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


# ---------------------------------------------------
# Legal Keyword Detection
# ---------------------------------------------------
def detect_legal_section(text):
    text_low = text.lower()
    for keyword, info in LEGAL_DB.items():
        if keyword in text_low:
            return info
    return None


# ---------------------------------------------------
# UI Input Box
# ---------------------------------------------------
user_input = st.text_area("Enter English text:", height=160)


# ---------------------------------------------------
# Main Logic
# ---------------------------------------------------
if st.button("Translate & Analyze"):
    if not user_input.strip():
        st.warning("Please enter some text.")
        st.stop()

    # Translate to Tamil
    try:
        tamil_text = GoogleTranslator(source="auto", target="ta").translate(user_input)
        st.subheader("📌 Tamil Translation")
        st.success(tamil_text)
    except Exception as e:
        st.error("Translation failed: " + str(e))
        tamil_text = ""

    # Tamil Voice Output
    st.subheader("🔊 Tamil Voice Output")
    audio_file = generate_audio(tamil_text)

    if audio_file:
        st.audio(audio_file)
    else:
        st.warning("Voice not available right now.")

    # Legal Detection
    st.subheader("⚖️ Legal Awareness")

    legal = detect_legal_section(user_input)

    if legal:
        st.write(f"**Section:** {legal['section']}")
        st.write(f"**Explanation:** {legal['tamil']}")
        st.write(f"**Punishment:** {legal['punishment']}")
        st.write(f"**Helpline:** {legal['helpline']}")
        st.info(f"Example: {legal['example']}")
        section_name = legal["section"]
    else:
        st.info("No legal issues detected.")
        section_name = "None"

    # Feedback System
    st.subheader("📝 Feedback")

    col1, col2 = st.columns(2)

    if col1.button("✅ Understand"):
        save_feedback(user_input, tamil_text, section_name, "Understand")
        st.success("Feedback saved!")

    if col2.button("❌ Not Understand"):
        need = st.radio("What do you need help with?", ["Text", "Voice", "Both"])
        save_feedback(user_input, tamil_text, section_name, "Not Understand", need)
        st.error("Feedback saved. We will improve!")


# Developer Option
if st.checkbox("Show Feedback Log (Developer Only)"):
    if os.path.exists("user_feedback.csv"):
        df = pd.read_csv("user_feedback.csv")
        st.dataframe(df.tail(20))
    else:
        st.info("No feedback available yet.")



