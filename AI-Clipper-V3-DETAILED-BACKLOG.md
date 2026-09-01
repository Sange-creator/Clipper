# AI Clipper — V3 Detailed Backlog

## V3 Goal

V3 supports exactly **two clipping modes**:

1. **Regular Podcast Clipper** — optimized for podcasts, interviews, and conversations.
2. **Long Video Viral Moment Clipper** — analyzes long videos, finds the strongest standalone moments, aggressively removes dead air/filler, and renders short-form clips.

### Explicit V3 constraint
**No face tracking. No automatic speaker framing. No AI B-roll. No generative video. No artificial alteration of source meaning.**

V3 does not guarantee virality. It optimizes for **viral potential** using hook strength, curiosity, retention potential, emotional intensity, novelty, payoff, shareability, quotability, and standalone completeness.

---

# Product Scope

## In Scope

- Multi-video upload
- Podcast clipping mode
- Long-video viral-moment mode
- Media inspection
- Local timestamped transcription
- Silence/dead-air detection
- Filler/false-start detection
- Scene detection
- AI candidate discovery
- AI scoring and ranking
- Context expansion
- Clip-boundary optimization
- Duplicate/overlap removal
- User-selected clip count
- User-selected duration range
- Dead-air/filler edit timeline
- FFmpeg rendering
- 9:16 output
- Captions
- Clip preview
- Clip regeneration
- Manual start/end adjustment
- Batch processing
- Progress tracking
- Retry handling
- Download/export

## Explicitly Out of Scope

- Face tracking
- Subject tracking
- Automatic speaker/camera framing
- Dynamic camera switching
- AI-generated B-roll
- Generative video
- Automatic social publishing
- Social performance learning
- Advanced timeline editor
- Multi-camera editing
- Voice cloning
- Lip-sync modification
- Heavy visual effects

---

# Core User Flow

```text
UPLOAD VIDEOS
      ↓
CHOOSE MODE
      ↓
CHOOSE CLIP COUNT
      ↓
CHOOSE DURATION RANGE
      ↓
START GENERATION
      ↓
MEDIA ANALYSIS
      ↓
TRANSCRIPTION
      ↓
SILENCE / FILLER / SCENE ANALYSIS
      ↓
CANDIDATE DISCOVERY
      ↓
AI ANALYSIS + VIRAL SCORING
      ↓
CONTEXT EXPANSION
      ↓
DEAD-AIR / FILLER EDITING
      ↓
DUPLICATE + OVERLAP REMOVAL
      ↓
GLOBAL RANKING
      ↓
TOP-N SELECTION
      ↓
FFMPEG RENDER
      ↓
CAPTIONS
      ↓
RESULTS GRID
```

---

# 1. Project Creation

## V3-001 — Project Model

Create a project entity with:

```text
id
name
mode
status
settings
created_at
updated_at
```

Supported modes:

```text
podcast
viral_moments
```

Acceptance criteria:

- Project persists in PostgreSQL.
- Selected mode persists.
- Project settings persist.
- Processing can resume after restart.

Priority: **P0**

---

# 2. Multi-Video Upload

## V3-002 — Video Ingestion

Support uploading one or many long videos.

Store:

```text
original_filename
storage_path
mime_type
size
sha256_hash
duration
width
height
fps
codec
audio_present
```

Acceptance criteria:

- Invalid media is rejected.
- Duplicate files can be detected by hash.
- Multiple videos can belong to one project.
- Large uploads do not require loading the entire file into browser memory.

Priority: **P0**

---

# 3. Media Inspection

## V3-003 — FFprobe/FFmpeg Inspection

Extract media metadata before AI processing.

Acceptance criteria:

- Duration available.
- Resolution available.
- Frame rate available.
- Audio presence available.
- Unsupported codecs are surfaced clearly.

Priority: **P0**

---

# 4. Audio Extraction

## V3-004 — Audio Extraction

Use FFmpeg to produce an analysis-friendly audio file.

Acceptance criteria:

- Standardized audio can be passed to Whisper.
- Videos without audio fail gracefully.
- Audio extraction is cached.

Priority: **P0**

---

# 5. Transcription

## V3-005 — faster-whisper

