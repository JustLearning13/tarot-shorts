import os
import streamlit as st
import glob

from deck import load_deck, pick_card, DECK_DIR
from question_agent import decide_question

st.set_page_config(page_title="Tarot Video Generator", layout="centered")
st.title("Tarot Video Generator")

# Load deck once, cached so it doesn't reload on every rerun
@st.cache_data
def get_deck():
    return load_deck()

deck = get_deck()

# --- Session state setup: these persist across Streamlit reruns ---
if "reasoning" not in st.session_state:
    st.session_state.reasoning = None
if "question" not in st.session_state:
    st.session_state.question = None
if "viewer_intro" not in st.session_state:
    st.session_state.viewer_intro = None
if "card" not in st.session_state:
    st.session_state.card = None

# --- SECTION 1: Question ---
st.header("1. Question")

if st.button("Ask agent to generate a question"):
    with st.spinner("Agent is thinking..."):
        result = decide_question()
    st.session_state.question = result["question"]
    st.session_state.viewer_intro = result["viewer_intro"]
    st.session_state.reasoning = result["reasoning"]

st.session_state.question = st.text_area(
    "Question (edit the agent's suggestion, or type your own):",
    value=st.session_state.question or "",
    height=80
)

if st.session_state.question:
    st.session_state.viewer_intro = st.text_area(
        "Viewer intro (editable):",
        value=st.session_state.viewer_intro or "",
        height=80
    )
    if st.session_state.reasoning:
        with st.expander("Why the agent chose this"):
            st.write(st.session_state.reasoning)

# --- SECTION 2: Card ---
st.header("2. Card")

card_names = ["Random"] + [c["name"] for c in deck]
selected = st.selectbox("Pick a specific card, or leave Random:", card_names)

if st.button("Draw card"):
    name_arg = None if selected == "Random" else selected
    st.session_state.card = pick_card(deck, name_arg)

if st.session_state.card:
    card = st.session_state.card
    image_path = os.path.join(DECK_DIR, "images", card["image_file"])
    st.image(image_path, caption=card["name"], width=300)
    st.caption(f"Upright meaning: {card['upright_meaning']}")

from ai_text import generate_tarot_reading, translate_text, build_narration_script

# --- Session state additions ---
if "reading" not in st.session_state:
    st.session_state.reading = None
if "language" not in st.session_state:
    st.session_state.language = "en"
if "narration" not in st.session_state:
    st.session_state.narration = None

# --- SECTION 3: Reading ---
st.header("3. Reading")

if st.session_state.card and st.session_state.question:
    if st.button("Generate reading"):
        with st.spinner("Consulting the cards..."):
            st.session_state.reading = generate_tarot_reading(
                st.session_state.question, st.session_state.card
            )

    if st.session_state.reading:
        st.session_state.reading = st.text_area(
            "Reading (editable):", value=st.session_state.reading, height=120
        )
else:
    st.info("Set a question and draw a card first.")

from critique_agent import critique_video_script

# --- SECTION 4: Critique (on demand) ---
st.header("4. Critique (optional)")

if st.session_state.reading:
    if st.button("Ask critique agent for feedback"):
        est_words = len(f"{st.session_state.viewer_intro} {st.session_state.reading}".split())
        est_duration = est_words / 2.4  # rough speaking-pace estimate

        with st.spinner("Getting feedback..."):
            critique = critique_video_script(
                st.session_state.question,
                st.session_state.viewer_intro,
                st.session_state.card,
                st.session_state.reading,
                est_duration
            )

        verdict = critique["verdict"]
        if verdict == "good_to_post":
            st.success(f"**Verdict:** {verdict}")
        elif verdict == "minor_tweaks_suggested":
            st.warning(f"**Verdict:** {verdict}")
        else:
            st.error(f"**Verdict:** {verdict}")

        st.write(critique["critique"])
        if critique["suggested_fix"]:
            st.info(f"**Suggested fix:** {critique['suggested_fix']}")
else:
    st.info("Generate a reading first.")    

# --- SECTION 5: Translation ---
st.header("5. Translation & Narration")

if st.session_state.reading:
    st.session_state.language = st.selectbox(
        "Language:", ["en", "uk", "es"],
        index=["en", "uk", "es"].index(st.session_state.language)
    )

    if st.button("Build narration"):
        narration_en = build_narration_script(
            st.session_state.question,
            st.session_state.viewer_intro,
            st.session_state.card,
            st.session_state.reading
        )
        with st.spinner("Translating..."):
            st.session_state.narration = translate_text(narration_en, st.session_state.language)
    if st.session_state.narration:
        st.session_state.narration = st.text_area(
            "Final narration (editable):", value=st.session_state.narration, height=150
        )
else:
    st.info("Generate a reading first.")

import os
from datetime import datetime
from voice import text_to_speech, transcribe_audio
from video import create_video

if "audio_file" not in st.session_state:
    st.session_state.audio_file = None
if "video_file" not in st.session_state:
    st.session_state.video_file = None

# --- SECTION 6: Audio ---
st.header("6. Audio")

if st.session_state.narration:
    if st.button("Generate audio"):
        os.makedirs("output", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        card_slug = st.session_state.card["image_file"].replace(".png", "")
        audio_path = f"output/{timestamp}_{card_slug}.wav"

        with st.spinner("Generating audio..."):
            text_to_speech(st.session_state.narration, audio_path)

        st.session_state.audio_file = audio_path
        st.session_state.video_file = None  # reset, since audio changed

    if st.session_state.audio_file:
        st.audio(st.session_state.audio_file)
        st.caption("Not happy with it? Click 'Generate audio' again to redo.")
else:
    st.info("Build the narration first.")

# --- SECTION 7: Video ---
st.header("7. Video")

if st.session_state.audio_file:
    music_files = glob.glob("assets/music/*.mp3") + glob.glob("assets/music/*.wav")
    music_choice = st.selectbox("Background music:", ["None"] + music_files)
    music_path = None if music_choice == "None" else music_choice

    if st.button("Generate video"):
        card = st.session_state.card
        card_image = os.path.join(DECK_DIR, "images", card["image_file"])
        video_path = st.session_state.audio_file.replace(".wav", ".mp4")

        with st.spinner("Transcribing audio..."):
            words = transcribe_audio(st.session_state.audio_file)

        with st.spinner("Rendering video..."):
            create_video(card_image, words, st.session_state.audio_file, video_path, music_file=music_path)
        st.session_state.video_file = video_path

    if st.session_state.video_file:
        st.video(st.session_state.video_file)
        st.success("Video ready!")
else:
    st.info("Generate audio first.")    