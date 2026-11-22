# MedScribe – speech to structured clinical notes

Consultation audio → Whisper transcript → Gemini note (Pydantic schema) → automatic claim checks → doctor review/edit → finalize.

## Run (Docker)
```
cp .env.example .env   # add GEMINI_API_KEY
docker compose up --build
```
Open http://localhost:3000 and sign in with ADMIN_EMAIL / ADMIN_PASSWORD (default admin@example.com / admin12345). Admins create doctor accounts under **Users**. First transcription downloads the Whisper model.

## Run (local dev)
```
cd backend && python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # needs ffmpeg: brew install ffmpeg
export DATABASE_URL=postgresql+psycopg2://medscribe:medscribe@localhost:5432/medscribe GEMINI_API_KEY=...
uvicorn app.main:app --reload
cd ../frontend && npm install && npm run dev
```
(Start Postgres with `docker compose up db`.) API docs: http://localhost:8000/docs

## How it works
- **Preprocess**: ffmpeg → 16 kHz mono, high-pass + loudness normalisation.
- **Transcribe**: faster-whisper with VAD.
- **Note**: Gemini returns JSON constrained to `ClinicalNote` (each statement carries a verbatim `source_quote`); re-validated with Pydantic, one retry.
- **Checks** (`validation.py`): flags statements whose quote isn't in the transcript, have no quote, or contain numbers (doses etc.) the transcript never mentions.
- **Review**: doctor edits; each save re-runs checks. Finalizing with open flags needs explicit confirmation; finalized notes are locked.
- **Roles**: doctors see only their consultations; admins see all and manage users.
- **Live updates**: WebSocket `/ws/consultations/{id}` streams pipeline stages. Processing runs in FastAPI background tasks (single process).

Prototype: not a certified medical device; a clinician must review every note.
