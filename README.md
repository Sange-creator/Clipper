# AI Video Clipper Pro

Production-grade AI video clipping and short-form discovery platform that automatically discovers, ranks, slices, and renders high-potential short-form clips for TikTok, Instagram Reels, and YouTube Shorts.

---

![AI Video Clipper Pro Multi-Device Showcase](docs/assets/clipper_3devices_showcase.jpg)

---

## Key Capabilities & Features

### 1. Dual Pre-Clipping Hook Strategies (User Choice)
Before launching a clipping job, creators can choose how every extracted clip hooks the audience:
- **⚡ 5s Climax Teaser Hook (In Medias Res / Viral Meta)**:
  - Intelligently locates the most explosive **4–5 second fight, clash, scream, or shocking revelation** inside the moment.
  - Slices and plays this intense climax first (`0.0s – 5.0s`) to catch viewers off-guard and maximize retention.
  - Rewinds to the natural beginning to build up the full story context until resolving the climax and punchline.
  - Subtitles are automatically retimed across both intervals without drift.
- **▶ Direct Chronological Cut**:
  - Slices the video directly from start to finish in normal chronological sequence without moving or splicing scenes.
  - Ideal for clean sequential storytelling, monologues, and tutorials.

### 2. Intense Clash, Fight & Conflict Discovery
- Overhauled reasoning prompts for **Regular Podcast Clipper** and **Long Video Viral Moments**.
- Prioritizes heated arguments, verbal/physical clashes, explosive confrontations, loud reactions, and shocking confessions.
- Heavily penalizes childish, mundane, or boring conversational filler.
- Structured JSON output identifies `climax_start`, `climax_end`, and `climax_summary` timestamps.

### 3. Automated OpenCV Computer Vision Watermark Detection & Eraser
- **Temporal Persistence Analysis**: Samples frames across the video and computes standard deviation variance across pixel regions.
- **Canny Edge Density Scoring**: Distinguishes static logos and channel bugs from natural scene motion.
- **Autonomous Resolution**: Resolves corner locations (`top_right`, `bottom_right`, `top_left`, `bottom_left`, `tiktok_bounce`, `all_corners`).
- **FFmpeg Delogo Filter**: Seamlessly erases watermarks with boundary-clamped coordinates before vertical reframing.

### 4. Complete Metadata Stripping & Anti-Duplicate Architecture
- **Exhaustive Tag Wiping**: Strips QuickTime atoms, camera hardware serials, vendor IDs, GPS coordinates, chapter markers, and creation timestamps (`-map_metadata -1`, `-flags +bitexact`).
- **Anti-Duplicate Perceptual Transform**: Applies subtle micro-adjustments to color vibrance, edge sharpness, and EBU R128 audio loudness normalization to generate fresh perceptual content hashes.

### 5. CapCut & TikTok Boxed Caption Styles
- Word-level animated karaoke captions with colored background bounding boxes using ASS `BorderStyle: 3`.
- Presets: `capcut_black_box`, `capcut_yellow_box`, `tiktok_boxed`, `tiktok_viral`, `hormozi_bold`, `clean_white`, `bold_yellow`, `podcast_box`, `cinematic`, `meme_impact`, and `cyber_neon`.
- Customizable vertical positioning (10% Top to 90% Bottom) with optional persistent TikTok hook headers.

### 6. Strict Dual-Folder Bulk Download ZIP Architecture
Batch downloads from jobs or project workstations output ZIP archives formatted with **strictly two root folders**:
```
zip_root/
├── videos/
│   ├── clip_01_a1b2c3_WHY_NOBODY_TALKS_ABOUT_THIS.mp4
│   ├── clip_02_d4e5f6_THE_GREATEST_MISTAKE_IN_HISTORY.mp4
│   └── ...
└── titles_and_thumbnails/
    ├── clip_01_a1b2c3_WHY_NOBODY_TALKS_ABOUT_THIS_thumbnail.jpg
    ├── clip_01_a1b2c3_WHY_NOBODY_TALKS_ABOUT_THIS_title.txt
    ├── clip_01_a1b2c3_WHY_NOBODY_TALKS_ABOUT_THIS_metadata.json
    ├── clip_02_d4e5f6_THE_GREATEST_MISTAKE_IN_HISTORY_thumbnail.jpg
    ├── clip_02_d4e5f6_THE_GREATEST_MISTAKE_IN_HISTORY_title.txt
    └── clip_02_d4e5f6_THE_GREATEST_MISTAKE_IN_HISTORY_metadata.json
```

