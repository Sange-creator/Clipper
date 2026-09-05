# GEMINI.md — AI Video Clipper Engineering Specification

## Project Mission

Build a production-quality AI video clipping platform that accepts one or many long-form videos and automatically discovers, ranks, and renders high-potential short-form clips for TikTok, Instagram Reels, and YouTube Shorts.

The system must prioritize:

1. Strong opening hooks
2. High viewer-retention potential
3. Emotional or intellectual engagement
4. Clear story/context
5. Strong payoff
6. Quotability
7. Curiosity
8. Shareability
9. Natural clip boundaries
10. Platform compatibility
11. High-quality captions
12. Minimal unnecessary editing

Never claim that a clip is guaranteed to go viral. The system should identify clips with characteristics associated with strong short-form performance.

---

# Session Tracking & Continuity Rule

1. Always read `SESSION_TRACKER.md` at the beginning of each session.
2. Always consult the Graphify knowledge graph (`graphify-out/GRAPH_REPORT.md` or `graphify query "<question>"`) before answering architecture or codebase questions.
3. Primary Live Production Server: `https://ai-clipper-pro.vercel.app/`.
4. Always log user prompts verbatim, implementation actions, modified files, and system status into `SESSION_TRACKER.md`.
5. Always commit changes locally with clean, atomic commit messages so the user can easily revert changes if desired.
6. After modifying code files, run `graphify update .` to keep `graphify-out/` synced.

---

# Core Architecture

Use a modular architecture:

Frontend:

* Next.js
* TypeScript
* Tailwind CSS
* shadcn/ui

Backend:

* Python
* FastAPI
* Pydantic

Media:

* FFmpeg
* OpenCV
* PySceneDetect
* faster-whisper

Infrastructure:

* PostgreSQL
* Redis
* Object storage such as Cloudflare R2 or S3

AI:

* Gemini as the primary reasoning provider
* Groq and/or other supported providers as fallbacks
* Local/open-source models when practical

The frontend and backend must remain cleanly separated.

Heavy media processing must never run inside serverless frontend/API functions.

Use asynchronous background jobs for:

* transcription
* scene detection
* AI analysis
* candidate generation
* ranking
* rendering

---

# Engineering Principles

Write production-quality code.

Prioritize:

* correctness
* reliability
* modularity
* testability
* observability
* type safety
* graceful failure
* resumable processing
* idempotent jobs
* clean interfaces
* minimal coupling

Do not create giant monolithic files.

Do not duplicate business logic.

Do not hard-code API keys.

Use environment variables.

Validate all external input.

Handle provider failures gracefully.

Do not silently swallow exceptions.

Log useful diagnostic information.

---

# AI Provider Abstraction

Never tightly couple application logic to one AI provider.

Create an abstraction similar to:

AIProvider

with methods such as:

* analyze_content()
* generate_candidates()
* rank_candidates()
* generate_metadata()
* analyze_visual_context()

Implement:

* GeminiProvider
* GroqProvider
* optional fallback providers

The application should be able to switch providers through configuration.

Example:

AI_PROVIDER=gemini

Never expose API keys to the browser.

---

# Video Processing Pipeline

Every uploaded video should pass through a deterministic pipeline:

1. Validate file
2. Inspect media metadata
3. Create job
4. Extract audio
5. Transcribe using faster-whisper
6. Detect scenes
7. Generate timestamped transcript
8. Detect candidate moments
9. Expand candidate context
10. Analyze candidate quality
11. Score candidates
12. Remove duplicates/overlaps
13. Rank globally
14. Apply user duration constraints
15. Generate final clip boundaries
16. Render clips using FFmpeg
17. Generate captions
18. Generate thumbnails
19. Generate clip metadata
20. Store results
21. Mark job complete

Every stage should expose progress.

---

# Transcription

Use timestamped transcription.

Preserve:

* word timestamps when available
* segment timestamps
* speaker information when available
* confidence information when available

Never discard timing information because exact clip boundaries depend on timestamps.

Store transcripts in the database.

Do not re-transcribe the same video unless explicitly requested.

Use a content hash to detect previously processed files.

---

# Candidate Discovery

Do NOT ask the AI to immediately produce the final requested number of clips.

If the user requests N clips:

Generate substantially more candidates first.

Example:

Requested:
20

Candidate pool:
100–200

Then:

* score candidates
* eliminate weak candidates
* eliminate duplicates
* eliminate excessive overlap
* rank globally
* select the strongest N

Candidate discovery should consider:

