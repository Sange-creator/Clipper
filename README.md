# AI Video Clipper Pro

Production-grade AI video clipping and short-form discovery platform that converts long-form videos into high-retention 9:16 vertical clips optimized for TikTok, Instagram Reels, and YouTube Shorts.

---

## Architectural Overview

AI Video Clipper Pro is structured as a decoupled full-stack application designed for deterministic media processing, resilient AI reasoning, and high-performance video rendering.

### Core Technology Stack

- **Frontend**: Next.js 15 (App Router), TypeScript, Tailwind CSS, Lucide Icons, HTML5 Media APIs
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy Async, SQLite / PostgreSQL, Pydantic V2
- **Speech Recognition**: Deepgram Nova-3 API (Word-level timestamps, speaker diarization) with local Faster-Whisper fallback
- **Reasoning Engine**: Groq LPU (Llama 3), Google Gemini 2.0 Flash (Multimodal reasoning), and deterministic heuristic fallback
- **Media Processing**: FFmpeg 7+ / 9.0 Pro, OpenCV, PySceneDetect

---

## Deterministic 21-Stage Video Pipeline

Every uploaded video is processed through a sequential, state-tracked pipeline with real-time WebSocket and polling observability:

1. **Validate File**: MIME type verification, container integrity, and duration inspection.
2. **Inspect Media Metadata**: Audio sample rates, video dimensions, frame rates, and codec compliance via FFprobe.
3. **Create Job**: Initialization of persistent SQLite job record with user-configured presets.
4. **Extract Audio**: High-efficiency extraction of 16kHz mono PCM WAV audio for acoustic modeling.
5. **Transcribe Audio**: Deepgram Cloud STT / Faster-Whisper transcription preserving word-level timestamps.
6. **Detect Scenes**: Audio silence analysis, dead-air boundary detection, and scene transitions.
7. **Generate Timestamped Transcript**: Alignment and serialization of timed speech segments.
8. **Detect Candidate Moments**: Autonomous discovery of candidate clips using structured JSON schema validation.
9. **Expand Candidate Context**: Natural boundary expansion to complete preceding thoughts and resolve payoffs.
10. **Analyze Candidate Quality**: Evaluation of linguistic tension, curiosity gaps, and narrative hooks.
11. **Score Candidates**: Computation of 12-factor composite metric (hook, retention, story, payoff, shareability).
12. **Remove Duplicates / Overlaps**: Temporal Intersection-over-Union (IoU) Non-Maximum Suppression (NMS).
13. **Rank Globally**: Normalization and global priority sorting across candidate pools.
14. **Apply User Duration Constraints**: Preservation of narrative arcs within target durations (15-30s, 30-45s, 45-60s, 60-90s).
15. **Generate Final Clip Boundaries**: Generation of exact trimming intervals with dead-air excision.
16. **Render Clips Using FFmpeg**: 9:16 vertical crop, 16:9 blurred background synthesis, or native 16:9 export.
17. **Generate Captions**: Generation of timed Advanced SubStation Alpha (.ass) and SubRip (.srt) subtitle tracks.
18. **Generate Thumbnails**: Extraction of high-engagement hook keyframes.
19. **Generate Clip Metadata**: Production of viral titles, captions, and platform hashtags.
20. **Store Results**: Persistence of clip assets, video streams, and scoring metrics to local database.
21. **Mark Job Complete**: Finalization of job state and emission of completion signals.

---

## AI Provider Resilience and Fallback Matrix

To guarantee uninterrupted processing regardless of rate limits or service outages, the system utilizes a chained multi-provider architecture:

```
+-------------------------------------------------------------------+
|                        Client Job Request                         |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                  Stage 5: Speech-to-Text (STT)                    |
|    Deepgram Nova-3 Cloud STT ----(Fallback)----> Faster-Whisper   |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|               Stage 8: Candidate Moment Discovery                 |
|   Groq LPU (Llama 3) ----(401/429 Fallback)----> Gemini 2.0 Flash |
|                                |                                  |
|                      (All Providers Failed)                       |
|                                |                                  |
|                                v                                  |
|                 Deterministic Heuristic Fallback                  |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                     Stage 16: Media Rendering                     |
|           FFmpeg Vertical Framing + Subtitle Burn-In              |
+-------------------------------------------------------------------+
```

