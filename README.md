# Vibe to Playlist

A Streamlit web app that turns a short description of your day into a 5-song playlist with mood-based explanations and Spotify links.

## Features
- Streamlit frontend
- Optional Groq-powered playlist generation
- Local mood-based fallback if no API key is set
- Spotify search link for every suggested song
- Mobile-friendly once deployed to a public host

## Local setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Then add your Groq API key to `.env` if you want live AI recommendations.

## Run locally
```powershell
.\.venv\Scripts\python -m streamlit run app.py
```

## Deploy so it works from your phone

### Option 1: Streamlit Community Cloud
1. Push this folder to a GitHub repo.
2. Go to [https://share.streamlit.io](https://share.streamlit.io).
3. Create a new app and select your repo.
4. In **Secrets**, add:
   ```toml
   GROQ_API_KEY = "your_key_here"
   GROQ_MODEL = "llama-3.3-70b-versatile"
   ```
5. Deploy and open the public URL on your phone.

### Option 2: Render
This repo now includes `render.yaml`, so you can deploy it directly on Render:
1. Push the repo to GitHub.
2. Create a new **Blueprint** service on [https://render.com](https://render.com).
3. Add `GROQ_API_KEY` in Render environment variables.
4. Deploy and use the generated public URL from any device.
