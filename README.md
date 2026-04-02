# Vibe to Playlist

A static web app that turns a short description of your day into a 5-song playlist with mood-based reasons, language selection (English, Bengali, Hindi), and Spotify/YouTube links.

## Features
- Pure HTML/JS static site (no server needed)
- Language picker: English, Bengali, Hindi
- Mood/vibe text input with headings
- Top 5 tracks in selected language
- Spotify link for English (primary), YouTube fallback
- YouTube link for Bengali/Hindi (primary), Spotify fallback
- Client-side sentiment analysis using Sentiment.js
- Local mood-based playlist generation

## Access the App
The app is deployed on GitHub Pages: [https://somnathkarforma.github.io/Vibe-to-Playlist/](https://somnathkarforma.github.io/Vibe-to-Playlist/)

You can access it from any device with internet.

## Local Development (optional)
To run locally:
1. Open `index.html` in your browser.
2. No server required, it's static.

## Deployment to GitHub Pages
1. Push this repo to GitHub.
2. Go to repo Settings > Pages.
3. Set source to "Deploy from a branch", branch "main", folder "/ (root)".
4. Save, and the site will be live at `https://<username>.github.io/<repo-name>/`.

## Notes
- Uses client-side JS for all logic.
- No API keys needed; all processing is local.
- If you need AI-powered playlists, consider a server-based deployment.

## Example Usage
1. Choose `Bengali` or `Hindi` (or `English`).
2. Enter mood text under "How are you feeling for Mood/vibe input".
3. Generate playlist and click the provided song links.

