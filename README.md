# AI Video Clipper Pro

AI Video Clipper Pro is an automated content discovery and short-form video optimization platform. It analyzes long-form media, detects high-retention narrative moments, reframes footage to vertical 9:16 aspect ratios, generates animated subtitles, and prepares distribution-ready packages for TikTok, Instagram Reels, and YouTube Shorts.

---

## Architecture Overview

The system uses a decoupled client-server architecture:

- **Web Client (Frontend)**: Built with Next.js 15, TypeScript, Tailwind CSS, and shadcn/ui. Handles user workflows, multi-video batch management, safe-zone previewing, and subtitle customization.
- **Media Processing Engine (Backend)**: Built with Python 3.11, FastAPI, Pydantic, FFmpeg, OpenCV, and faster-whisper. Executes deterministic 21-stage media analysis, nonlinear editing, acoustic modeling, and hardware-accelerated video rendering.

### Deployment Model

Due to the compute and storage demands of video transcoding, acoustic analysis, and computer vision operations, the media processing backend runs outside serverless environments.

| Component | Hosted Location | Description |
|:---|:---|:---|
| **Web Interface** | `https://ai-clipper-pro.vercel.app/` | Production web application. Connects to any accessible Clipper backend instance via user-configured API endpoints. |
| **Media Engine** | Local Machine / Private Server (`localhost:8000`) | Handles all FFmpeg rendering, transcription, and candidate scoring on dedicated hardware. |

Users can operate the software in two configurations:
1. **Hybrid Execution (Recommended)**: Use the hosted web interface at `https://ai-clipper-pro.vercel.app/` connected to a backend running on `localhost:8000` or a remote server.
2. **Local Execution**: Run both the web interface (`localhost:3000`) and the backend (`localhost:8000`) locally.

---

## System Requirements

### Processing Backend
- Operating System: macOS, Linux, or Windows (WSL2 recommended for Windows)
- Python: 3.11 or higher
- FFmpeg: Version 6.0 or higher, compiled with `libass` support
- Memory: Minimum 8 GB RAM (16 GB recommended for concurrent video processing)
- Storage: 10 GB free disk space for temporary media processing

### Web Client (Optional for Local Hosting)
- Node.js: 18.17.0 or higher
- Package Manager: npm, pnpm, or yarn

---

## Quick Start

### 1. Start the Media Processing Backend

Clone the repository and enter the backend directory:

```bash
git clone https://github.com/Sange-creator/Clipper.git
cd Clipper/backend
```

Create and activate a virtual environment:

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```bash
pip install -e .
```

Configure environment settings:

```bash
cp .env.example .env
```

Edit `.env` to configure AI provider keys (optional; a deterministic mock engine is available for offline testing):

```env
# Reasoning and Transcription Providers
GEMINI_API_KEY=""
GROQ_API_KEY=""
DEEPGRAM_API_KEY=""

# Media Storage Paths
UPLOAD_DIR="./storage/uploads"
PROCESSED_DIR="./storage/processed"
SUBTITLE_DIR="./storage/subtitles"
THUMBNAIL_DIR="./storage/thumbnails"
```

Start the service with Uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify the backend service status:

```bash
curl http://127.0.0.1:8000/api/health
```

The interactive OpenAPI specification is available at `http://localhost:8000/docs`.

---

### 2. Connect the Web Interface

#### Method A: Use Hosted Web Client
1. Navigate to `https://ai-clipper-pro.vercel.app/` in your browser.
2. The client defaults to `http://127.0.0.1:8000/api`. If your backend runs on a different port or remote server, navigate to **Settings** and update the API base URL.
3. Verify connection via the health badge in the top navigation bar.

#### Method B: Run Web Client Locally
To host the frontend locally:

```bash
cd ../frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## Processing Pipeline

Every media source passes through a deterministic 21-stage execution pipeline:

```
[Upload / Ingestion]
       |
       v
 1. Container & Codec Validation (FFprobe)
 2. Stream Metadata Extraction
 3. Job Record Initialization
 4. Audio Extraction (16 kHz Mono PCM WAV)
 5. Transcription & Word Timestamp Alignment (Deepgram / Faster-Whisper)
 6. Acoustic Silence & Scene Transition Analysis
 7. Structured Transcript Serialization
 8. Candidate Moment Identification
 9. Narrative Context Expansion
