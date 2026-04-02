# Vibe to Playlist

A web app (FastAPI) that turns a short description of your day into a 5-song playlist with mood-based reasons, language selection (English, Bengali, Hindi), and Spotify/YouTube links.

## Features
- FastAPI + simple responsive HTML UI
- Language picker: English, Bengali, Hindi
- Mood/vibe text input with client heading prompts
- Top 5 tracks in selected language
- Spotify link for English (primary), YouTube fallback
- YouTube link for Bengali/Hindi (primary), Spotify fallback
- Optional Groq API support for AI playlist generation
- Local mood-based fallback if no API key or Groq errors

## Local setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Then add your Groq API key to `.env` if you want live AI recommendations (`GROQ_API_KEY`, `GROQ_MODEL`).

## Run locally
```powershell
.\.venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Access from anywhere (phone/web)
- Run with host `0.0.0.0` so the app is reachable on your local network.
- Open `http://<your-machine-ip>:8000` on your phone/browser.
- For public hosting, deploy to Render / Heroku / Railway / any FastAPI-supported platform and set `PORT` and `GROQ_API_KEY` as environment variables.

## Notes
- `https://<host>/` shows the language selector and mood text area.
- `https://<host>/generate` returns a playlist page with 5 tracks and provider-specific links.
- Any selected language that may not be available on Spotify will fall back to YouTube.

## Example
1. Choose `Bengali` or `Hindi` (or `English`).
2. Enter mood text under "How are you feeling for Mood/vibe input".
3. Generate playlist and click the provided song links.

