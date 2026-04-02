import json
import os
import re
from typing import Dict, List, Set, Tuple
from urllib.parse import quote_plus

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from groq import Groq
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

load_dotenv()
app = FastAPI(title="Vibe to Playlist")

SONG_LIBRARY_BY_LANGUAGE: Dict[str, List[Dict[str, object]]] = {
    "English": [
        {"song": "On Top of the World", "artist": "Imagine Dragons", "tags": {"productive", "motivated", "happy", "uplifting"}, "descriptor": "bright, forward-moving"},
        {"song": "Dog Days Are Over", "artist": "Florence + The Machine", "tags": {"uplifting", "relief", "energized", "happy"}, "descriptor": "explosive, freeing"},
        {"song": "Good Days", "artist": "SZA", "tags": {"calm", "reflective", "hopeful", "gentle"}, "descriptor": "smooth, reassuring"},
        {"song": "Vienna", "artist": "Billy Joel", "tags": {"reflective", "stressed", "calm", "comfort"}, "descriptor": "thoughtful, grounding"},
        {"song": "Shake It Out", "artist": "Florence + The Machine", "tags": {"release", "stressed", "uplifting", "relief"}, "descriptor": "cathartic, big-hearted"},
    ],
    "Bengali": [
        {"song": "Tomake Chai", "artist": "Hemanta Mukherjee", "tags": {"romantic", "nostalgic", "calm"}, "descriptor": "warm, heartfelt"},
        {"song": "Amake Amar Moto Thakte Dao", "artist": "Akhiyan", "tags": {"calm", "reflective", "gentle"}, "descriptor": "soothing, liberating"},
        {"song": "Mon Mano Na", "artist": "Mithun", "tags": {"upbeat", "happy", "energized"}, "descriptor": "bouncy, cheerful"},
        {"song": "Ei Raat Tomar Amar", "artist": "Firoza Begum", "tags": {"romantic", "calm", "reflective"}, "descriptor": "dreamy, poetic"},
        {"song": "Meghe Dhaka Tara", "artist": "Manna Dey", "tags": {"reflective", "comfort", "classic"}, "descriptor": "timeless, steady"},
    ],
    "Hindi": [
        {"song": "Tum Hi Ho", "artist": "Arijit Singh", "tags": {"romantic", "melancholy", "reflective"}, "descriptor": "deep, emotional"},
        {"song": "Kal Ho Naa Ho", "artist": "Sonu Nigam", "tags": {"hopeful", "comfort", "uplifting"}, "descriptor": "inspiring, gentle"},
        {"song": "Zindagi", "artist": "Bachna Ae Haseeno", "tags": {"happy", "energized", "upbeat"}, "descriptor": "playful, lively"},
        {"song": "Tere Bina", "artist": "A.R. Rahman", "tags": {"calm", "yearning", "reflective"}, "descriptor": "haunting, soft"},
        {"song": "Agar Tum Saath Ho", "artist": "Alka Yagnik & Arijit Singh", "tags": {"sad", "comfort", "heartfelt"}, "descriptor": "intimate, soothing"},
    ],
}

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
}


def spotify_search_url(song: str, artist: str) -> str:
    query = quote_plus(f"{song} {artist}".strip())
    return f"https://open.spotify.com/search/{query}"


def youtube_search_url(song: str, artist: str) -> str:
    query = quote_plus(f"{song} {artist}".strip())
    return f"https://www.youtube.com/results?search_query={query}"


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

    return f"Your vibe reads as {tone_text}, so this playlist leans {direction} to match your day."


def score_song(song: Dict[str, object], tags: Set[str]) -> int:
    song_tags = song.get("tags", set())
    overlap = len(song_tags.intersection(tags))
    return overlap * 3 + (1 if "calm" in song_tags and "stressed" in tags else 0)


def local_reason(song: Dict[str, object], tags: Set[str]) -> str:
    matches = list(song.get("tags", set()).intersection(tags))
    vibe = ", ".join(matches[:2]) if matches else "your current mood"
    return f"Its {song.get('descriptor', 'balanced')} energy matches {vibe}."