Use local `faster-whisper` for timestamped transcription.

Store:

```text
segments
words (when enabled)
start
end
text
confidence (when available)
language
```

Acceptance criteria:

- Transcript persists.
- Word/segment timestamps remain available.
- Completed transcription is not repeated unnecessarily.
- Empty or failed transcripts are handled safely.

Priority: **P0**

---

# 6. Silence / Dead-Air Detection

## V3-006 — Silence Detector

Detect silence regions independently from transcript analysis.

Store:

```text
start
end
duration
decibel_threshold
```

Initial heuristic defaults:

```text
< 0.45s     normally preserve
0.45–1.2s   evaluate context
1.2–2.0s    possible compression
> 2.0s      strong dead-air candidate
```

These are starting heuristics, not hard rules.

Acceptance criteria:

- Silence intervals are persisted.
- Threshold is configurable.
- Silence regions can be consumed by the clip-editing engine.

Priority: **P0**

---

# 7. Filler and False-Start Detection

## V3-007 — Filler Analyzer

Identify:

- uh/um
- filler use of “like”
- repeated words
- false starts
- abandoned sentences
- repeated explanations
- unnecessary greetings
- unnecessary transitions

The system must distinguish filler from meaningful speech.

Acceptance criteria:

- Proposed filler segments have timestamps.
- Filler suggestions can be accepted/rejected by the editor.
- Source meaning is preserved.

Priority: **P0**

---

# 8. Scene Detection

## V3-008 — Scene Segmentation

Use PySceneDetect or an equivalent local algorithm.

Store:

```text
scene_id
start
end
```

Scene detection is supporting intelligence; it must not override transcript-based storytelling boundaries.

Priority: **P1**

---

# 9. Mode A — Regular Podcast Clipper

## V3-009 — Podcast Candidate Discovery

Find high-value podcast/conversation moments:

- surprising statements
- strong opinions
- controversial takes
- emotional stories
- funny moments
- arguments/debates
- useful advice
- revelations
- memorable quotes
- strong answers
- strong questions
- hard truths
- narrative payoffs

Avoid:

- greetings
- introductions
- sponsor sections
- repetitive context
- rambling
- weak conclusions
- dead air

Priority: **P0**

---

# 10. Mode B — Long Video Viral Moment Clipper

## V3-010 — Long Video Candidate Discovery

Do not assume the content is a podcast.

Support discovery from:

- documentaries
- interviews
- commentary
- livestreams
- educational videos
- tutorials
- speeches
- reactions
- storytelling
- news-style content
- recorded events
- general long-form video

Look for:

- surprising events
- revelations
- emotional peaks
- dramatic statements
- unusual facts
- shocking information
- conflict
- tension
- transformation
- demonstrations
- discoveries
- funny incidents
- highly useful information
- strong conclusions
- compelling story beats
- high-curiosity moments
- self-contained moments

Priority: **P0**

---

# 11. Candidate Pool Strategy

## V3-011 — Oversample Candidates

Never ask the model for only the final requested number.

Example:

```text
User requests 20 clips
        ↓
Generate 100–200 candidates
        ↓
Analyze
        ↓
Score
        ↓
Deduplicate
        ↓
Rank
        ↓
Return best 20
```

Candidate pool should scale with source duration.

Suggested starting ranges:

```text
Short source       50–100
Medium source      100–150
Long source        150–300
```

Cap candidate generation to avoid runaway API usage.

Priority: **P0**

---

# 12. Context Expansion

## V3-012 — Standalone Moment Builder

A candidate timestamp is not necessarily a final clip.

For every candidate determine:

```text
hook_start
context_start
content_start
payoff_start
natural_end
```

Then derive:

```text
final_start
final_end
```

Example:

```text
AI discovers:
12:31–12:47

Context requires:
12:24

Payoff ends:
12:53

Final:
12:24–12:53
```

Acceptance criteria:

- Clip does not begin mid-sentence unless the cut is naturally acceptable.
- Viewer can understand what is happening.
- Payoff remains present.
- Unnecessary lead-in/outro is removed.

Priority: **P0**

---

# 13. Viral Scoring Engine

## V3-013 — Candidate Score Schema

Every candidate receives 0–100 scores:

```text
hook_score
retention_score
curiosity_score
emotion_score
novelty_score
story_score
payoff_score
shareability_score
quotability_score
rewatch_score
visual_score
audio_score
standalone_score
platform_score
```

Priority: **P0**

---

# 14. Initial Score Weights

## V3-014 — Weighted Ranking

Starting point:

```text
hook              0.16
retention         0.15
curiosity         0.12
story             0.10
payoff            0.10
emotion           0.08
shareability      0.08
standalone        0.07
novelty           0.05
quotability       0.04
rewatch           0.03
visual            0.01
audio             0.01
```

Weights must be configurable.

Add penalties for:

- weak opening
- weak ending
- missing context
- long dead air
- excessive filler
- repetition
- poor audio
- unintelligible speech
- misleading framing
- duplicate content
- excessive overlap

Priority: **P0**

---

# 15. AI Candidate Analysis

## V3-015 — Gemini Analysis

Use Gemini for reasoning over candidate transcript/context and selected representative visual information when useful.

Do not send every frame of a long video to the model.

AI output must be structured JSON.

Validate with Pydantic.

Retry malformed responses safely.

Cache successful analysis.

Priority: **P0**

---

# 16. Duration Engine

## V3-016 — User Duration Selection

Presets:

```text
15–30 sec
30–45 sec
45–60 sec
60–90 sec
```

Also support custom:

```text
minimum
preferred target
maximum
```

Duration is a target range, not a reason to destroy narrative completeness.

Example:

A 37-second complete story should beat an arbitrary 30-second crop that cuts off the payoff.

Priority: **P0**

---

# 17. Boundary Optimization

## V3-017 — Smart Start/End Selection

Use:

- transcript timestamps
- sentence boundaries
- silence intervals
- filler candidates
- candidate context
- payoff position
- user duration range

Acceptance criteria:

- No mid-word cuts.
- Strong hook preserved.
- Payoff preserved.
- Duration target respected when possible.
- Clip remains coherent.

Priority: **P0**

---

# 18. Dead-Air Editing

## V3-018 — Timeline-Based Silence Removal

Represent kept intervals explicitly:

```json
{
  "source_start": 100.2,
  "source_end": 145.7,
  "keep": [
    [100.2, 112.4],
    [113.1, 129.8],
    [131.6, 145.7]
  ]
}
```

FFmpeg then renders the assembled timeline.

Rules:

- Remove genuine dead air.
- Preserve short natural pauses.
- Avoid robotic pacing.
- Maintain audio/video sync.

Priority: **P0**

---

# 19. Filler Editing

## V3-019 — Safe Filler Cuts

Use proposed filler regions to create edit points.

A filler cut must be rejected when it would:

- change meaning
- remove a key word
- break sentence continuity
- create unnatural audio
- make the speaker difficult to understand

Priority: **P0**

---

# 20. Duplicate / Overlap Removal

## V3-020 — Candidate Deduplication

Detect duplicate moments using:

- temporal overlap
- transcript similarity
- optional semantic similarity

If two clips represent the same moment, preserve the stronger candidate.

Priority: **P0**

---

# 21. Global Ranking

## V3-021 — Cross-Video Ranking

When multiple source videos are uploaded:

1. Analyze each source.
2. Build a shared candidate pool.
3. Score all candidates consistently.
4. Remove duplicates.
5. Rank globally.
6. Select final N.

Do not automatically pick equal numbers from each source.

Priority: **P0**

---

# 22. Diversity Strategy

## V3-022 — Source / Topic Diversity

Support:

```text
quality_first
balanced_sources
maximum_diversity
```

Default:

```text
balanced_sources
```

Diversity should never override a massive quality difference.

Priority: **P1**

---

# 23. Final N Selection

## V3-023 — Top-N Selector

Inputs:

```text
candidate_pool
requested_clip_count
duration_range
diversity_strategy
```

Output:

```text
final_selected_candidates
```

Acceptance criteria:

- Return N when enough valid candidates exist.
- Return fewer when quality candidates are insufficient.
- Explain when fewer than requested are returned.

Priority: **P0**

---

# 24. Vertical Render

## V3-024 — 9:16 FFmpeg Output

Default master output:

