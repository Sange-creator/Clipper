"use client";

import { Zap, Smartphone, FileText, Cpu, ShieldCheck, Layers, Activity } from "lucide-react";
import { VideoUploader } from "@/components/upload/VideoUploader";
import { HistoryHub } from "@/components/history/HistoryHub";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export default function HomePage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8 space-y-16">
      {/* Hero Header */}
      <div className="relative text-center max-w-4xl mx-auto space-y-5 pt-4">
        {/* Glow ambient highlight */}
        <div className="absolute -top-12 left-1/2 -translate-x-1/2 w-96 h-40 bg-violet-600/15 blur-3xl pointer-events-none" />

        <div className="inline-flex items-center gap-2">
          <Badge variant="outline" className="border-violet-500/30 bg-violet-500/10 text-violet-300 px-3.5 py-1 text-xs font-mono">
            <Activity className="h-3 w-3 text-violet-400" />
            <span>Deterministic Video Pipeline v3.2</span>
          </Badge>
        </div>

        <h1 className="text-4xl sm:text-6xl font-black tracking-tight text-white leading-[1.12]">
          Turn Long-Form Videos into{" "}
          <span className="bg-gradient-to-r from-violet-400 via-indigo-300 to-cyan-400 bg-clip-text text-transparent">
            High-Retention Shorts
          </span>
        </h1>

        <p className="text-base sm:text-lg text-zinc-300 max-w-2xl mx-auto leading-relaxed font-normal">
          Autonomous discovery of high-impact hooks, context-complete narrative boundaries, 9:16 smart reframing, and GPU-rendered animated subtitles.
        </p>

        {/* Feature Pill Highlights */}
        <div className="flex flex-wrap items-center justify-center gap-2.5 pt-2">
          <Badge variant="secondary" className="gap-1.5 py-1 px-3 text-xs bg-zinc-900/80 border-white/10 text-zinc-300">
            <Cpu className="h-3.5 w-3.5 text-indigo-400" /> Deepgram + Faster-Whisper
          </Badge>
          <Badge variant="secondary" className="gap-1.5 py-1 px-3 text-xs bg-zinc-900/80 border-white/10 text-zinc-300">
            <Zap className="h-3.5 w-3.5 text-amber-400" /> Multi-Tier AI Failover
          </Badge>
          <Badge variant="secondary" className="gap-1.5 py-1 px-3 text-xs bg-zinc-900/80 border-white/10 text-zinc-300">
            <Smartphone className="h-3.5 w-3.5 text-cyan-400" /> 9:16 Adaptive Canvas & Blur
          </Badge>
        </div>
      </div>

      {/* Video Upload & Preset Configuration Dropzone */}
      <VideoUploader />

      {/* Historical Clips & Job Execution Library */}
      <HistoryHub />

      {/* Engineering Pillars & Value Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-10 border-t border-white/[0.08]">
        <Card className="glass-panel glass-panel-hover border-white/10 bg-zinc-950/60 p-2 space-y-2">
          <CardHeader>
            <div className="h-10 w-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 mb-2">
              <Zap className="h-5 w-5" />
            </div>
            <CardTitle className="text-base font-bold text-white">Hook-First Candidate Discovery</CardTitle>
            <CardDescription className="text-xs text-zinc-400 leading-relaxed">
              Evaluates the opening seconds for tension, curiosity, and psychological engagement. Applies non-maximum suppression to eliminate narrative redundancy.
            </CardDescription>
          </CardHeader>
        </Card>

        <Card className="glass-panel glass-panel-hover border-white/10 bg-zinc-950/60 p-2 space-y-2">
          <CardHeader>
            <div className="h-10 w-10 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400 mb-2">
              <Smartphone className="h-5 w-5" />
            </div>
            <CardTitle className="text-base font-bold text-white">Adaptive Vertical Reframing</CardTitle>
            <CardDescription className="text-xs text-zinc-400 leading-relaxed">
              Dynamic focal tracking, 16:9 within 9:16 with frosted glass Gaussian blur, or native 16:9 landscape rendering without distorting source framing.
            </CardDescription>
          </CardHeader>
        </Card>

        <Card className="glass-panel glass-panel-hover border-white/10 bg-zinc-950/60 p-2 space-y-2">
          <CardHeader>
            <div className="h-10 w-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 mb-2">
              <FileText className="h-5 w-5" />
            </div>
            <CardTitle className="text-base font-bold text-white">Kinetic Captions & Copy</CardTitle>
            <CardDescription className="text-xs text-zinc-400 leading-relaxed">
              Word-level aligned animated ASS subtitles with customizable vertical baseline, accompanied by platform-specific titles and hashtags.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    </div>
  );
}
