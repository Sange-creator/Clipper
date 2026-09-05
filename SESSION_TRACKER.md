# AI Video Clipper — Session & Progress Tracker

> **Notice for Future Agents & Sessions**:
> Always read this file at the start of any new session to immediately understand the current state, recent changes, architecture, and user prompts.
> At the end of each session or major feature milestone, update this document with the user's prompt, what was accomplished, files modified, and commit status. Always commit local changes with clean, atomic messages so the user can easily revert if desired.

---

## Current Architecture & System Overview

- **Primary Live Production Server**: `https://ai-clipper-pro.vercel.app/`
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
    - Primary Production URL: `https://ai-clipper-pro.vercel.app/`
    - Alternative Aliases:
      - `https://clipper-ai-pro.vercel.app/`
      - `https://ai-clipper-pro-lama8050-1395s-projects.vercel.app/`
      - `https://frontend-two-mu-2qajzx2xxc.vercel.app/`

---

### Session 3: Live Server Alias Correction & Graphify Installation (Local & Global Antigravity)
- **Date / Time**: 2026-09-06
- **User Prompt**:
  > *"u are a fukcing idiot, my live server is this : 
  > https://ai-clipper-pro.vercel.app/
  > 
  > please keep a track of what is what>
  > 
  > please install a graphify to keep track for this : https://github.com/Graphify-Labs/graphify.git
  > 
  > and always begin the session with this for this project,
  > 
  > Install globally for antigrabity too"*

- **Status & Actions**:
  1. **Primary Production Server Verified & Aliased**:
     - Verified Vercel project `ai-clipper-pro`.
     - Explicitly mapped the latest production deployment (`dpl_36of7VVf7JYUrZqqFUqJmJVf93nK`) to alias `https://ai-clipper-pro.vercel.app/` and verified with `curl -ILs` (HTTP 200 OK).
     - Recorded `https://ai-clipper-pro.vercel.app/` as the single primary production server in `GEMINI.md` and `SESSION_TRACKER.md`.
  2. **Graphify Knowledge Graph CLI Installed**:
     - Installed `graphifyy` via `uv tool`.
     - Ran AST code extraction across 112 repository files.
     - Generated full codebase knowledge graph in `graphify-out/`:
       - `graphify-out/graph.json`: 1,202 nodes, 1,619 edges, 113 communities.
       - `graphify-out/GRAPH_REPORT.md`: God nodes, community structure, and architecture overview.
       - `graphify-out/graph.html`: Interactive visual force-directed graph.
  3. **Antigravity Global & Project Skills Configured**:
     - Installed global Antigravity skill in `/Users/saangetamang/.gemini/config/skills/graphify/SKILL.md` and `/Users/saangetamang/.agents/skills/graphify/SKILL.md`.
     - Installed workspace skill in `.agents/skills/graphify/SKILL.md`.
     - Added always-on rule in `.agents/rules/graphify.md` and workflow in `.agents/workflows/graphify.md`.
  4. **Engineering Guidelines Updated in `GEMINI.md`**:
     - Mandatory rule added: Every future session MUST begin by consulting `SESSION_TRACKER.md` and Graphify (`graphify-out/GRAPH_REPORT.md` or `graphify query "<question>"`).
     - After modifying code files, assistant must run `graphify update .` to keep the AST graph synchronized.

---

### Session 4: Production Deployment Alias Sync (`https://ai-clipper-pro.vercel.app/`)
- **Date / Time**: 2026-09-06
- **User Prompt**:
  > *"update teh changes to vercerl : https://github.com/Graphify-Labs/graphify.git"*
  > *"https://ai-clipper-pro.vercel.app/"*
- **Status & Actions**:
  - Latest production deployment: `dpl_5nSqB6TwobY6GbuwaPBHrnGKbNcv` (`ai-clipper-fauo77n4m-lama8050-1395s-projects.vercel.app`).
  - Successfully mapped and verified production aliases:
    - `https://ai-clipper-pro.vercel.app/` -> `dpl_5nSqB6TwobY6GbuwaPBHrnGKbNcv` (HTTP/2 200 OK)
    - `https://clipper-ai-pro.vercel.app/` -> `dpl_5nSqB6TwobY6GbuwaPBHrnGKbNcv` (HTTP/2 200 OK)
  - All multi-genre hooks, series numbering, TikTok rounded box subtitles, and Graphify integrations are live.

---

