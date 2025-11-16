import random
import requests
import streamlit as st
import pandas as pd
import os
from pathlib import Path


# if os.path.exists(CSV_PATH):
#     try:
#         df = pd.read_csv(CSV_PATH)

#         if "word" in df.columns:
#             pre_words = (
#                 df["word"]
#                 .dropna()
#                 .astype(str)
#                 .str.strip()
#                 .str.lower()
#                 .tolist()
#             )

#             for w in pre_words:
#                 if w not in st.session_state.word_list:
#                     st.session_state.word_list.append(w)

#             print(f"Pre-loaded {len(pre_words)} words from CSV.")
#         else:
#             print("CSV found, but no 'word' column.")
#     except Exception as e:
#         print(f"Error loading CSV: {e}")
# else:
#     print(f"CSV not found at: {CSV_PATH}")

# Simple free dictionary API
API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/{}"


def lookup_word(word: str):
    """Look up a word and return meaning, phonetic and audio URL (if any)."""
    word = word.strip().lower()
    if not word:
        return None

    resp = requests.get(API_URL.format(word))
    if resp.status_code != 200:
        return None

    try:
        data = resp.json()[0]
    except (ValueError, IndexError):
        return None

    # Definition
    meaning = None
    try:
        meaning = data["meanings"][0]["definitions"][0]["definition"]
    except (KeyError, IndexError):
        pass

    # Phonetic text
    phonetic = data.get("phonetic")
    if not phonetic:
        for p in data.get("phonetics", []):
            if p.get("text"):
                phonetic = p["text"]
                break

    # Audio URL
    audio = None
    for p in data.get("phonetics", []):
        if p.get("audio"):
            audio = p["audio"]
            break

    return {
        "word": word,
        "meaning": meaning,
        "phonetic": phonetic,
        "audio": audio,
    }


# ---------- Session state init ----------
if "word_list" not in st.session_state:
    st.session_state.word_list = []  # words for quiz
if "current_word" not in st.session_state:
    st.session_state.current_word = None
if "score" not in st.session_state:
    st.session_state.score = 0
if "total" not in st.session_state:
    st.session_state.total = 0

if "wrong_words" not in st.session_state:
    st.session_state.wrong_words = []  # track incorrect spellings
if "quiz_spelling" not in st.session_state:
    st.session_state.quiz_spelling = ""  # for clearing text input on new word


BASE_DIR = Path(__file__).resolve().parent  # folder where this .py file lives
CSV_PATH = BASE_DIR / "2025-2026_speling_bee_list.csv"

if CSV_PATH.exists():
    try:
        df = pd.read_csv(CSV_PATH)

        if "word" in df.columns:
            pre_words = (
                df["word"]
                .dropna()
                .astype(str)
                .str.strip()
                .str.lower()
                .tolist()
            )

            for w in pre_words:
                if w not in st.session_state.word_list:
                    st.session_state.word_list.append(w)

            print(f"Pre-loaded {len(pre_words)} words from CSV at {CSV_PATH}.")
        else:
            print(f"CSV found at {CSV_PATH}, but no 'word' column.")
    except Exception as e:
        print(f"Error loading CSV from {CSV_PATH}: {e}")
else:
    print(f"CSV not found at: {CSV_PATH}")

st.title("📚 Spelling Bee Helper")

tab_lookup, tab_quiz = st.tabs(["🔍 Look up word", "📝 Spelling quiz"])

# ---------- TAB 1: Look up word ----------
with tab_lookup:
    word_input = st.text_input("Enter a word:")

    if st.button("Look up"):
        info = lookup_word(word_input)
        if not info:
            st.error("Word not found or API error.")
        else:
            st.write(f"**Word:** {info['word']}")
            if info["meaning"]:
                st.write(f"**Definition:** {info['meaning']}")
            if info["phonetic"]:
                st.write(f"**Pronunciation:** {info['phonetic']}")
            if info["audio"]:
                st.audio(info["audio"])

            if st.button("➕ Add to quiz list"):
                if info["word"] not in st.session_state.word_list:
                    st.session_state.word_list.append(info["word"])
                    st.success(f"Added **{info['word']}** to quiz list.")
                else:
                    st.info("Word is already in the quiz list.")

    st.subheader("Current quiz word list")
    if st.session_state.word_list:
        st.write(", ".join(st.session_state.word_list))
    else:
        st.write("_No words added yet._")

    st.subheader("📤 Import word list from CSV")

    uploaded_file = st.file_uploader("Upload CSV file with a 'word' column", type=["csv"])

    if uploaded_file is not None:
        import pandas as pd
        df = pd.read_csv(uploaded_file)

        if "word" not in df.columns:
            st.error("CSV must contain a column named 'word'.")
        else:
            new_words = df["word"].dropna().str.strip().str.lower().tolist()
            added = 0
            
            for w in new_words:
                if w not in st.session_state.word_list:
                    st.session_state.word_list.append(w)
                    added += 1

            st.success(f"Imported {added} new words!")
            st.write(f"Total words in quiz list: {len(st.session_state.word_list)}")

# ---------- TAB 2: Quiz ----------
with tab_quiz:
    if not st.session_state.word_list:
        st.info("Add some words in the **Look up word** tab first.")
    else:
        st.write(f"Total words available for quiz: **{len(st.session_state.word_list)}**")
        st.write(f"Score this session: **{st.session_state.score} / {st.session_state.total}**")

        # Button to pick a new random word
        if st.button("🎲 New word"):
            st.session_state.current_word = random.choice(st.session_state.word_list)
            st.session_state.quiz_feedback = ""
            st.session_state.last_definition = None
            # 👇 CLEAR previous spelling input
            st.session_state["quiz_spelling"] = ""

        if st.session_state.current_word:
            quiz_word = st.session_state.current_word
            st.subheader("Spell this word")

            # Get info for audio + definition
            info = lookup_word(quiz_word)
            if info and info.get("audio"):
                st.audio(info["audio"])
            else:
                st.caption("No audio available for this word; spell from memory 🙂.")

            user_spelling = st.text_input(
                "Your spelling:",
                key="quiz_spelling",
                placeholder="Type the spelling here"
            )

            if st.button("Check spelling"):
                st.session_state.total += 1
                normalized = user_spelling.strip().lower()

                # Save definition (if any) to show as feedback
                st.session_state.last_definition = info.get("meaning") if info else None

                if normalized == quiz_word:
                    st.session_state.score += 1
                    st.success("✅ Correct!")
                else:
                    st.error(f"❌ Incorrect. Correct spelling: **{quiz_word}**")
                    # Track words that were missed
                    if quiz_word not in st.session_state.wrong_words:
                        st.session_state.wrong_words.append(quiz_word)

            # Show definition after answer (if available)
            if st.session_state.get("last_definition"):
                st.info(f"**Definition:** {st.session_state.last_definition}")

        else:
            st.write("Click **New word** to start the quiz.")

        st.markdown("---")
        with st.expander("Words you missed in this session"):
            if st.session_state.wrong_words:
                st.write(", ".join(st.session_state.wrong_words))
            else:
                st.write("✅ No missed words yet—great job!")