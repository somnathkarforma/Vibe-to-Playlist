import json
import os
import re
from typing import Dict, List, Set, Tuple

import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

load_dotenv()

st.set_page_config(page_title="Vibe to Playlist", page_icon="🎵", layout="centered")

SONG_LIBRARY: List[Dict[str, object]] = [
    {"song": "On Top of the World", "artist": "Imagine Dragons", "tags": {"productive", "motivated", "happy", "uplifting"}, "descriptor": "bright, forward-moving"},
    {"song": "Dog Days Are Over", "artist": "Florence + The Machine", "tags": {"uplifting", "relief", "energized", "happy"}, "descriptor": "explosive, freeing"},
    {"song": "Good Days", "artist": "SZA", "tags": {"calm", "reflective", "hopeful", "gentle"}, "descriptor": "smooth, reassuring"},
    {"song": "Vienna", "artist": "Billy Joel", "tags": {"reflective", "stressed", "calm", "comfort"}, "descriptor": "thoughtful, grounding"},
    {"song": "Shake It Out", "artist": "Florence + The Machine", "tags": {"release", "stressed", "uplifting", "relief"}, "descriptor": "cathartic, big-hearted"},
    {"song": "Sunflower", "artist": "Post Malone & Swae Lee", "tags": {"light", "happy", "easy", "calm"}, "descriptor": "easygoing, warm"},
    {"song": "Weightless", "artist": "Marconi Union", "tags": {"calm", "stressed", "gentle", "relief"}, "descriptor": "soft, decompressing"},
    {"song": "Midnight City", "artist": "M83", "tags": {"energized", "motivated", "focus", "uplifting"}, "descriptor": "shimmering, high-energy"},
    {"song": "Holocene", "artist": "Bon Iver", "tags": {"reflective", "gentle", "comfort", "calm"}, "descriptor": "quiet, expansive"},
    {"song": "Walking on a Dream", "artist": "Empire of the Sun", "tags": {"happy", "uplifting", "light", "energized"}, "descriptor": "dreamy, upbeat"},
    {"song": "Lose Yourself", "artist": "Eminem", "tags": {"motivated", "productive", "focus", "energized"}, "descriptor": "intense, locked-in"},
    {"song": "Breathe Me", "artist": "Sia", "tags": {"reflective", "sad", "comfort", "gentle"}, "descriptor": "vulnerable, slow-building"},
    {"song": "Saturday Sun", "artist": "Vance Joy", "tags": {"hopeful", "light", "happy", "easy"}, "descriptor": "sunny, breezy"},
    {"song": "Nights", "artist": "Frank Ocean", "tags": {"reflective", "moody", "late-night", "calm"}, "descriptor": "moody, emotionally rich"},
    {"song": "Stronger", "artist": "Kanye West", "tags": {"motivated", "energized", "productive", "uplifting"}, "descriptor": "confident, punchy"},
    {"song": "Fix You", "artist": "Coldplay", "tags": {"comfort", "sad", "hopeful", "gentle"}, "descriptor": "healing, gradual"},
    {"song": "Bloom", "artist": "The Paper Kites", "tags": {"calm", "gentle", "reflective", "easy"}, "descriptor": "soft, intimate"},
    {"song": "Levitating", "artist": "Dua Lipa", "tags": {"happy", "energized", "uplifting", "light"}, "descriptor": "sparkly, dance-ready"},
    {"song": "River", "artist": "Leon Bridges", "tags": {"calm", "comfort", "reflective", "gentle"}, "descriptor": "soulful, settling"},
    {"song": "Feel It Still", "artist": "Portugal. The Man", "tags": {"happy", "light", "uplifting", "energized"}, "descriptor": "snappy, playful"},
]

KEYWORD_TAGS: Dict[str, Set[str]] = {
    "productive": {"productive", "motivated", "focus"},
    "focused": {"productive", "focus", "motivated"},
    "motivated": {"motivated", "productive", "uplifting"},
    "stressed": {"stressed", "calm", "relief"},
    "anxious": {"stressed", "calm", "gentle"},
    "overwhelmed": {"stressed", "relief", "comfort"},
    "tired": {"gentle", "comfort", "calm"},
    "exhausted": {"gentle", "comfort", "calm"},
    "happy": {"happy", "uplifting", "light"},
    "excited": {"happy", "energized", "uplifting"},
    "sad": {"sad", "reflective", "comfort"},
    "down": {"sad", "gentle", "comfort"},
    "calm": {"calm", "gentle", "easy"},
    "relaxed": {"calm", "easy", "light"},
    "lonely": {"reflective", "comfort", "gentle"},
    "burned out": {"tired", "comfort", "calm"},
    "burnt out": {"tired", "comfort", "calm"},
}


def extract_json(text: str) -> Dict[str, object]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    payload = match.group(0) if match else cleaned
    data = json.loads(payload)

    if not isinstance(data, dict) or "playlist" not in data:
        raise ValueError("Model response did not include a playlist.")

    playlist = data.get("playlist", [])
    if not isinstance(playlist, list) or len(playlist) < 5:
        raise ValueError("Model response returned fewer than 5 songs.")

    return data


