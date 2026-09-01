# AI Clipper — Next Version Backlog

## Purpose

This backlog defines the next production-focused version of the AI video clipper after the MVP. The goal is to move from **working automatic clipping** to a **high-quality short-form content engine** that can process batches of long videos, generate better clips, make them platform-native, and learn from actual performance.

> Product principle: optimize for **viral potential**, not guaranteed virality. Preserve source meaning, context, and authenticity while maximizing hook strength, retention potential, payoff, and shareability.

---

# Priority System

- **P0 — Critical:** Required for the next release or a major reliability problem.
- **P1 — High:** Strongly improves clip quality or product usability.
- **P2 — Medium:** Valuable enhancement after the core system is stable.
- **P3 — Later:** Experimental or growth-stage feature.

---

# Release Goal

The next version should allow a user to:

1. Upload many long videos in one project.
2. Process them asynchronously and reliably.
3. Discover a large candidate pool.
4. Rank candidates using multi-factor scoring.
5. Automatically remove repetitive or overlapping clips.
6. Select a requested number of clips from a larger candidate pool.
7. Respect a requested duration range without destroying narrative quality.
8. Reframe landscape footage into 9:16 intelligently.
9. Generate polished captions.
10. Review, edit, regenerate, favorite, reject, and export clips.
11. Generate platform-specific titles/captions/metadata.
12. Preserve enough structured data to learn from future performance.

---

# EPIC 1 — Batch Processing & Job Reliability

## P0-01 — Batch Uploads

**Goal:** Support 20–30+ videos in a single project.

### Tasks
- Add multi-file upload UI.
- Show per-file upload progress.
- Show aggregate project progress.
- Validate files before upload.
- Store upload metadata.
- Generate a stable content hash for each source video.
- Prevent duplicate processing when the same source is uploaded again.

### Acceptance Criteria
- User can upload at least 30 videos without UI failure.
- Large uploads do not freeze the browser.
- Duplicate files are detected.
- Each video gets its own processing state.

**Priority:** P0

---

## P0-02 — Background Job Pipeline

### Tasks
Create jobs for:

- media inspection
- audio extraction
- transcription
- scene detection
- candidate discovery
- candidate scoring
- ranking
- final clip planning
- rendering
- thumbnail generation
- metadata generation

### Acceptance Criteria
- Processing continues if the user leaves the page.
- Jobs survive worker restarts.
- Jobs are retryable.
- Failed stages report a useful error.
- Jobs are idempotent.

**Priority:** P0

---

## P0-03 — Job Progress Events

### Tasks
Expose:

- overall progress
- current stage
- per-video status
- candidate count
- clips selected
- clips rendered

Use SSE or WebSockets.

### Example

```text
Analyzing videos        34%
Transcribing            7 / 20
Candidates found        182
Ranking candidates      68%
Rendering               12 / 20
```

**Priority:** P0

---

# EPIC 2 — Better AI Clip Discovery

## P0-04 — Candidate Overgeneration

Do not directly generate the number of clips requested by the user.

### Logic

```text
Requested clips = 20
        ↓
Generate 100–200 candidates
        ↓
Score candidates
        ↓
Remove weak candidates
        ↓
Remove overlaps / duplicates
        ↓
Rank globally
        ↓
Select best 20
```

### Acceptance Criteria
- Candidate pool is substantially larger than final requested count.
- Final selections are not simply the first N candidates returned by the model.

**Priority:** P0

---

## P0-05 — Context-Aware Clip Boundaries

### Tasks
For every candidate, determine:

- hook start
- required context
- escalation
- payoff
- natural ending

Then produce final start/end timestamps.

### Rules
- Do not cut off the payoff.
- Do not include unnecessary setup.
- Avoid starting mid-sentence unless intentional and coherent.
- Prefer natural speech boundaries.

**Priority:** P0

---

## P0-06 — Multi-Factor Clip Scoring

Store individual scores for:

- hook
- retention
- curiosity
- emotion
- story completeness
- payoff
- shareability
- novelty
- quotability
- visual quality
- audio quality
- platform fit

### Acceptance Criteria
- Scores are normalized 0–100.
- Composite score is reproducible from stored values.
- The system records the AI's reasoning.
- Scoring weights are configurable.

**Priority:** P0

---

## P1-07 — Dynamic Hook Optimization

### Goal
Improve the first seconds without changing the meaning of the source.

### Tasks
- Identify weak openings.
- Search nearby transcript windows for a stronger natural opening.
- Compare candidate openings.
- Penalize misleading context shifts.

### Safety/quality rule
Never create a deceptive quote by removing context that materially changes meaning.

**Priority:** P1

---

## P1-08 — Duplicate & Near-Duplicate Detection

### Detect
- same timestamp ranges
- overlapping transcript content
- semantically identical moments
- repeated talking points
- clips from the same story beat

### Acceptance Criteria
The final 20 clips should feel meaningfully different.

**Priority:** P1

---

## P1-09 — Cross-Video Global Ranking

Instead of ranking clips independently per video, combine all candidates into one pool.

### Example

```text
Video A → 42 candidates
Video B → 31 candidates
Video C → 57 candidates

                ↓

Global pool → 130 candidates
                ↓

Top 20 across entire project
```

Add a configurable source-diversity preference.

**Priority:** P1

---

# EPIC 3 — Smart Duration Engine

## P0-10 — Duration Ranges

Support:

- 15–30 seconds
- 30–45 seconds
- 45–60 seconds
- 60–90 seconds
- custom minimum/maximum

### Rule
Duration is a **target range**, not a blind hard cut.

**Priority:** P0

---

## P1-11 — Narrative-Aware Duration Selection

The system should choose the best duration inside the user's target range based on:

- context
- hook
- story progression
- payoff
- natural ending
- speech boundaries

### Example

User asks for 30–45 seconds.

AI chooses 37 seconds because the payoff lands at 37s.

**Priority:** P1

---

# EPIC 4 — Smart Vertical Reframing

## P0-12 — 9:16 Conversion

Render final clips at:

```text
1080 × 1920
9:16
```

Preserve source frame rate when practical.

**Priority:** P0

---

## P1-13 — Face Detection & Tracking

### Tasks
- Detect faces.
- Identify primary speaker.
- Track face position over time.
- Generate a dynamic crop path.
- Keep the speaker inside a safe region.

### Acceptance Criteria
- No obvious head cropping during normal talking-head footage.
- Camera movement does not cause violent crop jumps.

**Priority:** P1

---

## P1-14 — Multi-Person Reframing

Support conversations and podcasts.

### Logic

```text
Speaker A talking → focus A
Speaker B responds → focus B
Both relevant → wider crop
```

Avoid excessive camera switching.

**Priority:** P1

---

## P2-15 — Visual Attention Model

Later, rank important visual subjects beyond faces:

- products
- demonstrations
- objects
- slides
- screenshots
- action

Use representative frames and visual analysis only where needed.

**Priority:** P2

---

# EPIC 5 — Captions & Visual Styling

## P0-16 — High-Quality Captions

### Requirements
- Whisper-derived timing.
- Good line breaks.
- No hallucinated words.
- Readable on mobile.
- Avoid covering faces when possible.

### Output

```text
SRT
ASS
```

**Priority:** P0

---

## P1-17 — Caption Presets

Initial presets:

- Clean
- Bold
- Podcast
- Meme
- Cinematic
- News
- Gaming

### Architecture
Caption templates must be data/config driven rather than hard-coded into one renderer.

**Priority:** P1

---

## P1-18 — Keyword Emphasis

Optionally emphasize high-value words such as:

- numbers
- surprising claims
- emotional words
- names
- punchlines

Never over-stylize every word.

**Priority:** P1

---

# EPIC 6 — Clip Review Studio

## P0-19 — Clip Review Grid

Show generated clips as cards with:

