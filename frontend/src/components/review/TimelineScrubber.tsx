"use client";

import { useState } from "react";
import { Scissors, RefreshCw, Sparkles, Sliders, Subtitles, Check, Smartphone, Maximize2, Monitor, Flame, Eraser, Wand2, Zap, FileText, MessageSquare, Clock, BookOpen } from "lucide-react";

import { formatSeconds } from "@/lib/utils";

interface TimelineScrubberProps {
  initialStart: number;
  initialEnd: number;
  maxVideoDuration: number;
  initialFramingMode?: string;
  initialBlurRadius?: number;
  initialSubtitlePosition?: number;
  initialAddHookHeader?: boolean;
  initialHookHeaderPosition?: number;
  initialHookHeaderStyle?: string;
  initialHookHeaderText?: string | null;
  initialRemoveWatermark?: boolean;
  initialWatermarkPosition?: "top_right" | "bottom_right" | "top_left" | "bottom_left" | string;
  initialEnhanceQuality?: boolean;
  initialCaptionStyle?: string;
  initialBurnCaptions?: boolean;
  onRerender: (
    start: number,
    end: number,
    framingMode?: string,
    blurRadius?: number,
    subtitlePosition?: number,
    addHookHeader?: boolean,
    hookHeaderPosition?: number,
    hookHeaderText?: string,
    removeWatermark?: boolean,
    watermarkPosition?: string,
    enhanceQuality?: boolean,
    hookHeaderStyle?: string,
    captionStyle?: string,
    burnCaptions?: boolean
  ) => Promise<void>;
}

