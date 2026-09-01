"use client";

import { Film } from "lucide-react";
import { HistoryHub } from "@/components/history/HistoryHub";

export default function HistoryPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      <div className="flex items-center gap-4 border-b border-white/[0.08] pb-6">
        <div className="relative flex-shrink-0">
          <div className="absolute -inset-1 rounded-xl bg-gradient-to-r from-violet-600 to-cyan-500 opacity-40 blur" />
          <div className="relative h-12 w-12 rounded-xl bg-[#0f1222] border border-violet-500/30 p-1.5 shadow-lg">
            <img src="/logo.svg" alt="Clipper Pro" className="w-full h-full" />
          </div>
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Historical Clips & Runs Library</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Access and manage all generated vertical clips, playback previews, downloads, and pipeline execution logs.
          </p>
        </div>
      </div>

      <HistoryHub />
    </div>
  );
}