- preview
- duration
- viral potential score
- source video
- reason for selection
- status

Actions:

- Play
- Favorite
- Reject
- Edit
- Regenerate
- Export

**Priority:** P0

---

## P0-20 — Manual Boundary Editing

Allow the user to adjust:

- start
- end

Re-render without rerunning AI discovery.

**Priority:** P0

---

## P1-21 — Regenerate Clip

User can request:

- stronger hook
- shorter version
- longer version
- more context
- different ending
- different caption style

The system should preserve the original candidate for comparison.

**Priority:** P1

---

## P1-22 — Favorites & Rejection Feedback

Store:

```text
accepted
rejected
favorite
manually edited
regenerated
```

This becomes valuable training/feedback data later.

**Priority:** P1

---

# EPIC 7 — Platform Optimization

## P1-23 — Platform Profiles

Support:

```text
TikTok
Instagram Reels
YouTube Shorts
```

Create a shared clip and platform-specific metadata layer.

**Priority:** P1

---

## P1-24 — Metadata Generation

For each clip generate:

- title
- short caption
- description
- hashtags
- optional CTA

Do not generate spammy hashtag blocks.

**Priority:** P1

---

## P2-25 — Platform Variant Generation

Allow the same clip to have slightly different:

- opening text overlay
- title
- caption
- CTA
- hashtag strategy

Keep source footage unchanged unless the user explicitly requests a variant edit.

**Priority:** P2

---

# EPIC 8 — Thumbnails & Visual Packaging

## P1-26 — Automatic Thumbnail Selection

Choose frames based on:

- face visibility
- emotional expression
- visual clarity
- relevance to clip topic

Output high-quality thumbnail JPG/PNG.

**Priority:** P1

---

## P2-27 — AI Thumbnail Text

Optional short headline generated from the clip.

Rules:

- 2–7 words preferred.
- Must not contradict the video.
- Avoid clickbait that materially misrepresents content.

**Priority:** P2

---

# EPIC 9 — AI Provider Reliability & Cost Control

## P0-28 — Provider Abstraction

Create:

```text
AIProvider
 ├── GeminiProvider
 ├── GroqProvider
 └── OptionalFallbackProvider
```

No API provider calls should be scattered throughout the application.

**Priority:** P0

---

## P0-29 — AI Response Validation

All model outputs must use structured JSON and be validated with Pydantic/Zod.

### Handle
- malformed JSON
- missing fields
- invalid timestamps
- impossible scores
- model refusal
- API timeouts

**Priority:** P0

---

## P0-30 — AI Caching

Cache:

- transcript analysis
- candidate discovery
- candidate scoring
- frame analysis
- metadata generation

Use deterministic content/configuration keys where possible.

**Priority:** P0

---

## P1-31 — AI Quota Tracking

Track per provider:

- requests
- estimated tokens
- failures
- rate limits
- latency
- cost estimate

Show internal admin metrics.

**Priority:** P1

---

## P1-32 — Automatic Provider Fallback

When the primary provider fails or reaches configured limits:

```text
Gemini
  ↓ failure / quota
Fallback provider
  ↓
Retry structured task
```

Record the provider used for every AI request.

**Priority:** P1

---

# EPIC 10 — Data Model & Observability

## P0-33 — Core Database Entities

Minimum entities:

```text
users
projects
videos
video_jobs
transcripts
scenes
clip_candidates
clips
render_jobs
ai_requests
```

**Priority:** P0

---

## P1-34 — Processing Audit Trail

Store:

- pipeline stage
- timestamp
- provider
- model
- input/config hash
- duration
- result
- failure reason

This makes debugging possible.

**Priority:** P1

---

## P1-35 — Admin Dashboard

Show:

- jobs today
- failed jobs
- average processing time
- clips generated
- provider error rates
- average AI latency
- storage usage

**Priority:** P1

---

# EPIC 11 — Storage & Media Lifecycle

## P0-36 — Object Storage

Use a production object store such as Cloudflare R2 or S3.