def generate_groq_playlist(day_text: str, api_key: str, model: str) -> Dict[str, object]:
    client = Groq(api_key=api_key)
    prompt = f'''
You are a thoughtful music curator.
Based on the user's day, suggest exactly 5 real songs.
Return only valid JSON in this format:
{{
  "summary": "one short paragraph summary",
  "playlist": [
    {{"song": "Song Title", "artist": "Artist Name", "reason": "Why it fits"}}
  ]
}}

Rules:
- Exactly 5 songs
- Real, well-known songs
- Vary the artists when possible
- Make each reason 1-2 sentences and specific to the user's mood

User description: {day_text}
'''

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You create emotionally aware playlists and respond with JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.9,
    )

    content = response.choices[0].message.content or ""
    return extract_json(content)


def infer_tags(day_text: str) -> Tuple[Set[str], Dict[str, float]]:
    analyzer = SentimentIntensityAnalyzer()
    scores = analyzer.polarity_scores(day_text)
    text = day_text.lower()
    tags: Set[str] = set()

    for keyword, mapped_tags in KEYWORD_TAGS.items():
        if keyword in text:
            tags.update(mapped_tags)

    if scores["compound"] >= 0.45:
        tags.update({"happy", "uplifting", "energized", "hopeful"})
    elif scores["compound"] <= -0.45:
        tags.update({"reflective", "comfort", "gentle"})
    else:
        tags.update({"calm", "balanced"})

    if not tags:
        tags.update({"reflective", "calm", "balanced"})

    return tags, scores


def local_summary(tags: Set[str], scores: Dict[str, float]) -> str:
    tone_order = ["productive", "stressed", "happy", "reflective", "calm", "tired", "motivated"]
    tones = [tone for tone in tone_order if tone in tags][:3]
    tone_text = ", ".join(tones) if tones else "mixed"

    if scores["compound"] >= 0.45:
        direction = "uplifting and high-energy"
    elif scores["compound"] <= -0.45:
        direction = "gentle and grounding"
    else:
        direction = "balanced and steady"

    return f"Your vibe reads as {tone_text}, so this playlist leans {direction} to match your day without overdoing it."


def score_song(song: Dict[str, object], tags: Set[str]) -> int:
    song_tags = song["tags"]
    overlap = len(song_tags.intersection(tags))
    return overlap * 3 + (1 if "calm" in song_tags and "stressed" in tags else 0)


def local_reason(song: Dict[str, object], tags: Set[str]) -> str:
    matches = list(song["tags"].intersection(tags))
    vibe = ", ".join(matches[:2]) if matches else "your current mood"
    return f"Its {song['descriptor']} energy lines up with {vibe} and helps the set feel intentional rather than random."


def generate_local_playlist(day_text: str) -> Dict[str, object]:
    tags, scores = infer_tags(day_text)
    ranked = sorted(SONG_LIBRARY, key=lambda song: score_song(song, tags), reverse=True)
    selected = ranked[:5]

    playlist = [
        {
            "song": song["song"],
            "artist": song["artist"],
            "reason": local_reason(song, tags),
        }
        for song in selected
    ]

    return {
        "summary": local_summary(tags, scores),
        "playlist": playlist,
    }


def generate_playlist(day_text: str, api_key: str, model: str) -> Tuple[Dict[str, object], str]:
    if api_key:
        try:
            return generate_groq_playlist(day_text, api_key, model), "Groq"
        except Exception as exc:
            fallback = generate_local_playlist(day_text)
            fallback["summary"] += f"\n\nGroq mode was unavailable, so a local mood-based recommender was used instead. ({exc})"
            return fallback, "Local fallback"

    return generate_local_playlist(day_text), "Local fallback"


st.title("🎵 Vibe to Playlist")
st.write("Describe how your day went, and this app will turn that vibe into a 5-song playlist.")

with st.sidebar:
    st.subheader("Settings")
    api_key = st.text_input(
        "Groq API key (optional)",
        value=os.getenv("GROQ_API_KEY", ""),
        type="password",
        help="Add a Groq key for full AI-generated playlists. Without one, the app uses a local mood-based fallback.",
    )
    model = st.text_input("Model", value=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"))

example = "I'm feeling productive but stressed, like I got a lot done but need to unwind."
day_text = st.text_area("How did your day go?", value=example, height=160)

if st.button("Generate playlist", type="primary"):
    if not day_text.strip():
        st.warning("Please type a short description of your day first.")
    else:
        with st.spinner("Building your playlist..."):
            result, source = generate_playlist(day_text, api_key.strip(), model.strip())

        st.success(f"Playlist ready — source: {source}")
        st.markdown("### Why this playlist fits")
        st.write(result["summary"])

        st.markdown("### Your 5-song playlist")
        for index, item in enumerate(result["playlist"][:5], start=1):
            st.markdown(f"**{index}. {item['song']} — {item['artist']}**")
            st.write(item["reason"])
            st.divider()

st.caption("Tip: set `GROQ_API_KEY` in a `.env` file if you want live AI-generated recommendations.")
