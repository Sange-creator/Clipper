"use client";

import { Sparkles, Layers, CheckCircle2, Filter } from "lucide-react";
import { CandidateDetail } from "@/lib/types";

interface CandidatePoolVisualizerProps {
  candidates: CandidateDetail[];
  totalFound: number;
}

export function CandidatePoolVisualizer({ candidates, totalFound }: CandidatePoolVisualizerProps) {
  const selectedCount = candidates.filter((c) => c.selected).length;

  return (
    <div className="glass-panel rounded-2xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-violet-400" />
          <h3 className="text-sm font-semibold text-white">Candidate Pool Discovery & Ranking</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-violet-500/10 border border-violet-500/20 px-2.5 py-0.5 text-xs text-violet-300 font-medium">
            {totalFound || candidates.length} Candidate Moments Evaluated
          </span>
          <span className="rounded-full bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 text-xs text-emerald-300 font-medium">
            {selectedCount || candidates.length} Selected
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 max-h-72 overflow-y-auto p-1">
        {candidates.map((cand) => (
          <div
            key={cand.id}
            className={`rounded-xl p-3 border transition-all ${
              cand.selected
                ? "bg-violet-600/10 border-violet-500/30 text-white"
                : "bg-white/[0.02] border-white/5 text-zinc-400 opacity-60"
            }`}
          >
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="font-semibold text-violet-400">Rank #{cand.rank}</span>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-white">{cand.scores.composite_score.toFixed(0)}</span>
                <span className="text-[10px] text-zinc-500">/ 100</span>
              </div>
            </div>

            <p className="text-xs font-medium text-zinc-200 line-clamp-1 mb-1">
              {cand.hook_text || `Moment ${cand.start_time.toFixed(1)}s -> ${cand.end_time.toFixed(1)}s`}
            </p>

            <div className="flex items-center justify-between text-[10px] text-zinc-400 pt-1 border-t border-white/5">
              <span>{cand.duration.toFixed(1)}s duration</span>
              <span className="text-emerald-400 font-medium">Hook: {cand.scores.hook_score.toFixed(0)}</span>
              <span className="text-indigo-400 font-medium">Payoff: {cand.scores.payoff_score.toFixed(0)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