* surprising statements
* emotional moments
* arguments
* revelations
* useful advice
* controversial opinions
* humor
* unexpected outcomes
* dramatic stories
* impressive demonstrations
* strong questions
* strong answers
* memorable quotes
* unusual facts
* moments of tension
* moments of transformation
* moments with a clear payoff

---

# Hook Analysis

The first seconds matter heavily.

Evaluate whether the beginning creates:

* curiosity
* tension
* surprise
* emotional interest
* useful information
* novelty
* conflict
* unanswered questions

Prefer clips where the viewer immediately has a reason to continue watching.

Weak openings should receive a substantial penalty.

Avoid clips that begin with:

* long greetings
* unrelated setup
* filler
* silence
* repeated statements
* excessive disclaimers
* meaningless transitions

When possible, choose a natural earlier/later boundary that improves the opening without changing the meaning.

Never manipulate a quote in a misleading way.

---

# Story Completeness

A clip must make sense without requiring the full source video.

Check:

* Is the necessary context present?
* Is the subject identifiable?
* Does the viewer understand the situation?
* Is there a progression?
* Is there a payoff or conclusion?

A shorter clip with complete context is usually preferable to a longer clip requiring external context.

---

# Context Expansion

Never assume the first detected timestamp is the final boundary.

For each candidate:

1. identify the hook
2. inspect preceding dialogue
3. locate required context
4. identify escalation
5. identify payoff
6. identify natural ending
7. determine final start/end timestamps

The resulting clip should feel intentionally edited rather than arbitrarily sliced.

---

# Scoring

Every candidate should receive normalized 0–100 scores:

* hook_score
* retention_score
* curiosity_score
* emotion_score
* story_score
* payoff_score
* shareability_score
* novelty_score
* quotability_score
* visual_score
* audio_score
* platform_score

Use a weighted composite score.

Recommended starting weights:

hook: 0.18
retention: 0.18
emotion: 0.12
story: 0.12
payoff: 0.12
curiosity: 0.10
shareability: 0.08
novelty: 0.04
quotability: 0.04
visual: 0.01
audio: 0.01

The weights may evolve after real performance data is collected.

Apply penalties for:

* missing context
* weak opening
* weak ending
* excessive silence
* repetition
* unclear speech
* poor audio
* duplicate content
* excessive overlap
* visual inactivity
* misleading framing

Never allow one score to dominate the entire evaluation.

---

# Diversity

Do not select 20 clips that are essentially the same moment.

The final selection should maximize:

* quality
* topic diversity
* emotional diversity
* narrative diversity
* source-video diversity

When multiple candidates overlap heavily, normally retain the strongest one.

Use temporal overlap detection.

---

# User Duration

The user may choose:

* 15–30 sec
* 30–45 sec
* 45–60 sec
* 60–90 sec
* custom

Treat duration as a target range, not an arbitrary hard cut.

Preserve narrative completeness.

Never remove the payoff solely to satisfy a target duration.

If necessary, choose a slightly shorter or longer duration within reasonable tolerance.

---

# Platform Optimization

Primary output:

* aspect ratio: 9:16
* target resolution: 1080x1920
* high-quality H.264
* normalized audio
* burned-in captions when enabled

The underlying clip selection should remain platform-agnostic.

Platform-specific metadata can be generated separately:

TikTok:

* title/caption optimized for TikTok
* concise hashtags

Instagram:

* caption optimized for Reels
* concise hashtags

YouTube Shorts:

* title optimized for Shorts
* description and hashtags

Never stuff irrelevant hashtags.

---

# Captions

Use transcription timestamps.

Do not hallucinate dialogue.

Captions should:

* be readable
* preserve meaning
* have sensible line breaks
* avoid covering important faces
* maintain timing
* emphasize important words only when visually appropriate

Generate subtitles in a standard subtitle format and use FFmpeg for final burn-in.

---

# Smart Vertical Reframing

For landscape source videos:

1. detect faces/subjects
2. track the primary subject
3. determine safe crop
4. dynamically reposition the crop
5. preserve important visual information

Do not blindly center-crop every video.

For multi-person conversations, intelligently switch focus when appropriate.

Do not crop subtitles, graphics, or important objects.

---

# Visual Analysis

Do not send every frame to the AI provider.

Use a hierarchical approach:

1. Local media analysis
2. Scene detection
3. Transcript candidate discovery
4. Representative frame extraction
5. AI visual analysis only for relevant candidates

Optimize API consumption aggressively.

---

# API Cost Control

Minimize external AI calls.

Cache:

* transcriptions
* scene detection
* frame descriptions
* candidate analysis
* ranking results

Never repeat an expensive operation when the input and configuration have not changed.

Use hashes/configuration fingerprints to identify cached work.

---