```text
1080x1920
9:16
H.264
AAC
high quality
```

Preserve source FPS where practical.

Normalize audio.

No face tracking.

No intelligent subject tracking.

Default landscape handling:

```text
inspect dimensions
↓
calculate 9:16 crop
↓
center crop
↓
preserve useful image area
```

Priority: **P0**

---

# 25. Caption System

## V3-025 — Accurate Captions

Generate captions from the Whisper transcript.

Styles:

```text
Clean
Bold
Minimal
High Contrast
```

Requirements:

- accurate words
- accurate timing
- readable line length
- sensible grouping
- safe placement
- no hallucination

Priority: **P0**

---

# 26. Caption Sync After Cuts

## V3-026 — Edited-Timeline Subtitle Mapping

When silence/filler cuts occur, subtitle timestamps must be remapped to the final timeline.

Acceptance criteria:

- Captions remain synchronized after arbitrary cuts.
- Removed transcript segments do not appear in final captions.
- No caption appears during removed dead air.

Priority: **P0**

---

# 27. Thumbnail Generation

## V3-027 — Thumbnail Frame Selection

Choose representative frames that are:

- visually interesting
- clear
- not black
- not transitional
- representative of the clip

Text overlays can remain optional.

Priority: **P1**

---

# 28. Clip Metadata

## V3-028 — Structured Clip Record

Store:

```json
{
  "clip_id": "...",
  "source_video_id": "...",
  "mode": "podcast",
  "source_start": 123.4,
  "source_end": 158.8,
  "output_duration": 35.4,
  "viral_score": 94.2,
  "hook_score": 97,
  "retention_score": 93,
  "curiosity_score": 95,
  "emotion_score": 84,
  "story_score": 91,
  "payoff_score": 96,
  "standalone_score": 94,
  "title": "...",
  "caption": "...",
  "reason": "...",
  "render_status": "completed"
}
```

Priority: **P0**

---

# 29. Background Job System

## V3-029 — Redis Worker Pipeline

Jobs:

```text
inspect
extract_audio
transcribe
detect_silence
detect_scenes
discover_candidates
analyze_candidates
score_candidates
optimize_boundaries
remove_duplicates
select_top_n
render_clips
generate_captions
generate_thumbnails
```

Job fields:

```text
id
project_id
video_id
stage
status
progress
retry_count
error
created_at
updated_at
```

Statuses:

```text
queued
processing
completed
failed
cancelled
```

Priority: **P0**

---

# 30. API Provider Abstraction

## V3-030 — AI Provider Interface

Use an abstraction such as:

```text
AIProvider
├── GeminiProvider
├── GroqProvider
└── OptionalFallbackProvider
```

Methods may include:

```text
analyze_content()
generate_candidates()
rank_candidates()
generate_metadata()
```

API keys are server-side only.

Priority: **P0**

---

# 31. AI Prompt Architecture

Create separate prompts:

```text
prompts/
├── podcast/
│   ├── candidate-discovery.md
│   ├── candidate-analysis.md
│   ├── boundary-optimization.md
│   └── metadata.md
│
├── viral-moments/
│   ├── candidate-discovery.md
│   ├── candidate-analysis.md
│   ├── boundary-optimization.md
│   └── metadata.md
│
└── shared/
    ├── scoring.md
    ├── deduplication.md
    └── output-schema.md
```

Do not use one giant prompt for all stages.

Priority: **P0**

---

# 32. Structured AI Schema

Example:

```json
{
  "candidates": [
    {
      "start": 123.4,
      "end": 158.6,
      "hook_start": 123.4,
      "payoff_start": 151.3,
      "natural_end": 158.6,
      "hook_score": 96,
      "retention_score": 92,
      "curiosity_score": 95,
      "emotion_score": 84,
      "novelty_score": 90,
      "story_score": 91,
      "payoff_score": 95,
      "shareability_score": 88,
      "quotability_score": 91,
      "standalone_score": 94,
      "reason": "Strong curiosity hook followed by a clear payoff."
    }
  ]
}
```

Validate all AI output with Pydantic.

Do not rely on natural-language parsing when structured JSON is possible.

Priority: **P0**

---

# 33. Processing Cost Control

## V3-031 — AI Usage Optimization

