import streamlit as st
from deep_translator import GoogleTranslator
import pandas as pd
import requests
import os
from datetime import datetime
from legal_db import LEGAL_DB

# ---------------------------------------------------
# Streamlit App Settings
# ---------------------------------------------------
st.set_page_config(
    page_title="Rural ACT - Tamil Legal Awareness Translator",
    layout="wide"
)

st.title("🌾 Rural ACT – Tamil Legal Awareness Translator")
st.write("Translate English → Tamil + Legal Detection + Tamil Voice Output (via HuggingFace TTS)")


# ---------------------------------------------------
# Feedback Save Function
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
# Legal Detection Function
# ---------------------------------------------------
def detect_legal_section(text):
    text_low = text.lower()
    for keyword, info in LEGAL_DB.items():
        if keyword in text_low:
            return info
    return None


# ---------------------------------------------------
# HuggingFace Tamil TTS Function (Works on Streamlit Cloud)
# ---------------------------------------------------
def generate_audio(text):
    api_url = "https://api-inference.huggingface.co/models/facebook/mms-tts-tam"

    if "HF_TOKEN" not in st.secrets:
        st.error("HuggingFace token missing! Add HF_TOKEN in Streamlit Secrets.")
        return None

    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    payload = {"inputs": text}

    try:
        response = requests.post(api_url, headers=headers, json=payload)

        if response.status_code == 200:
            audio_path = "tamil_audio.mp3"
            with open(audio_path, "wb") as f:
                f.write(response.content)
            return audio_path
        else:
            st.warning("TTS request failed. Status code: " + str(response.status_code))
            return None

    except Exception as e:
        st.warning("Audio generation error: " + str(e))
        return None


# ---------------------------------------------------
# UI – Input Box
# ---------------------------------------------------
user_input = st.text_area("Enter English text to translate:", height=160)


# ---------------------------------------------------
# Button Click
# ---------------------------------------------------
if st.button("Translate & Analyze"):
    if not user_input.strip():
        st.warning("Please type some English text.")
        st.stop()

    # Translation
    try:
        tamil_text = GoogleTranslator(source="auto", target="ta").translate(user_input)
        st.subheader("📌 Tamil Translation")
        st.success(tamil_text)
    except Exception as e:
        st.error("Translation failed: " + str(e))
        tamil_text = ""

    # Audio (Tamil Voice)
    st.subheader("🔊 Tamil Voice Output")
    audio_file = generate_audio(tamil_text)

    if audio_file:
        st.audio(audio_file)
    else:
        st.warning("Voice output unavailable right now.")

    # Legal Section Detection
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

    # Feedback Section
    st.subheader("📝 User Feedback")
    col1, col2 = st.columns(2)

    if col1.button("✅ I Understood"):
        save_feedback(user_input, tamil_text, section_name, "Understand")
        st.success("Thank you! Feedback saved.")

    if col2.button("❌ I Did Not Understand"):
        need = st.radio("What help do you need?", ["Text", "Voice", "Both"])
        save_feedback(user_input, tamil_text, section_name, "Not Understand", need)
        st.error("Feedback saved. We will improve the explanation.")

# Developer Option to View Feedback
if st.checkbox("Show Feedback Log (Developer Only)"):
    if os.path.exists("user_feedback.csv"):
        df = pd.read_csv("user_feedback.csv")
        st.dataframe(df.tail(30))
    else:
        st.info("No feedback available yet.")