Separate:

```text
originals/
proxies/
audio/
transcripts/
clips/
thumbnails/
exports/
```

**Priority:** P0

---

## P1-37 — Cleanup Policies

Implement retention rules for:

- temporary audio
- extracted frames
- intermediate renders
- failed job artifacts

Do not delete user-selected final clips automatically.

**Priority:** P1

---

# EPIC 12 — Performance & Infrastructure

## P0-38 — Worker Concurrency Controls

Never start unlimited FFmpeg or Whisper processes.

Configure limits based on:

- CPU
- RAM
- GPU availability
- storage throughput

**Priority:** P0

---

## P0-39 — Proxy Media Pipeline

Create low-resolution proxy media for operations that do not need the original resolution.

Use originals only for final render.

**Priority:** P0

---

## P1-40 — Resume From Last Completed Stage

If rendering fails after transcription and ranking, do not rerun earlier stages unnecessarily.

### Example

```text
Upload       ✓
Transcribe   ✓
Analyze      ✓
Rank         ✓
Render       ✗

Retry → Render only
```

**Priority:** P1

---

# EPIC 13 — Security

## P0-41 — Secure Upload Validation

Validate:

- file type
- extension
- MIME type
- file size
- duration
- codec

Reject malformed media safely.

**Priority:** P0

---

## P0-42 — Secrets Management

Never expose:

- Gemini API keys
- Groq API keys
- database credentials
- object-storage credentials
- Redis credentials

Use server-side environment variables/secrets.

**Priority:** P0

---

## P1-43 — Safe FFmpeg Invocation

Never concatenate raw user input into shell commands.

Use argument arrays and validated paths.

**Priority:** P1

---

# EPIC 14 — Quality Evaluation

## P0-44 — Offline Evaluation Dataset

Create a small internal benchmark of source videos with human-labeled:

- good clips
- bad clips
- strong hooks
- weak hooks
- context-complete clips
- misleading clips

Use it to compare scoring changes.

**Priority:** P0

---

## P1-45 — Clip Quality Metrics

Track internal metrics such as:

- average candidate score
- human acceptance rate
- regeneration rate
- rejection rate
- average clip duration
- percentage of clips requiring manual boundary edits

**Priority:** P1

---

## P2-46 — A/B Prompt Evaluation

Allow two prompt versions to be evaluated against the same benchmark.

Store:

- prompt version
- model
- scores
- human preference

**Priority:** P2

---

# EPIC 15 — Learning From Real Performance

## P2-47 — Performance Data Model

Prepare for importing:

- views
- likes
- comments
- shares
- saves
- completion rate
- average watch time
- retention

Do not require these metrics for the first version.

**Priority:** P2

---

## P3-48 — Learned Ranking Model

Once enough labeled/performance data exists, train a ranking model that learns from:

- AI scores
- transcript features
- duration
- topic
- hook style
- emotion
- source type
- actual performance

Use the AI score as one feature rather than the sole ranking mechanism.

**Priority:** P3

---

# EPIC 16 — Product UX Improvements

## P1-49 — Project Dashboard

Show:

```text
Project
├── Sources
├── Analysis
├── Candidates
├── Generated Clips
├── Favorites
└── Exports
```

**Priority:** P1

---

## P1-50 — Saved Clip Presets

Allow users to save:

```text
Preset: Podcast Shorts
Duration: 30–60s
Aspect: 9:16
Captions: Bold
Platform: All
```

**Priority:** P1

---

## P2-51 — Bulk Actions

Allow users to:

- select many clips
- apply caption style
- render selected
- download selected
- reject selected
- export metadata

**Priority:** P2

---

# EPIC 17 — Export & Publishing

## P1-52 — Batch Export

Export multiple clips as a ZIP or through direct object-storage downloads.

Include:

```text
clips/
metadata/
subtitles/
thumbnails/
```

**Priority:** P1

---

## P2-53 — Social Publishing Integrations