Do not send every video frame to the AI provider.

Use hierarchical processing:

```text
Local media analysis
↓
Transcript
↓
Scene/candidate identification
↓
Representative frames only when useful
↓
AI analysis on candidates
```

Cache:

- transcripts
- scene detection
- silence detection
- candidate analysis
- ranking

Priority: **P0**

---

# 34. Processing Cache

## V3-032 — Deterministic Cache Keys

Cache key should incorporate:

```text
video_hash
processing_version
model_version
prompt_version
settings_hash
```

Changing relevant logic must invalidate stale results.

Priority: **P1**

---

# 35. Results UI

## V3-033 — Results Grid

Each clip card displays:

- thumbnail
- title
- duration
- viral score
- source video
- source timestamp
- preview
- download
- regenerate
- reject
- favorite

Priority: **P0**

---

# 36. Clip Review

## V3-034 — Clip Detail View

Show:

- final video
- transcript
- source range
- score breakdown
- AI explanation
- edit timeline
- final duration

Actions:

```text
Regenerate
Adjust Start
Adjust End
Re-render
Download
```

Priority: **P1**

---

# 37. Manual Boundary Adjustment

## V3-035 — Start/End Editing

Allow user to adjust:

```text
start
end
```

Re-render without repeating AI discovery.

Priority: **P1**

---

# 38. Regenerate Clip

## V3-036 — Regeneration

Allow:

> Regenerate this clip

The system should reconsider:

- start
- end
- context
- dead air
- filler
- alternate nearby moment

Reuse existing transcript and analysis when possible.

Priority: **P1**

---

# 39. Processing Dashboard

## V3-037 — Progress UI

Display:

```text
Uploading
Analyzing media
Transcribing
Finding moments
Scoring candidates
Selecting clips
Rendering
Completed
```

Also show:

- videos processed
- candidate count
- selected clip count
- failed jobs
- current stage

Priority: **P0**

---

# 40. Error Handling

## V3-038 — Resilient Pipeline

Handle:

- AI API failures
- rate limits
- malformed JSON
- FFmpeg failure
- Whisper failure
- corrupted videos
- missing audio
- insufficient storage
- worker restarts

Every failure must be visible and retryable where safe.

Priority: **P0**

---

# 41. Idempotency

## V3-039 — Safe Retry Architecture

Every worker task should be safe to retry.

A worker restart must not:

- duplicate clips
- overwrite valid outputs incorrectly
- restart all analysis unnecessarily
- corrupt the project state

Priority: **P0**

---

# 42. Export Package

## V3-040 — Download Results

Single clip download:

```text
clip.mp4
```

Complete clip package:

```text
clip.mp4
thumbnail.jpg
captions.srt
metadata.json
```

Batch option:

```text
all-clips.zip
```

Priority: **P1**

---

# 43. AI Title and Caption Metadata

## V3-041 — Metadata Generation

Generate:

- clip title
- short social caption
- relevant hashtags

Titles must be:

- accurate
- concise
- curiosity-driven
- non-misleading

Do not use spammy hashtag lists.

Priority: **P1**

---

# 44. Testing Dataset

## V3-042 — Quality Test Set

Test at minimum:

- 10 podcasts
- 10 interviews
- 10 documentaries
- 10 commentary videos
- 10 educational/lecture videos
- 10 livestream-style videos

For each source inspect:

- candidate quality
- hook quality
- context completeness
- payoff preservation
- dead-air removal
- filler removal
- caption synchronization
- duplicate handling
- duration compliance
- output quality

Priority: **P0**

---

# 45. Quality Rules

## V3-043 — Human QA Checklist

A generated clip should fail QA when:

- viewer needs unexplained source context
- hook is weak
- payoff is missing
- sentence begins/ends unnaturally
- dead air remains unnecessarily
- aggressive cuts create robotic speech
- captions are wrong
- captions are out of sync
- duplicate clip already exists
- output has audio/video sync problems

Priority: **P0**

---

# 46. Metrics

## V3-044 — Internal Quality Metrics

Track:

### Selection

- keep rate
- reject rate
- favorite rate
- quality score

### Editing

- manual boundary adjustment rate
- regeneration rate
- caption error rate
- render failure rate