# Structured AI Output

AI outputs must be machine-readable JSON.

Do not rely on natural-language parsing when structured JSON is possible.

Example candidate:

{
"start": 123.4,
"end": 157.8,
"hook_score": 94,
"retention_score": 92,
"curiosity_score": 96,
"emotion_score": 83,
"story_score": 91,
"payoff_score": 95,
"shareability_score": 90,
"novelty_score": 84,
"quotability_score": 89,
"reason": "Strong curiosity hook followed by a clear payoff."
}

Validate all AI-generated JSON with Pydantic.

If parsing fails, retry using a constrained repair strategy.

Do not trust model output blindly.

---

# Job System

Long-running operations must run asynchronously.

Use Redis-backed jobs.

Jobs should have:

* id
* status
* progress
* current_stage
* created_at
* updated_at
* error
* retry_count

Possible statuses:

queued
processing
completed
failed
cancelled

Make workers idempotent.

A worker restart must not corrupt the project.

---

# Frontend UX

The user should always understand:

* upload progress
* processing progress
* current stage
* number of candidates found
* number of clips selected
* rendering progress
* failures

Show:

Video:
"Understanding source..."

Then:

"Found 137 candidate moments"

Then:

"Ranking candidates..."

Then:

"Rendering 20 clips..."

Avoid vague loading indicators for long operations.

---

# UI Guidelines & Design System

Always adhere strictly to `UI_GUIDELINES.md`:
* Use shadcn/ui primitives and clean dark-mode obsidian styling (`bg-[#07090E]`, `border-white/10`).
* Zero-Emoji Policy in UI: Never use emojis in UI controls, buttons, tabs, preset cards, or badges. Use Lucide-react SVG icons instead.
* Responsive layouts: Never cram 4 columns into half-width containers. Rich cards with titles and font badges must use 2 columns max (`grid-cols-1 sm:grid-cols-2`) so badges and text never overlap or collide.
* Component integrity: Ensure all typography badges, titles, and descriptions maintain adequate spacing and breathing room.

---

# Clip Review Interface

Users should be able to:

* preview clip
* change start
* change end
* regenerate
* reject
* favorite
* download
* export

Display the AI score and explanation.

Do not force users to accept AI boundaries blindly.

---

# Security

Never expose:

* Gemini API keys
* database credentials
* storage credentials
* Redis credentials

Validate upload:

* MIME type
* extension
* file size
* duration
* codec

Do not execute arbitrary user-provided commands.

Construct FFmpeg arguments safely.

Sanitize filenames.

---

# Reliability

For every expensive operation:

* log start
* log success
* log failure
* store job state
* support retry

External AI APIs can fail.

Storage can fail.

FFmpeg can fail.

Whisper can fail.

Assume failures will happen and design around them.

---

# Testing

Write tests for:

* transcript processing
* timestamp calculations
* candidate scoring
* overlap detection
* clip duration selection
* FFmpeg command construction
* provider fallback
* job retry behavior
* malformed AI responses
* empty transcripts
* videos without audio
* videos with multiple speakers

Prefer deterministic tests over tests that directly depend on live AI responses.

---

# Performance

Do not load entire large video files into memory unnecessarily.

Prefer streams/files on disk.

Extract audio efficiently.

Generate low-resolution proxy media when useful.

Use concurrency carefully.

Never start unlimited FFmpeg/Whisper processes.

Respect CPU, RAM, GPU, and storage limits.

---

# Code Style

TypeScript:

* strict mode
* clear interfaces
* no unnecessary any
* reusable components
* server/client boundaries respected

Python:

* type hints
* Pydantic models
* service-layer architecture
* small functions
* explicit error handling

Prefer readable code over clever code.

---

# Product Principle

The application is not primarily a video editor.

It is an:

AI-assisted content discovery and short-form optimization engine.

The highest-value feature is identifying the right moments.

Rendering is the final step.

Focus engineering effort accordingly.

---

# Future Learning System

The architecture should eventually store performance data:

* views
* watch time
* completion rate
* likes
* comments
* shares
* saves

Use historical performance to learn which candidate characteristics correlate with successful clips.

Eventually replace static scoring weights with a learned ranking model.

Do not implement this prematurely.

Build the data model so it can be added later.

---

# Default Decision Rule

When there is a conflict between:

"shorter"

and

"better story",

prefer the better story.

When there is a conflict between:

"more clips"

and

"higher quality",

prefer higher quality.

When there is a conflict between:

"AI creativity"

and

"faithful source meaning",

preserve source meaning.

The system should produce clips that feel intentionally edited, context-complete, compelling, and native to short-form platforms.
