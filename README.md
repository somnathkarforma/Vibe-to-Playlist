# Vibe to Playlist

A simple Streamlit web app that turns a short description of your day into a 5-song playlist.

## Features
- Streamlit frontend
- Optional Groq-powered playlist generation
- Local mood-based fallback if no API key is set
- Short explanation for why each song fits

## Setup
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Then add your Groq API key to `.env` if you want live AI recommendations.

## Run
```powershell
streamlit run app.py
```