Later support direct publishing where official APIs and account permissions allow it.

Initial architecture should not assume direct publishing is available.

**Priority:** P2

---

# Recommended Technical Order

Do not implement the backlog strictly by epic number. Build in this order:

## Phase A — Production Foundation

```text
P0-01  Batch Uploads
P0-02  Background Jobs
P0-03  Progress Events
P0-10  Duration Ranges
P0-12  9:16 Conversion
P0-16  Captions
P0-19  Clip Review Grid
P0-20  Manual Boundary Editing
```

## Phase B — Clip Intelligence

```text
P0-04  Candidate Overgeneration
P0-05  Context-Aware Boundaries
P0-06  Multi-Factor Scoring
P1-07  Dynamic Hook Optimization
P1-08  Duplicate Detection
P1-09  Global Ranking
P1-11  Narrative-Aware Duration
```

## Phase C — Quality & Rendering

```text
P1-13  Face Tracking
P1-14  Multi-Person Reframing
P1-17  Caption Presets
P1-18  Keyword Emphasis
P1-26  Thumbnails
P1-21  Regenerate Clip
```

## Phase D — Reliability & Scale

```text
P0-28  Provider Abstraction
P0-29  AI Response Validation
P0-30  AI Caching
P0-33  Database Entities
P0-36  Object Storage
P0-38  Worker Concurrency
P0-39  Proxy Media
P0-40  Resume Pipeline
P0-41  Upload Validation
```

## Phase E — Intelligence Loop

```text
P1-31  AI Quota Tracking
P1-32  Provider Fallback
P1-34  Audit Trail
P0-44  Evaluation Dataset
P1-45  Quality Metrics
P2-47  Performance Data
P3-48  Learned Ranking
```

---

# Definition of Done — Next Version

The release is ready when all of the following are true:

- [ ] User can upload 20–30 long videos in one project.
- [ ] Uploads are resumable/reliable enough for normal production use.
- [ ] Processing runs asynchronously.
- [ ] Failed jobs can retry.
- [ ] Completed stages are not unnecessarily repeated.
- [ ] Source videos are transcribed with timestamps.
- [ ] The system discovers substantially more candidates than requested.
- [ ] Candidates are scored across multiple dimensions.
- [ ] Near-duplicate clips are removed.
- [ ] Final clips are globally ranked across the project.
- [ ] Duration is selected intelligently inside the user's target range.
- [ ] Clips preserve narrative context and payoff.
- [ ] Landscape footage can be converted to 9:16.
- [ ] Faces are tracked for talking-head content.
- [ ] Captions are readable and timestamp-accurate.
- [ ] Users can review and edit generated clips.
- [ ] Users can regenerate individual clips.
- [ ] Platform-specific metadata can be generated.
- [ ] AI responses are validated.
- [ ] API failures have fallback/retry handling.
- [ ] AI requests are cached where appropriate.
- [ ] API keys never reach the client.
- [ ] Media processing is isolated from the frontend/serverless runtime.
- [ ] Internal metrics exist for clip acceptance and processing reliability.

---

# Future Vision

The long-term architecture should evolve from:

```text
AI finds clips
```

to:

```text
AI discovers
   ↓
AI ranks
   ↓
AI edits
   ↓
User reviews
   ↓
Platform performance is collected
   ↓
System learns what works
   ↓
Ranking improves
   ↓
Better clips are produced automatically
```

The ultimate product should behave like an **AI short-form content editor + ranking engine**, not merely a video cutter.

---

# Backlog Rules for Future Development

1. Do not sacrifice source meaning for clickability.
2. Do not promise or claim guaranteed virality.
3. Prefer measurable quality improvements over adding flashy features.
4. Keep AI provider integrations replaceable.
5. Keep rendering deterministic and local/server-side.
6. Cache expensive AI work.
7. Keep pipeline stages independently retryable.
8. Preserve structured data for future learning.
9. Validate AI output before using it operationally.
10. Build the product so real performance data can eventually replace static assumptions.