- **Deepgram Nova-3**: Cloud speech recognition supporting word timestamps and speaker identification.
- **Groq LPU**: Sub-second candidate extraction running Llama 3 models.
- **Google Gemini 2.0 Flash**: Multi-modal fallback capable of contextual reasoning and visual validation.
- **Heuristic Engine**: Deterministic fallback guaranteeing pipeline completion under total network isolation.

---

## Framing and Captioning Capabilities

### Video Reframing Modes
- **9:16 Smart Center / Face Crop**: Vertical framing focusing on detected subjects.
- **16:9 in 9:16 Blurred Background**: Preserves original 16:9 landscape aspect ratio centered within a 9:16 canvas, with user-configurable background gaussian blur radius (5px to 60px).
- **16:9 Landscape Native**: Preserves original source dimensions.

### Subtitle Rendering
- **Karaoke Word-Level Highlighting**: Word-by-word active syllable emphasis.
- **Configurable Vertical Placement**: Subtitle vertical position slider (15% to 88% screen height) with one-click presets (Top, Upper-Middle, Center, Lower-Third, Bottom).
- **Styling Presets**: Bold Yellow, Neon Cyan, Classic White, Minimal Boxed, and Subtitle-Free export.

---

## Project Structure

```
Clipper/
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |   |-- routes/
|   |   |   |   |-- admin.py
|   |   |   |   |-- clips.py
|   |   |   |   |-- export.py
|   |   |   |   |-- jobs.py
|   |   |   |   |-- media.py
|   |   |   |   |-- projects.py
|   |   |   |   |-- settings.py
|   |   |   |   `-- upload.py
|   |   |   |-- schemas.py
|   |   |   `-- router.py
|   |   |-- core/
|   |   |   |-- database.py
|   |   |   `-- models.py
|   |   |-- services/
|   |   |   |-- ai/
|   |   |   |   |-- base.py
|   |   |   |   |-- factory.py
|   |   |   |   |-- gemini.py
|   |   |   |   |-- groq.py
|   |   |   |   |-- mock.py
|   |   |   |   `-- prompt_templates.py
|   |   |   |-- audio/
|   |   |   |   |-- audio_service.py
|   |   |   |   |-- deepgram.py
|   |   |   |   `-- whisper.py
|   |   |   |-- media/
|   |   |   |   |-- captioner.py
|   |   |   |   |-- ffmpeg_service.py
|   |   |   |   |-- face_detector.py
|   |   |   |   |-- scene_detector.py
|   |   |   |   `-- silence_detector.py
|   |   |   `-- pipeline/
|   |   |       |-- candidate_discovery.py
|   |   |       |-- context_expansion.py
|   |   |       |-- deduplication.py
|   |   |       |-- duration_enforcer.py
|   |   |       |-- global_ranking.py
|   |   |       |-- pipeline.py
|   |   |       |-- regenerator.py
|   |   |       `-- scoring.py
|   |   |-- utils/
|   |   |   `-- storage.py
|   |   |-- config.py
|   |   `-- main.py
|   |-- tests/
|   `-- pyproject.toml
|-- frontend/
|   |-- public/
|   |   |-- icon.svg
|   |   |-- logo.svg
|   |   `-- brand-logo.jpg
|   |-- src/
|   |   |-- app/
|   |   |   |-- admin/page.tsx
|   |   |   |-- clips/[id]/page.tsx
|   |   |   |-- history/page.tsx
|   |   |   |-- jobs/[id]/page.tsx
|   |   |   |-- projects/page.tsx
|   |   |   |-- projects/[id]/page.tsx
|   |   |   |-- settings/page.tsx
|   |   |   |-- globals.css
|   |   |   |-- layout.tsx
|   |   |   `-- page.tsx
|   |   |-- components/
|   |   |   |-- history/
|   |   |   |-- layout/
|   |   |   |-- processing/
|   |   |   |-- review/
|   |   |   |-- ui/
|   |   |   `-- upload/
|   |   `-- lib/
|   |       |-- api.ts
|   |       `-- utils.ts
|   |-- package.json
|   |-- next.config.ts
|   `-- tailwind.config.ts
`-- README.md
```