---

## Multi-Device & Canvas Format Support

AI Video Clipper Pro provides native, responsive multi-format rendering across Mobile, Tablet, and Desktop screens.

| Format Mode | Aspect Ratio | Target Resolution | Primary Use Case | Output Characteristics |
|:---|:---|:---|:---|:---|
| **Mobile Short-Form** | 9:16 Vertical | 1080 x 1920 | TikTok, Reels, Shorts | Full vertical crop, face/subject focal tracking, animated karaoke captions. |
| **Tablet / Frosted Blur** | 16:9 in 9:16 | 1080 x 1920 | Podcasts, Interviews | 100% widescreen fit centered over a dynamic Gaussian-blurred video canvas. |
| **Desktop / Widescreen** | 16:9 Native | 1920 x 1080 | YouTube, Twitter/X | Preserves source resolution without vertical crop or frame distortion. |

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
15. **Generate Final Clip Boundaries**: Construction of editing timeline (applying 5s climax teaser or direct cut).
16. **Render Clips Using FFmpeg**: 9:16 vertical crop, 16:9 blurred background synthesis, or native 16:9 export.
17. **Generate Captions**: Multi-interval subtitle retiming and ASS/SRT generation.
18. **Generate Thumbnails**: Extraction of high-engagement 9:16 hook keyframes.
19. **Generate Clip Metadata**: Production of viral titles, captions, and platform hashtags.
20. **Store Results**: Persistence of clip assets, video streams, and scoring metrics to local database.
21. **Mark Job Complete**: Finalization of job state and emission of completion signals.

---

## AI Provider Resilience and Fallback Matrix

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

---

## Project Structure

```
Clipper/
|-- backend/
|   |-- app/
|   |   |-- api/routes/          # REST endpoints (upload, jobs, clips, settings, export, admin)
|   |   |-- core/                # Database configuration, SQLite schema, SQLAlchemy models, Pydantic schemas
|   |   |-- services/
|   |   |   |-- ai/              # Resilient AI engine (Groq, Gemini, Local Heuristics, Prompts)
|   |   |   |-- audio/           # Speech-to-text (Deepgram Nova-3, Faster-Whisper)
|   |   |   |-- media/           # FFmpeg rendering, watermark detector, captioner, silence detector
|   |   |   `-- pipeline/        # 21-stage deterministic orchestration & candidate scoring
|   |   `-- main.py              # FastAPI application entrypoint
|   `-- tests/                   # Comprehensive 35+ Pytest test suite
|-- frontend/
|   |-- public/                  # Static assets, brand logos, favicons, web manifest
|   |-- src/
|   |   |-- app/                 # Next.js 15 App Router pages (upload, jobs, clips, projects, settings, admin)
|   |   |-- components/
|   |   |   |-- ui/              # shadcn/ui components (buttons, badges, cards, sliders)
|   |   |   |-- upload/          # Single and batch video drag-and-drop wizards with hook strategy selector
|   |   |   |-- processing/      # 21-stage live progress monitor & log telemetry
|   |   |   `-- review/          # Clip workstation, timeline scrubber, player safe-zone
|   |   `-- lib/                 # Type definitions, API client, utility functions
|   `-- tailwind.config.ts       # shadcn/ui design tokens & zinc dark theme
`-- docs/assets/                 # Architecture diagrams and UI preview assets
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

The web application is accessible at `http://localhost:3000`.

---

## Live Deployments

- **Production Frontend**: [https://ai-clipper-pro.vercel.app](https://ai-clipper-pro.vercel.app)
- **Secondary / Legacy Domain**: [https://clipper-ai-pro.vercel.app](https://clipper-ai-pro.vercel.app)
- **Source Code**: [https://github.com/Sange-creator/Clipper](https://github.com/Sange-creator/Clipper)

---

## License

This project is licensed under the Apache License 2.0.
