# AI Video Clipper — Session & Progress Tracker

> **Notice for Future Agents & Sessions**:
> Always read this file at the start of any new session to immediately understand the current state, recent changes, architecture, and user prompts.
> At the end of each session or major feature milestone, update this document with the user's prompt, what was accomplished, files modified, and commit status. Always commit local changes with clean, atomic messages so the user can easily revert if desired.

---

## Current Architecture & System Overview

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui primitives.
  - Follows strict `UI_GUIDELINES.md` (zero-emoji policy in UI controls, Lucide-react SVG icons only, 2-column responsive layout).
- **Backend**: Python 3.11, FastAPI, Pydantic v2, SQLite (local dev) / PostgreSQL.
  - Deterministic 21-stage video pipeline (`backend/app/services/pipeline/pipeline.py`).
- **AI Engine Orchestration**:
  - `DeepgramProvider`: Word-level millisecond audio transcription & timestamps.
  - `GroqProvider`: High-throughput candidate pooling and initial scoring speed.
  - `GeminiProvider`: Multimodal context reasoning, source video title analysis, and social platform copywriting.
  - `HybridOrchestratedAIProvider`: Coordinates Deepgram + Groq + Gemini concurrently.
- **Captions & Hook Presentation**:
  - `libass` burned-in subtitles with font styling, active word highlighting, and emoji stripping (prevents `□` tofu font boxes on system ffmpeg).
  - TikTok rounded background box (`tiktok_rounded_box`) and black pill (`capcut_black_pill`) styles.
  - Persistent sticky hook headers with multi-part series tagging: `PART 1/5 • [HOOK TITLE]`.
- **Export System**:
  - Strict 2-folder structure in ZIP exports (`videos/` and `titles_and_thumbnails/`).
  - 1-Click single-paragraph ready-to-post clipboard copy (`Part X/N: Title — Description #tags`) and downloadable `.txt` files.

---

## Session History Log

### Session 1: Multi-Genre Viral Hook Detection, Series Branding & Single-Paragraph Export
- **Date / Time**: 2026-09-06
- **User Prompt**:
  > *"please the first 10 seconds must be hooked, fight, chaos, arguments, something watching.*
  > *analyze the audio scripts, and the captions to be added on the scren to the each video must be hooked, and properly relevant with the clips extracted.*
  > *Also if i have chosen for eg, 5 video clips from the videos. choose and cut the best video clips that will surely go viral.*
  > *I have multiple apis such as deepgram, groq, gemini, so use the best one, or if possible, listen carefllu, only if possible use them to do different things parallely, one doing the best that it gets best at doing that.*
  > *the video will also have the titles, so analyze that title too.*
  > *for now, i will be uploading, police cam pov, pov runfter, pov cycle chase, pov of vlog, history of american, military histroy, nostaliga content videos, and so on.*
  > *It must support any genere of the videos.*
  > *Also if the videos extreacted are 5 clips, part 1,part 2, etc must be iincldued in captions too.*
  > *the captions must be something like edited in tthe titko,k, like rounded, backgrond around the texts,*
  > *the titles, descriptoive, and hashtags must in a single para for eg, 5 clips, must be icnluded in single single , copy paste clipboard, within the site, and downloadable folder."*

