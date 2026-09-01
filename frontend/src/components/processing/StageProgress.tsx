"use client";

import { CheckCircle2, CircleDashed, AlertCircle, Loader2, Sparkles, Film } from "lucide-react";
import { JobStatusResponse } from "@/lib/types";

const STAGES = [
  { num: 1, name: "Validate file", desc: "Verifying container & codecs" },
  { num: 2, name: "Inspect media metadata", desc: "Extracting stream bitrates & fps" },
  { num: 3, name: "Create job", desc: "Initializing pipeline job record" },
  { num: 4, name: "Extract audio", desc: "16kHz mono WAV extraction" },
  { num: 5, name: "Transcribe audio", desc: "faster-whisper timestamped transcription" },
  { num: 6, name: "Detect scenes", desc: "PySceneDetect cut transitions" },
  { num: 7, name: "Generate transcript", desc: "Word & segment timestamp alignment" },
  { num: 8, name: "Detect candidates", desc: "AI viral hook candidate pool discovery" },
  { num: 9, name: "Expand context", desc: "Sentence snapping & filler trimming" },
  { num: 10, name: "Analyze quality", desc: "Linguistic retention & payoff scoring" },
  { num: 11, name: "Score candidates", desc: "12-dimensional composite calculation" },
  { num: 12, name: "Remove duplicates", desc: "Temporal IoU Non-Maximum Suppression" },
  { num: 13, name: "Rank globally", desc: "Ordering by composite quality" },
  { num: 14, name: "Duration constraints", desc: "Applying duration tolerance with story priority" },
  { num: 15, name: "Final boundaries", desc: "Locking precision cut timestamps" },
  { num: 16, name: "Render clips", desc: "FFmpeg 9:16 smart vertical reframing" },
  { num: 17, name: "Generate captions", desc: "Animated ASS/SRT karaoke subtitles" },
  { num: 18, name: "Generate thumbnails", desc: "Extracting hook peak keyframes" },
  { num: 19, name: "Generate metadata", desc: "TikTok, Reels, Shorts optimized copy" },
  { num: 20, name: "Store results", desc: "Persisting rendered assets" },
  { num: 21, name: "Job complete", desc: "Ready for review & export" },
];

interface StageProgressProps {
  job: JobStatusResponse;
}

export function StageProgress({ job }: StageProgressProps) {
  const currentStage = job.current_stage || 1;
  const isCompleted = job.status === "completed";
  const isFailed = job.status === "failed";

  return (
    <div className="glass-panel rounded-2xl p-6 sm:p-8 space-y-6">
      {/* Header with progress */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/[0.08] pb-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-violet-400">
              Pipeline Stage {currentStage} of 21
            </span>
            <span className="text-zinc-500">•</span>
            <span className="text-xs text-zinc-400 capitalize">
              {job.status === "processing" ? "Active" : job.status}
            </span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            {job.stage_name}
          </h2>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <span className="text-2xl sm:text-3xl font-extrabold text-white">
              {job.progress.toFixed(0)}%
            </span>
            <p className="text-[10px] text-zinc-400">Estimated progress</p>
          </div>
          <div className="h-12 w-12 rounded-full border-2 border-violet-500/20 bg-violet-500/10 flex items-center justify-center text-violet-400">
            {isCompleted ? (
              <CheckCircle2 className="h-6 w-6 text-emerald-400" />
            ) : isFailed ? (
              <AlertCircle className="h-6 w-6 text-rose-400" />
            ) : (
              <Loader2 className="h-6 w-6 animate-spin text-violet-400" />
            )}
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="h-2 w-full bg-zinc-800/80 rounded-full overflow-hidden p-0.5 border border-white/[0.04]">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              isCompleted
                ? "bg-gradient-to-r from-emerald-500 to-teal-400"
                : isFailed
                ? "bg-rose-500"
                : "bg-gradient-to-r from-violet-600 via-indigo-500 to-cyan-400"
            }`}
            style={{ width: `${Math.min(100, Math.max(4, job.progress))}%` }}
          />
        </div>
      </div>

      {/* 21 Stages Step Timeline Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-2 pt-2">
        {STAGES.map((s) => {
          const isDone = currentStage > s.num || isCompleted;
          const isCurrent = currentStage === s.num && !isCompleted && !isFailed;

          return (
            <div
              key={s.num}
              className={`rounded-xl p-2.5 border transition-all text-left ${
                isCurrent
                  ? "bg-violet-600/15 border-violet-500/80 shadow-lg shadow-violet-500/10 ring-1 ring-violet-500/50"
                  : isDone
                  ? "bg-emerald-500/[0.04] border-emerald-500/20 text-zinc-300"
                  : "bg-white/[0.01] border-white/[0.04] text-zinc-600 opacity-60"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-mono font-semibold">
                  #{s.num}
                </span>
                {isDone ? (
                  <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                ) : isCurrent ? (
                  <Loader2 className="h-3 w-3 animate-spin text-violet-400" />
                ) : (
                  <CircleDashed className="h-3 w-3 text-zinc-700" />
                )}
              </div>
              <p className="text-[11px] font-medium leading-tight truncate text-white">
                {s.name}
              </p>
              <p className="text-[9px] text-zinc-500 truncate mt-0.5">
                {s.desc}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