### Session 5: Dual Captions (Part 1..N + Script Headline) & Teaser Climax Timeline Splicing
- **Date / Time**: 2026-09-06
- **User Prompt**:
  > *"in the cpations, when 4 clips are chosen by the user, part 1, part2, 3, and 4 are not being shown at the captions.*
  > *one captions must be part 1,2,3,4*
  > *another captions must be related with the clips(analyze the audio script, and write the captions).*
  > *also the clips that u just generated have no hook at the starting 10s at all, if i have selected If I have selected 5-second climax teaser, then what it is to is suppose the clipped video is about 50 second long, okay? And in the middle of somewhere there is intense 10-second hook, then you have to cut that part and then bring it to the first 10-second part, and then the video must gradually go on to meet that cut part, okay? That cut part must be again shown at the later video. And another section is that direct chronological cut, and then in in this case the direct the direct 10-second clips must be shown at the first second video, at the first 10 second and the video must go on. And the you the technique the technique and the the technique and the method that you have used to extract the hook is not properly appropriate and is not properly working. The clips that you have generated have no hooks at all. Please update the method and use the best method you can."*

- **Changes & Deliverables**:
  1. **Dual On-Screen Captions with Explicit Series Numbering**:
     - Layer 2 (`PartBadge`): Displays `PART 1/4`, `PART 2/4`, etc. in a dedicated, high-contrast on-screen pill badge (`Style: PartBadge`, top-center `MarginV: 75`).
     - Layer 1 (`HookHeader`): Dynamically extracts and writes punchy, hook headlines analyzing the spoken dialogue of the audio script (`extract_hook_headline_from_script`). In teaser mode, shows `WAIT FOR IT...` during the teaser climax, then transitions to the authentic script hook title during the story.
     - Layer 0: Spoken word-level karaoke subtitles with word highlights.
  2. **5-Second Climax Teaser Hook Timeline Splicing (`teaser_climax_hook`)**:
     - Implemented `find_peak_climax_moment`: Detects the single most intense 5-8 second climax/fight/chaos/argument window in the middle/later part of the clip (`clip_start + 4.0` onwards).
     - Slices that climax moment to 0:00 as an opening teaser hook, then seamlessly plays the full chronological story from `cand.start` to `cand.end` to meet that cut again (`keep = [[climax_start, climax_end], [cand.start, cand.end]]`).
  3. **Direct Chronological Cut (`direct_chronological`)**:
     - Implemented `trim_calm_intro_to_hook`: Strips calm intro greetings (*"welcome back"*, *"hey guys"*, silence) and starts immediately at 0:00 on the intense hook sentence.
  4. **Frontend Hook Strategy Selector**:
     - Added 2-column card selector for Hook Extraction Strategy in Tab 2 of `frontend/src/app/projects/[id]/page.tsx` adhering to the zero-emoji policy and dark-mode obsidian aesthetic.
     - Wired `hook_strategy` into `api.processProject`.
  5. **Subtitle Retiming Multi-Interval Bug Fix**:
     - Fixed bug where `renderer.py` called `retime_ass_subtitles` on subtitle files that were already retimed with `keep_intervals`, which squashed timestamps to 0.0.
  6. **Pipeline Integration**:
     - Wired `resolve_clip_timeline_and_hook` into both single-video (`process_video_pipeline`) and multi-video project batch (`process_project_pipeline`).
  7. **Testing & Knowledge Graph**:
     - Added `test_four_clips_part_badges_and_audio_script_hook_captions` verifying 4-clip series part badges, script headlines, and teaser interval splicing.
     - 41/41 pytest tests passing (100%).
     - Frontend `npx tsc --noEmit` passed with 0 errors.
     - `graphify update .` synced knowledge graph (1,221 nodes, 1,649 edges, 113 communities).

- **Files Modified**:
  - `backend/app/services/media/audio_analyzer.py`
  - `backend/app/services/media/captioner.py`
  - `backend/app/services/media/renderer.py`
  - `backend/app/services/pipeline/pipeline.py`
  - `backend/tests/test_hook_strategy.py`
- **Production Deployment Status**:
  - Target: `ai-clipper-pro` (`prj_bb57uq24zhBH18NQgo8m98N9MLOh`)
  - Deployment ID: `dpl_EnTv5qZRUSGi9c56X1Qfx8rKpbyK`
  - Primary Production URL: `https://ai-clipper-pro.vercel.app/` (HTTP/2 200 OK)
  - Alternative Alias: `https://clipper-ai-pro.vercel.app/` (HTTP/2 200 OK)

