"use client";

import { Film } from "lucide-react";
import { HistoryHub } from "@/components/history/HistoryHub";

export default function HistoryPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      <div className="flex items-center gap-3 border-b border-white/[0.08] pb-6">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-600/20 border border-violet-500/30 text-violet-400">
          <Film className="h-5 w-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Historical Clips & Runs Library</h1>
          <p className="text-xs text-zinc-400">
            Access and manage all generated vertical clips, playback previews, downloads, and pipeline execution logs.
          </p>
        </div>
      </div>

      <HistoryHub />
    </div>
  );
}
