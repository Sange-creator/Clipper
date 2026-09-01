"use client";

import { useState } from "react";
import { Scissors, RefreshCw, Sparkles, Sliders, Subtitles, Check, Smartphone, Maximize2, Monitor } from "lucide-react";

import { formatSeconds } from "@/lib/utils";

interface TimelineScrubberProps {
  initialStart: number;
  initialEnd: number;
  maxVideoDuration: number;
  initialFramingMode?: string;
  initialBlurRadius?: number;
  initialSubtitlePosition?: number;
  onRerender: (start: number, end: number, framingMode?: string, blurRadius?: number, subtitlePosition?: number) => Promise<void>;
}

export function TimelineScrubber({
  initialStart,
  initialEnd,
  maxVideoDuration,
  initialFramingMode = "crop_9_16",
  initialBlurRadius = 30,
  initialSubtitlePosition = 75,
  onRerender,
}: TimelineScrubberProps) {
  const [startTime, setStartTime] = useState(initialStart);
  const [endTime, setEndTime] = useState(initialEnd);
  const [framingMode, setFramingMode] = useState<"crop_9_16" | "blur_fit_9_16" | "original_16_9">(
    (initialFramingMode as any) || "crop_9_16"
  );
  const [blurRadius, setBlurRadius] = useState<number>(initialBlurRadius || 30);
  const [subtitlePosition, setSubtitlePosition] = useState<number>(initialSubtitlePosition || 75);
  const [isRendering, setIsRendering] = useState(false);
  const [justSaved, setJustSaved] = useState(false);

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
      await onRerender(startTime, endTime, framingMode, blurRadius, subtitlePosition);
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

      {/* Subtitle Screen Position Slider */}
      <div className="pt-4 border-t border-white/5 space-y-3.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Subtitles className="h-4 w-4 text-violet-400" />
            <span className="text-xs font-semibold text-zinc-300">Subtitle Screen Position</span>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-violet-500/10 text-violet-400 border border-violet-500/20">
            {subtitlePosition}% from Top ({subtitlePosition <= 25 ? "Top" : subtitlePosition <= 45 ? "Upper-Mid" : subtitlePosition <= 60 ? "Center" : subtitlePosition <= 80 ? "Lower-Third" : "Bottom"})
          </span>
        </div>

        {/* Position Presets */}
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
              <span>Top Banner (15%)</span>
              <span>Center (50%)</span>
              <span>Lower-Third (75%)</span>
              <span>Bottom (88%)</span>
            </div>
          </div>

          {/* Mini phone screen preview */}
          <div className="w-10 h-16 rounded-lg bg-black/70 border border-violet-500/40 relative overflow-hidden flex-shrink-0 shadow-inner">
            <div
              className="absolute left-1 right-1 h-1.5 bg-yellow-400 rounded-full shadow-sm shadow-yellow-400/50 transition-all duration-150"
              style={{ top: `${subtitlePosition}%` }}
            />
          </div>
        </div>
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
    </div>
  );
}