def generate_local_playlist(day_text: str, language: str) -> Dict[str, object]:
    tags, scores = infer_tags(day_text)
    source_library = SONG_LIBRARY_BY_LANGUAGE.get(language, SONG_LIBRARY_BY_LANGUAGE["English"])
    ranked = sorted(source_library, key=lambda song: score_song(song, tags), reverse=True)
    selected = ranked[:5]

    playlist = []
    for s in selected:
        spotify_url = spotify_search_url(s["song"], s["artist"])
        youtube_url = youtube_search_url(s["song"], s["artist"])
        if language == "English":
            link, link_label = spotify_url, "Spotify"
            fallback = youtube_url
        else:
            link, link_label = youtube_url, "YouTube"
            fallback = spotify_url

        playlist.append(
            {
                "song": s["song"],
                "artist": s["artist"],
                "reason": local_reason(s, tags),
                "primary_link": link,
                "primary_label": link_label,
                "fallback_link": fallback,
            }
        )

    return {
        "summary": local_summary(tags, scores),
        "playlist": playlist,
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

    return data


def generate_groq_playlist(day_text: str, language: str, api_key: str, model: str) -> Dict[str, object]:
    client = Groq(api_key=api_key)
    prompt = f"""
You are a thoughtful music curator.
Composing 5 songs in {language} with mood-to-vibe alignment.
Return only valid JSON in this format:
{{
  "summary": "one short paragraph summary",
  "playlist": [
    {{"song": "Song Title", "artist": "Artist Name", "reason": "Why it fits"}}
  ]
}}

Rules:
- Exactly 5 songs
- Real, well-known songs (preferably {language})
- Vary the artists when possible
- Make each reason 1-2 sentences and specific to the user's mood

User description: {day_text}
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You create emotionally aware song playlists and respond with JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.9,
    )

    content = response.choices[0].message.content or ""
    parsed = extract_json(content)

    playlist: List[Dict[str, object]] = []
    for item in parsed.get("playlist", [])[:5]:
        song = str(item.get("song", "Unknown song")).strip()
        artist = str(item.get("artist", "Unknown artist")).strip()
        reason = str(item.get("reason", "")).strip()
        spotify_url = spotify_search_url(song, artist)
        youtube_url = youtube_search_url(song, artist)
        primary = spotify_url if language == "English" else youtube_url
        fallback = youtube_url if language == "English" else spotify_url
        playlist.append(
            {
                "song": song,
                "artist": artist,
                "reason": reason or "Selected for your mood.",
                "primary_link": primary,
                "primary_label": "Spotify" if language == "English" else "YouTube",
                "fallback_link": fallback,
            }
        )

    return {
        "summary": parsed.get("summary", "Playlist matched to your vibe."),
        "playlist": playlist,
    }


def generate_playlist(day_text: str, language: str, api_key: str, model: str) -> Dict[str, object]:
    if api_key:
        try:
            return generate_groq_playlist(day_text, language, api_key, model)
        except Exception:
            pass
    return generate_local_playlist(day_text, language)


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return HTMLResponse(
        f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Vibe to Playlist</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f8fafc; color: #0f172a; }
    .container { max-width: 900px; margin: 1.5rem auto; padding: 1rem; }
    .card { background: white; border-radius: 12px; box-shadow: 0 10px 30px rgba(20, 25, 45, 0.08); padding: 1.25rem; }
    h1 { margin-top: 0; }
    label { display: block; margin-bottom: 0.35rem; font-weight: 600; }
    select, textarea, input { width: 100%; padding: 0.75rem; border-radius: 8px; border: 1px solid #cbd5e1; margin-bottom: 1rem; }
    button { background: #2563eb; color: white; border: 0; padding: 0.75rem 1.1rem; border-radius: 8px; font-weight: 700; cursor: pointer; }
    button:hover { background: #1d4ed8; }
    .song-item { margin-bottom: 1rem; }
    .song-title { margin: 0 0 0.2rem; font-weight: 700; }
    .note { color: #475569; font-size: 0.95rem; }
    .flex-row { display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; }
    a { color: #2563eb; text-decoration: none; }
    a:hover { text-decoration: underline; }
    @media (max-width: 640px) { .container { margin: 0.7rem; padding: 0.7rem; } }
  </style>
</head>
<body>
  <div class="container card">
    <h1>Vibe to Playlist</h1>
    <p>Access from anywhere (phone/web). Select a language, describe your mood, and get matching top 5 songs.</p>
    <form action="/generate" method="post">
      <label for="language">Select your preferred language</label>
      <select id="language" name="language" required>
        <option value="English">English</option>
        <option value="Bengali">Bengali</option>
        <option value="Hindi">Hindi</option>
      </select>

      <label for="day_text">How are you feeling for Mood/vibe input</label>
      <textarea id="day_text" name="day_text" rows="5" placeholder="E.g., It was a stressful but productive day..." required></textarea>

      <label for="api_key">Groq API key (optional, leave empty for local fallback)</label>
      <input type="password" id="api_key" name="api_key" placeholder="Optional API key" />

      <label for="model">Groq model name</label>
      <input type="text" id="model" name="model" value="llama-3.3-70b-versatile" />

      <button type="submit">Generate playlist</button>
    </form>
  </div>
</body>
</html>
        """
    )


@app.post("/generate", response_class=HTMLResponse)
def generate(request: Request, day_text: str = Form(...), language: str = Form("English"), api_key: str = Form(""), model: str = Form("llama-3.3-70b-versatile")):
    if not day_text.strip():
        return HTMLResponse("<h2>Please provide a mood/vibe text.</h2>")

    result = generate_playlist(day_text, language, api_key.strip(), model.strip())
    source_text = "Groq" if api_key else "Local fallback"

    playlist_html = ""
    for idx, item in enumerate(result["playlist"], start=1):
        playlist_html += f"""
        <div class=\"song-item\">
          <p class=\"song-title\">{idx}. {item['song']} — {item['artist']}</p>
          <p>{item['reason']}</p>
          <div class=\"flex-row\"><a href=\"{item['primary_link']}\" target=\"_blank\">Open on {item['primary_label']}</a><span class=\"note\">(fallback: <a href=\"{item['fallback_link']}\" target=\"_blank\">{('YouTube' if item['primary_label'] == 'Spotify' else 'Spotify')}</a>)</span></div>
        </div>
        """

    return HTMLResponse(
        f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Playlist Result</title>
  <style>body {{font-family: Arial, sans-serif; margin: 1rem; background: #f8fafc; color: #0f172a;}} .card {{background: white; border-radius: 10px; padding: 1rem; max-width: 950px; margin: auto;}} a {{color: #2563eb;}}</style>
</head>
<body>
  <div class="card">
    <h1>Your playlist</h1>
    <p><strong>Language:</strong> {language}</p>
    <p><strong>Source:</strong> {source_text}</p>
    <h2>Why this playlist fits</h2>
    <p>{result['summary']}</p>
    <h2>Top 5 songs</h2>
    {playlist_html}
    <p><a href="/">&#8592; Generate another playlist</a></p>
  </div>
</body>
</html>
        """
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
""'
open('main.py','w',encoding='utf-8').write(content)