"use client";

import { Sparkles, Zap, Smartphone, FileText, ShieldCheck, Cpu, Flame, Layers } from "lucide-react";
import { VideoUploader } from "@/components/upload/VideoUploader";
import { HistoryHub } from "@/components/history/HistoryHub";
import { BrandLogo } from "@/components/ui/BrandLogo";

export default function HomePage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8 space-y-16">
      {/* Hero Header */}
      <div className="relative text-center max-w-4xl mx-auto space-y-5 pt-4">
        {/* Glow ambient highlight */}
        <div className="absolute -top-12 left-1/2 -translate-x-1/2 w-96 h-40 bg-violet-600/15 blur-3xl pointer-events-none" />

        <div className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-violet-500/10 via-indigo-500/10 to-cyan-500/10 border border-violet-500/20 px-4 py-1 text-xs font-semibold text-violet-300 shadow-sm shadow-violet-500/10">
          <Sparkles className="h-3.5 w-3.5 text-violet-400" />
          <span>AI Short-Form Discovery & Reframing Engine</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-black tracking-tight text-white leading-[1.12]">
          Turn Long-Form Videos into{" "}
          <span className="bg-gradient-to-r from-violet-400 via-indigo-300 to-cyan-400 bg-clip-text text-transparent">
            High-Retention Shorts
          </span>
        </h1>

        <p className="text-base sm:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed font-normal">
          Autonomous discovery of high-CTR hooks, complete story context, intelligent 9:16 vertical reframing, and animated karaoke subtitle burn-in.
        </p>

        {/* Feature Pill Highlights */}
        <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-900/60 border border-white/[0.08] text-xs font-medium text-slate-300">
            <Cpu className="h-3.5 w-3.5 text-indigo-400" /> Deepgram + Faster-Whisper
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-900/60 border border-white/[0.08] text-xs font-medium text-slate-300">
            <Flame className="h-3.5 w-3.5 text-amber-400" /> Groq + Gemini AI Fallback
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-900/60 border border-white/[0.08] text-xs font-medium text-slate-300">
            <Smartphone className="h-3.5 w-3.5 text-cyan-400" /> 9:16 Blur & Face Track
          </span>
        </div>
      </div>

      {/* Video Upload & Preset Configuration Dropzone */}
      <VideoUploader />

      {/* Historical Clips & Job Execution Library */}
      <HistoryHub />

      {/* Engineering Pillars & Value Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-10 border-t border-white/[0.08]">
        <div className="glass-panel glass-panel-hover rounded-2xl p-6 space-y-3">
          <div className="h-10 w-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 shadow-sm shadow-amber-500/10">
            <Zap className="h-5 w-5" />
          </div>
          <h3 className="font-bold text-white text-base">Hook-First Candidate Discovery</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Evaluates the opening 3 seconds for curiosity, tension, and surprise. Weak openings receive substantial penalties to prioritize maximum retention.
          </p>
        </div>

        <div className="glass-panel glass-panel-hover rounded-2xl p-6 space-y-3">
          <div className="h-10 w-10 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400 shadow-sm shadow-violet-500/10">
            <Smartphone className="h-5 w-5" />
          </div>
          <h3 className="font-bold text-white text-base">Smart Vertical Reframing</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Choose between smart subject crop, 16:9 in 9:16 with customizable background blur, or native 16:9 landscape export.
          </p>
        </div>

        <div className="glass-panel glass-panel-hover rounded-2xl p-6 space-y-3">
          <div className="h-10 w-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 shadow-sm shadow-cyan-500/10">
            <FileText className="h-5 w-5" />
          </div>
          <h3 className="font-bold text-white text-base">Animated Captions & Metadata</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Generates word-level karaoke animated ASS captions with adjustable screen position, plus high-CTR platform copy for TikTok, Reels, and Shorts.
          </p>
        </div>
      </div>
    </div>
  );
}

