# Nepali G2P Review UI

Local listening UI for comparing:

- existing `nepali_frontend` G2P
- experimental `real_nepali` G2P

Both sides use eSpeak NG's vocoder through generated bracket-phone WAVs. This
keeps the synthesizer fixed so the review focuses on the frontend, not neural
TTS training.

## Generate Assets

From the repo root:

```bash
python3 tools/generate_review_ui_assets.py
```

## Run

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

The UI opens on the `changed` filter so the first pass focuses on samples where
the two G2P profiles actually differ. Reviewer choices are stored in browser
local storage and can be exported as TSV from the UI.
