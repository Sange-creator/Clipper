"use client";

import {
  Award,
  Zap,
  HelpCircle,
  Heart,
  BookOpen,
  Gift,
  Share2,
  Sparkles,
  Quote,
  Video,
  Volume2,
  CheckCircle2,
  Repeat,
} from "lucide-react";
import { CandidateScores } from "@/lib/types";

interface ScoreRadarProps {
  scores: CandidateScores;
  reason?: string | null;
}

export function ScoreRadar({ scores, reason }: ScoreRadarProps) {
  const metrics = [
    { label: "Hook Intensity", value: scores.hook_score, icon: Zap, color: "from-amber-500 to-orange-500", weight: "16%" },
    { label: "Retention Potential", value: scores.retention_score, icon: Award, color: "from-violet-500 to-indigo-500", weight: "15%" },
    { label: "Curiosity Tension", value: scores.curiosity_score, icon: HelpCircle, color: "from-cyan-500 to-blue-500", weight: "12%" },
    { label: "Story Arc", value: scores.story_score, icon: BookOpen, color: "from-emerald-500 to-teal-500", weight: "10%" },
    { label: "Payoff & Resolution", value: scores.payoff_score, icon: Gift, color: "from-purple-500 to-fuchsia-500", weight: "10%" },
    { label: "Emotional Impact", value: scores.emotion_score, icon: Heart, color: "from-rose-500 to-pink-500", weight: "8%" },
    { label: "Shareability", value: scores.shareability_score, icon: Share2, color: "from-sky-500 to-indigo-500", weight: "8%" },
    { label: "Standalone Context", value: scores.standalone_score ?? 85.0, icon: CheckCircle2, color: "from-teal-500 to-emerald-500", weight: "7%" },
    { label: "Novelty & Insight", value: scores.novelty_score, icon: Sparkles, color: "from-yellow-500 to-amber-500", weight: "5%" },
    { label: "Quotability", value: scores.quotability_score, icon: Quote, color: "from-red-500 to-orange-500", weight: "4%" },
    { label: "Rewatchability", value: scores.rewatch_score ?? 78.0, icon: Repeat, color: "from-indigo-500 to-purple-500", weight: "3%" },
    { label: "Audio & Speech Flow", value: scores.audio_score, icon: Volume2, color: "from-teal-500 to-emerald-500", weight: "1%" },
  ];

  return (
    <div className="glass-panel rounded-2xl p-6 space-y-6">
      {/* Composite Score Header */}
      <div className="flex items-center justify-between border-b border-white/[0.08] pb-4">
        <div>
          <h3 className="text-sm font-semibold text-white">V3 Viral Intelligence Scoring</h3>
          <p className="text-xs text-zinc-400">12-factor multi-dimensional composite viral evaluation</p>
        </div>
        <div className="flex items-center gap-2 rounded-2xl bg-gradient-to-r from-violet-600/20 to-indigo-600/20 border border-violet-500/30 px-4 py-2">
          <Sparkles className="h-4 w-4 text-violet-400" />
          <div>
            <span className="text-xl font-extrabold text-white">
              {scores.composite_score.toFixed(0)}
            </span>
            <span className="text-[10px] text-zinc-400"> / 100</span>
          </div>
        </div>
      </div>

      {/* AI Explanation Rationale */}
      {reason && (
        <div className="rounded-xl bg-violet-500/[0.06] border border-violet-500/20 p-3.5 text-xs text-zinc-300 leading-relaxed">
          <strong className="text-violet-300 block mb-1">AI Curatorial Assessment:</strong>
          {reason}
        </div>
      )}

      {/* 12 Metric Progress Bars Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
        {metrics.map((m) => {
          const Icon = m.icon;
          return (
            <div key={m.label} className="space-y-1.5 rounded-xl bg-black/20 p-3 border border-white/[0.04]">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 text-zinc-300">
                  <Icon className="h-3.5 w-3.5 text-violet-400" />
                  <span>{m.label}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] text-zinc-500">wt: {m.weight}</span>
                  <span className="font-mono font-bold text-white">{m.value.toFixed(0)}</span>
                </div>
              </div>

              <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full bg-gradient-to-r ${m.color}`}
                  style={{ width: `${Math.min(100, Math.max(5, m.value))}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