export function TimelineScrubber({
  initialStart,
  initialEnd,
  maxVideoDuration,
  initialFramingMode = "crop_9_16",
  initialBlurRadius = 30,
  initialSubtitlePosition = 75,
  initialAddHookHeader = false,
  initialHookHeaderPosition = 12,
  initialHookHeaderStyle = "viral_creator",
  initialHookHeaderText = "",
  initialRemoveWatermark = false,
  initialWatermarkPosition = "top_right",
  initialEnhanceQuality = true,
  initialCaptionStyle = "tiktok_viral",
  initialBurnCaptions = true,
  onRerender,
}: TimelineScrubberProps) {
  const [startTime, setStartTime] = useState(initialStart);
  const [endTime, setEndTime] = useState(initialEnd);
  const [framingMode, setFramingMode] = useState<"crop_9_16" | "blur_fit_9_16" | "original_16_9">(
    (initialFramingMode as any) || "crop_9_16"
  );
  const [blurRadius, setBlurRadius] = useState<number>(initialBlurRadius || 30);
  const [subtitlePosition, setSubtitlePosition] = useState<number>(initialSubtitlePosition || 75);
  const [captionStyle, setCaptionStyle] = useState<string>(initialCaptionStyle || "tiktok_viral");
  const [burnCaptions, setBurnCaptions] = useState<boolean>(initialBurnCaptions !== false);
  const [addHookHeader, setAddHookHeader] = useState<boolean>(initialAddHookHeader || false);
  const [hookHeaderPosition, setHookHeaderPosition] = useState<number>(initialHookHeaderPosition || 12);
  const [hookHeaderStyle, setHookHeaderStyle] = useState<string>(initialHookHeaderStyle || "viral_creator");
  const [hookHeaderText, setHookHeaderText] = useState<string>(initialHookHeaderText || "");
  const [removeWatermark, setRemoveWatermark] = useState<boolean>(initialRemoveWatermark || false);
  const [watermarkPosition, setWatermarkPosition] = useState<"top_right" | "bottom_right" | "top_left" | "bottom_left">(
    (initialWatermarkPosition as any) || "top_right"
  );
  const [enhanceQuality, setEnhanceQuality] = useState<boolean>(initialEnhanceQuality !== false);
  const [isRendering, setIsRendering] = useState(false);
  const [justSaved, setJustSaved] = useState(false);

  // Playhead preview time
  const [previewTime, setPreviewTime] = useState<number | null>(null);

  const duration = Math.max(0, endTime - startTime);

  const handleStartChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = Number(e.target.value);
    if (val < endTime - 3) {
      setStartTime(val);
      setJustSaved(false);
    }
  };

  const handleEndChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = Number(e.target.value);
    if (val > startTime + 3) {
      setEndTime(val);
      setJustSaved(false);
    }
  };

  const handleTriggerRerender = async () => {
    setIsRendering(true);
    try {
      await onRerender(
        startTime,
        endTime,
        framingMode,
        blurRadius,
        subtitlePosition,
        addHookHeader,
        hookHeaderPosition,
        hookHeaderText.trim() || undefined,
        removeWatermark,
        watermarkPosition,
        enhanceQuality,
        hookHeaderStyle,
        captionStyle,
        burnCaptions
      );
      setJustSaved(true);
    } finally {
      setIsRendering(false);
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Scissors className="h-4 w-4 text-violet-400" />
            <h3 className="text-sm font-semibold text-white">Interactive Boundary & Layout Workstation</h3>
          </div>
          <p className="text-xs text-zinc-400">
            Adjust timestamps, aspect ratio framing, and subtitle screen position, then re-render instantly.
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="rounded-xl bg-white/[0.03] border border-white/10 px-4 py-2 text-center">
            <span className="text-xs text-zinc-400 block">Clip Duration</span>
            <span className="text-sm font-bold text-white font-mono">
              {duration.toFixed(1)}s
            </span>
          </div>

          <button
            onClick={handleTriggerRerender}
            disabled={isRendering}
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 px-5 py-2.5 text-xs font-semibold text-white shadow-lg shadow-violet-500/20 hover:from-violet-500 hover:to-indigo-500 active:scale-95 transition-all disabled:opacity-50"
          >
            {isRendering ? (
              <>
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                <span>Re-rendering...</span>
              </>
            ) : justSaved ? (
              <>
                <Check className="h-3.5 w-3.5 text-emerald-400" />
                <span>Up to Date</span>
              </>
            ) : (
              <>
                <Sparkles className="h-3.5 w-3.5" />
                <span>Re-render Clip</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Visual Timeline Waveform Simulation & Range Handles */}
      <div className="space-y-4 pt-2">
        {/* Simulated Waveform & Highlight Area */}
        <div className="relative h-14 w-full bg-black/40 rounded-xl overflow-hidden border border-white/10 flex items-center px-2">
          {/* Waveform vertical bars */}
          <div className="absolute inset-0 flex items-center justify-between px-3 opacity-30 pointer-events-none">
            {Array.from({ length: 48 }).map((_, i) => (
              <div
                key={i}
                className="w-1 bg-violet-400 rounded-full"
                style={{
                  height: `${20 + ((i * 17) % 65)}%`,
                }}
              />
            ))}
          </div>

          {/* Active selection highlight box */}
          <div
            className="absolute top-0 bottom-0 bg-violet-500/20 border-x-2 border-violet-500 transition-all pointer-events-none"
            style={{
              left: `${(startTime / (maxVideoDuration || 100)) * 100}%`,
              width: `${(duration / (maxVideoDuration || 100)) * 100}%`,
            }}
          >
            <div className="absolute top-1 left-2 text-[9px] font-mono font-bold text-violet-300">
              HOOK START
            </div>
            <div className="absolute bottom-1 right-2 text-[9px] font-mono font-bold text-violet-300">
              PAYOFF END
            </div>
          </div>
        </div>

        {/* Sliders */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="text-zinc-400">Start Timestamp</span>
              <span className="font-mono font-semibold text-white">{formatSeconds(startTime)}s</span>
            </div>
            <input
              type="range"
              min={0}
              max={maxVideoDuration || 100}
              step={0.1}
              value={startTime}
              onChange={handleStartChange}
              className="w-full accent-violet-500 h-1.5 bg-zinc-800 rounded-lg cursor-pointer"
            />
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="text-zinc-400">End Timestamp</span>
              <span className="font-mono font-semibold text-white">{formatSeconds(endTime)}s</span>
            </div>
            <input
              type="range"
              min={0}
              max={maxVideoDuration || 100}
              step={0.1}
              value={endTime}
              onChange={handleEndChange}
              className="w-full accent-violet-500 h-1.5 bg-zinc-800 rounded-lg cursor-pointer"
            />
          </div>
        </div>
      </div>

      {/* Subtitles & Typography Styling Workstation */}
      <div className="pt-4 border-t border-white/5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Subtitles className="h-4 w-4 text-violet-400" />
            <div>
              <span className="text-xs font-semibold text-zinc-300">Burn Animated Subtitles</span>
              <p className="text-[11px] text-zinc-400">Burn high-retention synchronized karaoke subtitles into video</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => {
              setBurnCaptions(!burnCaptions);
              setJustSaved(false);
            }}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              burnCaptions ? "bg-violet-600" : "bg-zinc-800"
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                burnCaptions ? "translate-x-6" : "translate-x-1"
              }`}
            />
          </button>
        </div>

        {burnCaptions && (
          <div className="space-y-4 pl-0 sm:pl-6 border-l-0 sm:border-l-2 border-violet-500/20 animate-in fade-in duration-200">
            {/* Subtitle Presets Grid */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-zinc-300">Subtitle Style Preset</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-violet-500/20 text-violet-300 border border-violet-500/30 capitalize">
                  {captionStyle.replace(/_/g, " ")}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
                {[
                  { id: "tiktok_viral", name: "TikTok Viral", font: "Arial Black" },
                  { id: "meme", name: "Meme Classic", font: "Impact" },
                  { id: "white_background", name: "White Card Box", font: "Arial Black" },
                  { id: "nostalgic", name: "Nostalgic", font: "Courier" },
                  { id: "old_history", name: "Old History", font: "Georgia" },
                  { id: "hormozi_bold", name: "Hormozi Punch", font: "Impact" },
                  { id: "bold_yellow", name: "Bold Yellow", font: "Arial Black" },
                  { id: "clean_white", name: "Clean White", font: "Arial" },
                  { id: "capcut_black_box", name: "CapCut Black", font: "Arial Black" },
                  { id: "capcut_yellow_box", name: "CapCut Yellow", font: "Impact" },
                  { id: "tiktok_boxed", name: "TikTok Boxed", font: "Arial Black" },
                  { id: "cyber_neon", name: "Cyber Neon", font: "Arial Black" },
                  { id: "cinematic", name: "Cinematic", font: "Georgia" },
                  { id: "podcast_box", name: "Podcast Box", font: "Trebuchet" },
                ].map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => {
                      setCaptionStyle(s.id);
                      setJustSaved(false);
                    }}
                    className={`p-2 rounded-xl border text-left transition-all ${
                      captionStyle === s.id
                        ? "bg-violet-600/20 border-violet-500 text-white shadow-sm ring-1 ring-violet-500/50"
                        : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white hover:bg-white/[0.04]"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-1 mb-0.5">
                      <span className="text-xs font-semibold truncate text-white">{s.name}</span>
                      <span className="text-[9px] font-mono text-zinc-500 shrink-0">{s.font}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Live Subtitle Style Preview Box */}
            <div className="rounded-xl bg-black/70 border border-violet-500/30 p-3.5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-zinc-400 flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5 text-violet-400" />
                  <span>Subtitle Appearance Preview</span>
                </span>
                <span className="text-[10px] text-zinc-500">Zero emoji tofu boxes</span>
              </div>
              <div className="relative rounded-lg bg-zinc-950 border border-white/5 h-20 flex items-center justify-center overflow-hidden px-4">
                {captionStyle === "white_background" ? (
                  <span className="inline-block bg-white text-black font-black px-3.5 py-1 rounded uppercase tracking-wider text-xs shadow-xl font-sans">
                    THIS IS THE <span className="text-red-600">SECRET</span> FORMULA
                  </span>
                ) : captionStyle === "capcut_black_box" ? (
                  <span className="inline-block bg-black text-white font-black px-3 py-1 rounded uppercase tracking-wider text-xs shadow-xl border border-white/20 font-sans">
                    THIS IS THE <span className="text-yellow-300">SECRET</span> FORMULA
                  </span>
                ) : captionStyle === "capcut_yellow_box" ? (
                  <span className="inline-block bg-yellow-400 text-black font-black px-3 py-1 rounded uppercase tracking-wider text-xs shadow-xl font-sans">
                    THIS IS THE <span className="text-white">SECRET</span> FORMULA
                  </span>
                ) : captionStyle === "tiktok_boxed" ? (
                  <span className="inline-block bg-[#141414] text-white font-black px-3 py-1 rounded uppercase tracking-wider text-xs shadow-xl border border-white/10 font-sans">
                    THIS IS THE <span className="text-emerald-400">SECRET</span> FORMULA
                  </span>
                ) : captionStyle === "meme" ? (
                  <span className="text-white font-black uppercase text-sm tracking-widest drop-shadow-[0_4px_8px_rgba(0,0,0,1)] font-sans">
                    THIS IS THE <span className="text-yellow-300">SECRET</span> FORMULA
                  </span>
                ) : captionStyle === "hormozi_bold" ? (
                  <span className="text-white font-black uppercase text-sm tracking-wide drop-shadow-[0_3px_6px_rgba(0,0,0,1)] font-sans">
                    THIS IS THE <span className="text-lime-400">SECRET</span> FORMULA
                  </span>
                ) : captionStyle === "nostalgic" ? (
                  <span className="text-amber-200 font-mono font-bold text-xs tracking-widest drop-shadow-[0_2px_4px_rgba(20,10,5,0.9)]">
                    THIS IS THE <span className="text-amber-400">SECRET</span> FORMULA
                  </span>
                ) : captionStyle === "old_history" ? (
                  <span className="text-amber-100 font-serif italic text-xs tracking-wide drop-shadow-[0_2px_4px_rgba(10,15,25,0.9)]">
                    THIS IS THE <span className="text-amber-300">SECRET</span> FORMULA
                  </span>
                ) : captionStyle === "cyber_neon" ? (
                  <span className="text-cyan-300 font-black uppercase text-xs tracking-wider drop-shadow-[0_0_8px_rgba(236,72,153,0.9)] font-sans">
                    THIS IS THE <span className="text-pink-400">SECRET</span> FORMULA
                  </span>
                ) : captionStyle === "cinematic" ? (
                  <span className="text-zinc-200 font-serif italic text-xs tracking-wider drop-shadow-[0_2px_4px_rgba(0,0,0,0.9)]">
                    This is the secret formula
                  </span>
                ) : captionStyle === "podcast_box" ? (
                  <span className="inline-block bg-black/80 text-white font-semibold px-2.5 py-0.5 rounded text-xs font-sans">
                    This is the <span className="text-amber-300">secret</span> formula
                  </span>
                ) : captionStyle === "clean_white" ? (
                  <span className="text-white font-medium text-xs drop-shadow-[0_2px_4px_rgba(0,0,0,0.8)] font-sans">
                    This is the secret formula
                  </span>
                ) : (
                  <span className="text-white font-black uppercase text-xs tracking-wide drop-shadow-[0_2px_5px_rgba(0,0,0,1)] font-sans">
                    THIS IS THE <span className="text-yellow-300">SECRET</span> FORMULA
                  </span>
                )}
              </div>
            </div>

            {/* Position Controls */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-zinc-300">Screen Position</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-violet-500/10 text-violet-400 border border-violet-500/20">
                  {subtitlePosition}% from Top ({subtitlePosition <= 25 ? "Top" : subtitlePosition <= 45 ? "Upper-Mid" : subtitlePosition <= 60 ? "Center" : subtitlePosition <= 80 ? "Lower-Third" : "Bottom"})
                </span>
              </div>

              <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
                {[
                  { label: "Top", pos: 20 },
                  { label: "Upper-Mid", pos: 35 },
                  { label: "Center", pos: 50 },
                  { label: "Lower-3rd", pos: 75 },
                  { label: "Bottom", pos: 88 },
                ].map((p) => (
                  <button
                    key={p.pos}
                    type="button"
                    onClick={() => {
                      setSubtitlePosition(p.pos);
                      setJustSaved(false);
                    }}
                    className={`rounded-lg py-1.5 px-2 text-center text-xs font-medium border transition-all ${
                      subtitlePosition === p.pos
                        ? "bg-violet-600/30 border-violet-400 text-white shadow-sm"
                        : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white"
                    }`}
                  >
                    {p.label} ({p.pos}%)
                  </button>
                ))}
              </div>

              {/* Slider & Phone Preview */}
              <div className="flex items-center gap-4 pt-1">
                <div className="flex-1 space-y-1">
                  <input
                    type="range"
                    min={15}
                    max={88}
                    step={1}
                    value={subtitlePosition}
                    onChange={(e) => {
                      setSubtitlePosition(Number(e.target.value));
                      setJustSaved(false);
                    }}
                    className="w-full accent-violet-500 h-1.5 bg-zinc-800 rounded-lg cursor-pointer"
                  />
                  <div className="flex justify-between text-[9px] text-zinc-500">
                    <span>Top (15%)</span>
                    <span>Center (50%)</span>
                    <span>Lower-Third (75%)</span>
                    <span>Bottom (88%)</span>
                  </div>
                </div>

                {/* Mini phone screen preview */}
                <div className="w-10 h-16 rounded-lg bg-black/70 border border-violet-500/40 relative overflow-hidden flex-shrink-0 shadow-inner">
                  {addHookHeader && (
                    <div
                      className="absolute left-1 right-1 h-1 bg-amber-400 rounded-full shadow-sm shadow-amber-400/80 transition-all duration-150"
                      style={{ top: `${hookHeaderPosition}%` }}
                    />
                  )}
                  <div
                    className="absolute left-1 right-1 h-1.5 bg-yellow-400 rounded-full shadow-sm shadow-yellow-400/50 transition-all duration-150"
                    style={{ top: `${subtitlePosition}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Sticky TikTok Hook Header Controls */}
      <div className="pt-4 border-t border-white/5 space-y-3.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Flame className="h-4 w-4 text-amber-400" />
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-semibold text-white">Sticky TikTok Hook Header</span>
                <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">VIRAL HOOK</span>
              </div>
              <p className="text-[11px] text-zinc-400">Keep catchy creator title overlay with emojis visible throughout clip</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => {
              setAddHookHeader(!addHookHeader);
              setJustSaved(false);
            }}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              addHookHeader ? "bg-amber-500" : "bg-zinc-800"
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                addHookHeader ? "translate-x-6" : "translate-x-1"
              }`}
            />
          </button>
        </div>

        {addHookHeader && (
          <div className="space-y-3.5 pt-1 animate-in fade-in duration-200">
            {/* Custom Hook Header Text Input & One-click Emoji picker */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="text-zinc-300 font-medium">Hook Header Text:</span>
                <span className="text-[10px] text-zinc-500">Auto-formatted in bold creator style</span>
              </div>
              <input
                type="text"
                value={hookHeaderText}
                onChange={(e) => {
                  setHookHeaderText(e.target.value);
                  setJustSaved(false);
                }}
                placeholder="Leave blank to use AI detected hook title, or type custom..."
                className="w-full rounded-xl bg-black/40 border border-white/10 px-3.5 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-amber-500"
              />
            </div>

            {/* Position Presets */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-zinc-300">Hook Screen Position</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  {hookHeaderPosition}% from Top ({hookHeaderPosition <= 15 ? "Top Banner" : hookHeaderPosition <= 30 ? "Upper-Third" : hookHeaderPosition <= 55 ? "Center" : "Bottom"})
                </span>
              </div>

              <div className="grid grid-cols-4 gap-2">
                {[
                  { label: "Top Banner", pos: 12 },
                  { label: "Upper 3rd", pos: 25 },
                  { label: "Center", pos: 50 },
                  { label: "Bottom", pos: 85 },
                ].map((p) => (
                  <button
                    key={p.pos}
                    type="button"
                    onClick={() => {
                      setHookHeaderPosition(p.pos);
                      setJustSaved(false);
                    }}
                    className={`rounded-lg py-1.5 px-2 text-center text-xs font-medium border transition-all ${
                      hookHeaderPosition === p.pos
                        ? "bg-amber-500/25 border-amber-400 text-white shadow-sm"
                        : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white"
                    }`}
                  >
                    {p.label} ({p.pos}%)
                  </button>
                ))}
              </div>

              {/* Slider & Phone Preview */}
              <div className="flex items-center gap-4 pt-1">
                <div className="flex-1 space-y-1">
                  <input
                    type="range"
                    min={8}
                    max={85}
                    step={1}
                    value={hookHeaderPosition}
                    onChange={(e) => {
                      setHookHeaderPosition(Number(e.target.value));
                      setJustSaved(false);
                    }}
                    className="w-full accent-amber-400 h-1.5 bg-zinc-800 rounded-lg cursor-pointer"
                  />
                  <div className="flex justify-between text-[9px] text-zinc-500">
                    <span>Top Banner (8%)</span>
                    <span>Upper (25%)</span>
                    <span>Center (50%)</span>
                    <span>Bottom (85%)</span>
                  </div>
                </div>

                <div className="w-10 h-16 rounded-lg bg-black/70 border border-amber-500/40 relative overflow-hidden flex-shrink-0 shadow-inner">
                  <div
                    className="absolute left-1 right-1 h-1.5 bg-amber-400 rounded-full shadow-sm shadow-amber-400/80 transition-all duration-150"
                    style={{ top: `${hookHeaderPosition}%` }}
                  />
                  <div
                    className="absolute left-1 right-1 h-1 bg-yellow-300/50 rounded-full transition-all duration-150"
                    style={{ top: `${subtitlePosition}%` }}
                  />
                </div>
              </div>

              {/* Hook Header Visual Style Selection */}
              <div className="space-y-2 pt-2 border-t border-white/5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-zinc-300">Hook Visual Style & Typography</span>
                  <span className="text-[10px] text-amber-400/90 font-mono">
                    {hookHeaderStyle === "white_box"
                      ? "White Card Box"
                      : hookHeaderStyle === "meme"
                      ? "Classic Meme"
                      : hookHeaderStyle === "nostalgic"
                      ? "Vintage Typewriter"
                      : hookHeaderStyle === "old_history"
                      ? "History Serif"
                      : hookHeaderStyle === "neon_cyber"
                      ? "Neon Glow"
                      : "Viral Creator"}
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
                  {[
                    { id: "viral_creator", label: "Viral Creator", icon: Zap, font: "Sans Bold" },
                    { id: "white_box", label: "White Card", icon: FileText, font: "Arial Black" },
                    { id: "meme", label: "Classic Meme", icon: MessageSquare, font: "Impact" },
                    { id: "nostalgic", label: "Nostalgic", icon: Clock, font: "Courier Type" },
                    { id: "old_history", label: "Old History", icon: BookOpen, font: "Georgia Serif" },
                    { id: "neon_cyber", label: "Cyber Neon", icon: Sparkles, font: "Cyan Glow" },
                  ].map((styleOpt) => {
                    const IconComponent = styleOpt.icon;
                    return (
                      <button
                        key={styleOpt.id}
                        type="button"
                        onClick={() => {
                          setHookHeaderStyle(styleOpt.id);
                          setJustSaved(false);
                        }}
                        className={`p-2 rounded-xl border text-center transition-all flex flex-col items-center justify-center gap-1.5 ${
                          hookHeaderStyle === styleOpt.id
                            ? "bg-amber-500/20 border-amber-400 text-white shadow-sm ring-1 ring-amber-400/40"
                            : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white hover:bg-white/[0.04]"
                        }`}
                      >
                        <div className="flex items-center gap-1.5">
                          <IconComponent className="h-3.5 w-3.5 text-amber-400 shrink-0" />
                          <span className="text-xs font-semibold leading-tight">{styleOpt.label}</span>
                        </div>
                        <span className="text-[9px] font-mono text-zinc-500">{styleOpt.font}</span>
                      </button>
                    );
                  })}
                </div>

                {/* Dynamic Creator Style Preview */}
                <div className="rounded-xl bg-black/60 border border-white/10 p-3 flex items-center justify-center min-h-[50px]">
                  <div
                    className={`px-4 py-1.5 text-center text-xs transition-all ${
                      hookHeaderStyle === "white_box"
                        ? "bg-white text-black font-black uppercase tracking-tight shadow-lg rounded-sm"
                        : hookHeaderStyle === "meme"
                        ? "text-white font-black uppercase tracking-wider text-sm [text-shadow:_2px_2px_0_rgb(0_0_0),_-2px_2px_0_rgb(0_0_0),_2px_-2px_0_rgb(0_0_0),_-2px_-2px_0_rgb(0_0_0)] font-sans"
                        : hookHeaderStyle === "nostalgic"
                        ? "bg-amber-950/80 text-amber-200 border border-amber-600/40 font-mono tracking-widest uppercase rounded shadow-inner text-xs"
                        : hookHeaderStyle === "old_history"
                        ? "bg-stone-900/90 text-amber-100 border-t border-b border-amber-500/50 font-serif italic tracking-wide text-xs px-5 shadow-lg"
                        : hookHeaderStyle === "neon_cyber"
                        ? "text-cyan-300 font-black uppercase tracking-widest [text-shadow:_0_0_8px_#06b6d4,_0_0_20px_#ec4899] font-mono text-xs"
                        : "text-yellow-400 font-extrabold uppercase tracking-wide [text-shadow:_1px_1px_0_#000,_-1px_-1px_0_#000] font-sans"
                    }`}
                  >
                    {hookHeaderText.trim() ? hookHeaderText : "WHY NOBODY TALKS ABOUT THIS"}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Framing & Blur Controls */}
      <div className="pt-4 border-t border-white/5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sliders className="h-4 w-4 text-cyan-400" />
            <span className="text-xs font-semibold text-zinc-300">Framing & Canvas Aspect Ratio</span>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            {framingMode === "crop_9_16" ? "9:16 Vertical Crop" : framingMode === "blur_fit_9_16" ? "16:9 Blurred Canvas" : "16:9 Landscape"}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          <button
            type="button"
            onClick={() => {
              setFramingMode("crop_9_16");
              setJustSaved(false);
            }}
            className={`rounded-xl p-3 text-left border transition-all ${
              framingMode === "crop_9_16"
                ? "bg-violet-500/15 border-violet-400 text-white shadow-sm"
                : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white hover:border-white/20"
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <Smartphone className="h-3.5 w-3.5 text-violet-400" />
              <span className="text-xs font-semibold">9:16 Vertical</span>
            </div>
            <p className="text-[10px] text-zinc-400">Smart focal tracking</p>
          </button>

          <button
            type="button"
            onClick={() => {
              setFramingMode("blur_fit_9_16");
              setJustSaved(false);
            }}
            className={`rounded-xl p-3 text-left border transition-all ${
              framingMode === "blur_fit_9_16"
                ? "bg-violet-500/15 border-violet-400 text-white shadow-sm"
                : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white hover:border-white/20"
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <Maximize2 className="h-3.5 w-3.5 text-cyan-400" />
              <span className="text-xs font-semibold">16:9 Frosted Blur</span>
            </div>
            <p className="text-[10px] text-zinc-400">Fit with canvas blur</p>
          </button>

          <button
            type="button"
            onClick={() => {
              setFramingMode("original_16_9");
              setJustSaved(false);
            }}
            className={`rounded-xl p-3 text-left border transition-all ${
              framingMode === "original_16_9"
                ? "bg-violet-500/15 border-violet-400 text-white shadow-sm"
                : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white hover:border-white/20"
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <Monitor className="h-3.5 w-3.5 text-emerald-400" />
              <span className="text-xs font-semibold">16:9 Landscape</span>
            </div>
            <p className="text-[10px] text-zinc-400">Native aspect ratio</p>
          </button>

        </div>

        {/* If Blurred Canvas is chosen, show Blur Ratio Controls */}
        {framingMode === "blur_fit_9_16" && (
          <div className="rounded-xl bg-black/40 border border-cyan-500/30 p-3.5 space-y-3 animate-in fade-in duration-200">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-cyan-300">
                Background Blur Radius: {blurRadius}px
              </span>
              <span className="text-[10px] text-zinc-500">Dimmed 35%</span>
            </div>

            <div className="grid grid-cols-4 gap-2">
              {[
                { label: "Light", r: 15 },
                { label: "Medium", r: 30 },
                { label: "Heavy", r: 50 },
                { label: "Ultra", r: 80 },
              ].map((b) => (
                <button
                  key={b.r}
                  type="button"
                  onClick={() => {
                    setBlurRadius(b.r);
                    setJustSaved(false);
                  }}
                  className={`rounded-lg py-1.5 px-2 text-center text-xs font-medium border transition-all ${
                    blurRadius === b.r
                      ? "bg-cyan-500/25 border-cyan-400 text-white"
                      : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white"
                  }`}
                >
                  {b.label} ({b.r}px)
                </button>
              ))}
            </div>

            <input
              type="range"
              min={10}
              max={80}
              step={5}
              value={blurRadius}
              onChange={(e) => {
                setBlurRadius(Number(e.target.value));
                setJustSaved(false);
              }}
              className="w-full accent-cyan-400 h-1.5 bg-zinc-800 rounded-lg cursor-pointer"
            />
          </div>
        )}
      </div>

      {/* Watermark Removal & Studio Enhancement Controls */}
      <div className="pt-4 border-t border-white/5 space-y-4">
        {/* Watermark / Logo Eraser */}
        <div className="rounded-xl bg-white/[0.02] border border-white/10 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Eraser className="h-4 w-4 text-cyan-400" />
              <div>
                <span className="text-xs font-semibold text-white">Erase Watermark / Logo / Trademark</span>
                <p className="text-[10px] text-zinc-400">Interpolate corner logo or watermark before vertical cropping</p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => {
                setRemoveWatermark(!removeWatermark);
                setJustSaved(false);
              }}
              className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                removeWatermark ? "bg-cyan-500" : "bg-zinc-800"
              }`}
            >
              <span
                className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                  removeWatermark ? "translate-x-4" : "translate-x-0.5"
                }`}
              />
            </button>
          </div>

          {removeWatermark && (
            <div className="pt-2 border-t border-white/5 space-y-2">
              <span className="text-[10px] text-cyan-300 font-semibold">Watermark Location:</span>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
                {[
                  { label: "Top Right", value: "top_right" },
                  { label: "Bottom Right", value: "bottom_right" },
                  { label: "Top Left", value: "top_left" },
                  { label: "Bottom Left", value: "bottom_left" },
                ].map((pos) => (
                  <button
                    key={pos.value}
                    type="button"
                    onClick={() => {
                      setWatermarkPosition(pos.value as any);
                      setJustSaved(false);
                    }}
                    className={`rounded-lg py-1 px-2 text-center text-[10px] font-medium border transition-all ${
                      watermarkPosition === pos.value
                        ? "bg-cyan-500/25 border-cyan-400 text-white shadow-sm"
                        : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white"
                    }`}
                  >
                    {pos.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Studio Enhancement */}
        <div className="rounded-xl bg-white/[0.02] border border-white/10 p-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Wand2 className="h-4 w-4 text-emerald-400" />
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-semibold text-white">Studio Enhancement &amp; Color Boost</span>
                <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">STUDIO</span>
              </div>
              <p className="text-[10px] text-zinc-400">Mobile sharpening, vibrant contrast and EBU R128 loudness</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => {
              setEnhanceQuality(!enhanceQuality);
              setJustSaved(false);
            }}
            className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
              enhanceQuality ? "bg-emerald-500" : "bg-zinc-800"
            }`}
          >
            <span
              className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                enhanceQuality ? "translate-x-4" : "translate-x-0.5"
              }`}
            />
          </button>
        </div>
      </div>
    </div>
  );
}