---

## Installation and Setup

### Prerequisites
- Python 3.11 or newer
- Node.js 18 or newer
- FFmpeg 6.0+ (compiled with `libass` for subtitle burn-in)

### 1. Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Start the FastAPI backend service:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API documentation is available at `http://localhost:8000/docs`.

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The web application is accessible at `http://localhost:3000` (or `http://localhost:3001`).

---

## Environment Variables

| Variable | Type | Description | Default |
|:---|:---|:---|:---|
| `AI_PROVIDER` | string | Primary reasoning engine (`groq`, `gemini`, `mock`) | `groq` |
| `GROQ_API_KEY` | string | Groq Cloud API authentication key | Optional |
| `GROQ_MODEL` | string | Groq model identifier | `llama-3.3-70b-versatile` |
| `GEMINI_API_KEY` | string | Google Gemini AI authentication key | Optional |
| `GEMINI_MODEL` | string | Gemini model identifier | `gemini-2.0-flash` |
| `DEEPGRAM_API_KEY` | string | Deepgram Cloud STT API key | Optional |
| `DEEPGRAM_MODEL` | string | Deepgram acoustic model | `nova-3` |
| `TRANSCRIBER_PROVIDER` | string | Speech recognition backend (`auto`, `deepgram`, `whisper`) | `auto` |
| `WHISPER_MODEL_SIZE` | string | Local Faster-Whisper model size | `base` |
| `DATABASE_URL` | string | Database connection string | `sqlite+aiosqlite:///./data/clipper.db` |
| `DATA_DIR` | string | Storage directory for video artifacts | `./data` |

---

## API Reference

### Video & Ingestion
- `POST /api/upload`: Upload video file and extract media metadata.
- `GET /api/videos`: List all registered source videos.
- `GET /api/videos/{id}`: Fetch video metadata and associated jobs.

### Jobs & Pipeline Execution
- `POST /api/jobs`: Dispatch a new asynchronous video clipping job.
- `GET /api/jobs`: Query active and past pipeline executions.
- `GET /api/jobs/{id}`: Real-time status, progress percentage, and log history.
- `GET /api/jobs/{id}/clips`: Retrieve rendered clips for a specific job.

### Clip Workstation & Trimming
- `GET /api/clips/{id}`: Detailed clip metrics, transcript context, and AI scores.
- `POST /api/clips/{id}/regenerate`: Fine-tune start and end timestamps and re-render clip.
- `POST /api/clips/{id}/favorite`: Toggle favorite bookmark state.

### Export & Archiving
- `GET /api/export/clip/{id}`: Single clip bundle download (.mp4, .srt, .ass, metadata.json).
- `GET /api/export/clip/{id}/mp4`: Direct MP4 video stream.
- `GET /api/export/job/{id}/batch`: Batch ZIP archive of all rendered clips in a job.
- `POST /api/export/clips/batch`: Multi-selection custom ZIP archive download.

### Settings & Admin
- `GET /api/settings`: Fetch current provider configurations and masked keys.
- `POST /api/settings`: Update API keys, framing preferences, and default styles.
- `POST /api/settings/test`: Validate credentials against remote AI APIs.
- `GET /api/admin/metrics`: Pipeline throughput, error rates, and system telemetry.

---

## Testing

Run the backend test suite:

```bash
cd backend
pytest
```

Run frontend linting and type verification:

```bash
cd frontend
npm run build
```

---

## License

This project is licensed under the Apache License 2.0.