- **Changes & Deliverables**:
  1. **Strict 10-Second Hook Mandate**:
     - Updated `prompt_templates.py` to enforce intense action, conflict, police pursuits, chaos, arguments, or high-stakes revelations in the opening 10 seconds.
     - Updated `audio_analyzer.py` with `CHAOS_ACTION_KEYWORDS` and `ARGUMENT_CLASH_KEYWORDS` (+15 pts) and a **-22 pt penalty** for calm intro greetings (*"hey guys"*, *"welcome back"*).
  2. **Video Title Context & Multi-Genre Specialization**:
     - Injected `{video_title}` context into prompt templates and AI metadata generation.
     - Implemented 6 distinct genre directives: `action_chase_pov`, `military_history`, `nostalgia`, `vlog_pov`, `podcast_debate`, `viral_moments`.
  3. **Multi-API Orchestration**:
     - Built `HybridOrchestratedAIProvider` in `factory.py` pairing Deepgram (word timestamps), Groq (candidate speed), and Gemini (multimodal reasoning & copywriting).
  4. **Multi-Part Series Tagging**:
     - Tagged clips sequentially as `Part 1/5`, `Part 2/5`, etc.
     - Rendered persistent hook headers as `PART 1/5 • [HOOK TITLE]`.
  5. **TikTok Rounded-Box Subtitles**:
     - Added `tiktok_rounded_box` (translucent rounded box `BorderStyle=3` with electric yellow highlight) and `capcut_black_pill` presets.
  6. **1-Click Single-Paragraph Clipboard & Export**:
     - Single paragraph format: `Part X/N: [Title] — [Hook / Description] [5 Hashtags]`.
     - 1-Click "Copy Post" button and `.txt` download in `PlatformMetadataCard.tsx`.
     - "Copy All ({count}) Single-Para" and `.txt` download banner in Project Detail Tab 3.
     - Packaged `single_paragraph_copy_paste.txt` and `titles_and_thumbnails/copy_paste_single_para_all_clips.txt` in ZIP exports.

- **Files Modified**:
  - `backend/app/api/routes/clips.py`
  - `backend/app/api/routes/export.py`
  - `backend/app/api/routes/jobs.py`
  - `backend/app/api/routes/projects.py`
  - `backend/app/core/database.py`
  - `backend/app/core/models.py`
  - `backend/app/core/schemas.py`
  - `backend/app/services/ai/base.py`
  - `backend/app/services/ai/factory.py`
  - `backend/app/services/ai/gemini.py`
  - `backend/app/services/ai/groq.py`
  - `backend/app/services/ai/mock.py`
  - `backend/app/services/ai/prompt_templates.py`
  - `backend/app/services/media/audio_analyzer.py`
  - `backend/app/services/media/captioner.py`
  - `backend/app/services/pipeline/pipeline.py`
  - `backend/tests/test_viral_hook_and_series.py`
  - `frontend/src/app/projects/[id]/page.tsx`
  - `frontend/src/components/review/CaptionPresetPicker.tsx`
  - `frontend/src/components/review/PlatformMetadataCard.tsx`
  - `frontend/src/lib/api.ts`
  - `frontend/src/lib/types.ts`

- **Verification Status**:
  - Backend: 40/40 pytest tests passed.
  - Frontend: TypeScript `tsc --noEmit` passed with 0 errors.

---

### Session 2: Session Tracking System, Git Commits & Vercel Deployment
- **Date / Time**: 2026-09-06
- **User Prompt**:
  > *"from now onward, always keep track of what is happening, and what has happened in a md file, with users prompts.*
  > *Keep a track of the file, what is happening, so when i open a new seesion, agent understands the progress, and status.*
  > *always commit the changes to local, so that i can revert back the changes, i don't like.*
  > *now push the whole in github with proper comments, and deploy to my old and single vercel server"*

- **Status & Actions**:
  - Created `SESSION_TRACKER.md` as permanent ledger for session progress, prompts, and architecture status.
  - Updated `GEMINI.md` to instruct all AI agents in future sessions to read and update `SESSION_TRACKER.md`.
  - Committed changes locally with descriptive multi-line commit message: `32485e3`.
  - Pushed to GitHub repository: `https://github.com/Sange-creator/Clipper.git` on branch `main`.
  - Production Deployment Succeeded on Vercel:
    - Target: `ai-clipper-pro` (`prj_bb57uq24zhBH18NQgo8m98N9MLOh`)
    - Deployment ID: `dpl_36of7VVf7JYUrZqqFUqJmJVf93nK`
    - Status: `● Ready`
    - Live URLs:
      - `https://ai-clipper-pro-lama8050-1395s-projects.vercel.app`
      - `https://frontend-two-mu-2qajzx2xxc.vercel.app`
      - `https://ai-clipper-pro-git-main-lama8050-1395s-projects.vercel.app`