### Performance

- processing time per source minute
- transcription time
- AI calls per source hour
- cache hit rate
- worker failure rate

Do not call these guaranteed viral metrics.

Priority: **P1**

---

# 47. Definition of Done

V3 is complete when a user can:

1. Create a project.
2. Upload one or multiple long videos.
3. Choose **Podcast** or **Viral Moments**.
4. Choose number of clips.
5. Choose a duration range.
6. Start generation.
7. See processing progress.
8. Receive ranked clips.
9. Preview clips.
10. See source timestamps.
11. See viral score and reasons.
12. Automatically remove dead air/filler where appropriate.
13. Receive 9:16 clips.
14. Receive synchronized captions.
15. Regenerate a clip.
16. Adjust boundaries.
17. Re-render without re-analyzing the source.
18. Download individual or batch results.

---

# Recommended V3 Build Order

## Sprint 1 — Foundation

- V3-001 Project model
- V3-002 Multi-video upload
- V3-003 Media inspection
- V3-029 Job system
- V3-030 AI provider abstraction

## Sprint 2 — Media Intelligence

- V3-004 Audio extraction
- V3-005 faster-whisper
- V3-006 Silence detector
- V3-007 Filler detection
- V3-008 Scene detection

## Sprint 3 — Podcast Mode

- V3-009 Podcast candidate discovery
- V3-012 Context expansion
- V3-013/V3-014 Viral scoring
- V3-017 Boundary optimization
- V3-023 Top-N selection

## Sprint 4 — Long Video Viral Moments

- V3-010 Long-video candidate discovery
- V3-011 Candidate oversampling
- V3-015 Gemini analysis
- V3-020 Duplicate removal
- V3-021 Global ranking
- V3-022 Diversity

## Sprint 5 — Editing + Rendering

- V3-018 Dead-air editing
- V3-019 Filler editing
- V3-024 FFmpeg 9:16 render
- V3-025 Captions
- V3-026 Caption timeline remapping
- V3-027 Thumbnails

## Sprint 6 — Product UX

- V3-033 Results grid
- V3-034 Clip review
- V3-035 Boundary adjustment
- V3-036 Regeneration
- V3-037 Progress dashboard
- V3-040 Export

## Sprint 7 — Hardening

- V3-031 Cost optimization
- V3-032 Cache
- V3-038 Error handling
- V3-039 Idempotency
- V3-042 Test dataset
- V3-043 Quality QA
- V3-044 Metrics

---

# Recommended Technical Architecture

```text
                         ┌──────────────────────┐
                         │       Next.js        │
                         │       Web App        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │       FastAPI        │
                         │         API          │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼──────────────────────┐
              │                     │                      │
              ▼                     ▼                      ▼
        PostgreSQL               Redis              Object Storage
                                                   R2 / S3 / Local
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Background Worker  │
                         └──────────┬───────────┘
                                    │
             ┌──────────────────────┼───────────────────────┐
             │                      │                       │
             ▼                      ▼                       ▼
      faster-whisper             FFmpeg             PySceneDetect
             │                      │                       │
             └──────────────────────┼───────────────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    AI Orchestrator   │
                         └──────────┬───────────┘
                                    │
                         ┌──────────┴──────────┐
                         │                     │
                         ▼                     ▼
                    Gemini API          Fallback Provider
```

---

# Final V3 Product Principle

V3 is a **viral-moment discovery and editing engine**, not a generic video editor.

The central loop is:

```text
UNDERSTAND THE LONG VIDEO
        ↓
FIND MOMENTS WORTH WATCHING
        ↓
FIND THE SMALLEST COMPLETE STORY
        ↓
REMOVE DEAD WEIGHT
        ↓
PRESERVE SOURCE MEANING
        ↓
RANK THE STRONGEST MOMENTS
        ↓
RENDER CLEAN SHORT-FORM CLIPS
```

For V3, keep the editing intelligence focused.

**No face tracking.**

**No complex subject framing.**

**No AI B-roll.**

**No unnecessary effects.**

Make the system exceptionally good at:

> **Finding the strongest moments inside long videos, cutting away dead space and filler, preserving the meaning, and producing short clips with high viral potential.**