10. Linguistic Hook & Tension Analysis
11. Multi-Factor Composite Quality Scoring
12. Temporal Intersection-over-Union (IoU) Non-Maximum Suppression
13. Global Ranking & Score Normalization
14. Target Duration Constraint Enforcement (15-30s, 30-45s, 45-60s, 60-90s)
15. Timeline Synthesis (Climax Teaser or Direct Chronological Cut)
16. Video Reframing & Transcoding (FFmpeg 9:16 Vertical / Frosted Canvas)
17. Multi-Interval Subtitle Alignment (ASS / SRT Burn-in)
18. Keyframe Thumbnail Extraction
19. Social Distribution Metadata Generation
20. Database Record Synchronization
21. Job Completion Signoff
```

---

## Core Capabilities

### Nonlinear Climax Teaser Hook
For content where the peak emotional or high-energy moment occurs midway through a narrative, the system offers nonlinear timeline restructuring:
- Identifies the highest-intensity 5 to 8 second segment within the clip boundaries.
- Slices and inserts this climax segment at the beginning (`0:00 - 0:06`).
- Sequentially restarts the clip from its narrative beginning, building up to the climax and payoff.
- Subtitle timecodes and audio transitions are dynamically retimed to prevent desynchronization.

### Direct Chronological Cut
- Detects and trims conversational pleasantries, introductory greetings, and dead air.
- Starts playback immediately on the opening hook statement while preserving chronological flow.

### Coordinated On-Screen Captions
- **Series Identifier Badge**: Dedicated pill badge displayed at top-center (`PART 1`, `PART 2`, etc.) without fraction indicators.
- **Hook Headline**: Real-time dialogue-analyzed topical hook banner displayed beneath the series badge.
- **Spoken Dialogue Subtitles**: Word-level karaoke highlighting with configurable styling (`tiktok_rounded_box`, `capcut_black_pill`, `hormozi_bold`, `clean_white`).

### Automated Watermark Detection and Removal
- Uses temporal persistence variance across sample frames to detect static network bugs and watermark coordinates.
- Applies Canny edge density filters to identify static overlays.
- Employs FFmpeg delogo filtering to interpolate and remove detected logos prior to vertical reframing.

### Multi-Platform Distribution Assets
- **1-Click Copy**: Structured post copy combining title, hook description, and curated hashtags into a single block.
- **Structured ZIP Export**: Bulk export packages organized into clean, predictable directories:
  ```
  archive.zip/
  ├── videos/
  │   ├── clip_01_PART_1_HOOK_TITLE.mp4
  │   └── clip_02_PART_2_HOOK_TITLE.mp4
  └── titles_and_thumbnails/
      ├── copy_paste_single_para_all_clips.txt
      ├── clip_01_PART_1_thumbnail.jpg
      ├── clip_01_PART_1_title.txt
      └── clip_01_PART_1_metadata.json
  ```

---

## Configuration Reference

Key configuration options supported via environment variables:

| Variable | Type | Default | Description |
|:---|:---|:---|:---|
| `GEMINI_API_KEY` | String | None | Google Gemini API key for multimodal analysis and copywriting. |
| `GROQ_API_KEY` | String | None | Groq API key for low-latency candidate moment extraction. |
| `DEEPGRAM_API_KEY` | String | None | Deepgram API key for word-level speech-to-text. |
| `DATABASE_URL` | String | `sqlite+aiosqlite:///./storage/clipper.db` | SQLAlchemy database connection URI. |
| `UPLOAD_DIR` | Path | `./storage/uploads` | Path for raw video uploads. |
| `PROCESSED_DIR` | Path | `./storage/processed` | Path for rendered video clips. |
| `SUBTITLE_DIR` | Path | `./storage/subtitles` | Path for generated subtitle assets (ASS/SRT). |
| `THUMBNAIL_DIR` | Path | `./storage/thumbnails` | Path for extracted thumbnail keyframes. |

---

## Automated Verification

The backend includes a comprehensive test suite covering API contracts, subtitle retiming, AI provider fallbacks, and rendering pipelines.

Run tests:

```bash
cd backend
.venv/bin/pytest -v
```

Type-check frontend:

```bash
cd frontend
npx tsc --noEmit
```

Update knowledge graph:

```bash
graphify update .
```

---

## License

This project is licensed under the Apache License 2.0. See the LICENSE file for details.
