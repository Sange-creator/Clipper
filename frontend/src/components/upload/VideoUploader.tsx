"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  UploadCloud,
  FileVideo,
  Sparkles,
  Sliders,
  Layers,
  Clock,
  Type,
  AlertCircle,
  Loader2,
  Mic,
  Zap,
  Volume2,
  Subtitles,
  Scissors,
} from "lucide-react";
import { api } from "@/lib/api";
import { formatFileSize } from "@/lib/utils";
import { VideoInfo } from "@/lib/types";

export function VideoUploader() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Upload state
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [uploadedVideo, setUploadedVideo] = useState<VideoInfo | null>(null);

  // V3 Configuration Presets
  const [mode, setMode] = useState<"podcast" | "viral_moments">("podcast");
  const [burnCaptions, setBurnCaptions] = useState<boolean>(true);
  const [removeDeadAir, setRemoveDeadAir] = useState<boolean>(true);
  const [framingMode, setFramingMode] = useState<"crop_9_16" | "blur_fit_9_16" | "original_16_9">("crop_9_16");
  const [blurRadius, setBlurRadius] = useState<number>(30);
  const [subtitlePosition, setSubtitlePosition] = useState<number>(75);
  const [targetClipsCount, setTargetClipsCount] = useState<number>(10);
  const [durationPreset, setDurationPreset] = useState<"15-30s" | "30-45s" | "45-60s" | "60-90s" | "custom">("30-45s");
  const [captionStyle, setCaptionStyle] = useState<"bold_yellow" | "clean_white" | "podcast_box" | "cinematic" | "meme_impact" | "cyber_neon">("bold_yellow");
  const [aiProvider, setAiProvider] = useState<"gemini" | "groq" | "mock" | "auto">("auto");
  const [customInstructions, setCustomInstructions] = useState<string>("");
  const [isLaunching, setIsLaunching] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await processSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await processSelectedFile(e.target.files[0]);
    }
  };

  const processSelectedFile = async (selectedFile: File) => {
    setFile(selectedFile);
    setError(null);
    setIsUploading(true);
    setUploadProgress(20);

    try {
      setUploadProgress(50);
      const res = await api.uploadVideo(selectedFile);
      setUploadProgress(100);
      setUploadedVideo(res.video);
    } catch (err: any) {
      setError(err.message || "Failed to upload video");
      setFile(null);
    } finally {
      setIsUploading(false);
    }
  };

  const handleStartProcessing = async () => {
    if (!uploadedVideo) return;
    setIsLaunching(true);
    setError(null);

    try {
      const job = await api.createJob({
        video_id: uploadedVideo.id,
        mode: mode,
        target_clips_count: targetClipsCount,
        duration_preset: durationPreset,
        caption_style: burnCaptions ? captionStyle : "none",
        burn_captions: burnCaptions,
        remove_dead_air: removeDeadAir,
        framing_mode: framingMode,
        blur_radius: blurRadius,
        subtitle_position: subtitlePosition,
        reframing_mode: "center_crop",
        ai_provider: aiProvider === "auto" ? undefined : aiProvider,
        custom_instructions: customInstructions.trim() || undefined,
      });

      router.push(`/jobs/${job.id}`);
    } catch (err: any) {
      setError(err.message || "Failed to start clipping job");
      setIsLaunching(false);
    }
  };



  return (
    <div className="w-full max-w-4xl mx-auto space-y-8">
      {/* Upload Dropzone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !file && fileInputRef.current?.click()}
        className={`relative group cursor-pointer overflow-hidden rounded-2xl border-2 border-dashed p-8 sm:p-12 transition-all duration-300 ${
          isDragging
            ? "border-violet-500 bg-violet-500/10 scale-[1.01]"
            : file
            ? "border-emerald-500/40 bg-emerald-500/[0.02]"
            : "border-white/10 hover:border-violet-500/40 hover:bg-white/[0.02] glass-panel"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="video/mp4,video/quicktime,video/x-matroska,video/webm"
          className="hidden"
          onChange={handleFileChange}
        />

        {file && uploadedVideo ? (
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                <FileVideo className="h-7 w-7" />
              </div>
              <div className="space-y-1 text-left">
                <h3 className="font-semibold text-white text-base truncate max-w-sm sm:max-w-md">
                  {uploadedVideo.filename}
                </h3>
                <div className="flex flex-wrap items-center gap-3 text-xs text-zinc-400">
                  <span>{formatFileSize(uploadedVideo.file_size_bytes)}</span>
                  <span>•</span>
                  <span>{uploadedVideo.duration_seconds.toFixed(1)}s duration</span>
                  <span>•</span>
                  <span>{uploadedVideo.width}x{uploadedVideo.height}</span>
                  <span>•</span>
                  <span className="text-emerald-400 font-medium">Validated</span>
                </div>
              </div>
            </div>

            <button
              onClick={(e) => {
                e.stopPropagation();
                setFile(null);
                setUploadedVideo(null);
              }}
              className="rounded-lg px-3 py-1.5 text-xs text-zinc-400 hover:text-white hover:bg-white/10 border border-white/10 transition-colors"
            >
              Change File
            </button>
          </div>
        ) : isUploading ? (
          <div className="flex flex-col items-center justify-center space-y-4 text-center">
            <Loader2 className="h-10 w-10 text-violet-400 animate-spin" />
            <div>
              <p className="font-semibold text-white">Inspecting & Uploading Video...</p>
              <p className="text-xs text-zinc-400 mt-1">Analyzing codecs, audio tracks, and duration</p>
            </div>
            <div className="w-48 bg-zinc-800 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-violet-500 h-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center space-y-4 text-center py-2">
            <div className="relative group/emblem">
              <div className="absolute -inset-2 rounded-3xl bg-gradient-to-r from-violet-600 via-indigo-600 to-cyan-500 opacity-30 blur-lg group-hover/emblem:opacity-60 transition duration-500" />
              <div className="relative flex h-20 w-20 items-center justify-center rounded-2xl bg-[#101322] border border-violet-500/30 p-2 shadow-2xl group-hover/emblem:scale-105 transition-transform duration-300">
                <img src="/logo.svg" alt="Clipper Pro" className="w-full h-full" />
              </div>
            </div>
            <div>
              <p className="text-base font-bold text-white">
                Drag and drop your long-form video, or <span className="text-violet-400 underline underline-offset-4">browse files</span>
              </p>
              <p className="text-xs text-slate-400 mt-1.5 max-w-md mx-auto">
                MP4, MOV, MKV, WebM • Automatic hook discovery, 9:16 smart reframing & animated captions
              </p>
            </div>
          </div>
        )}

      </div>

      {error && (
        <div className="flex items-center gap-3 rounded-xl bg-rose-500/10 border border-rose-500/20 p-4 text-sm text-rose-400">
          <AlertCircle className="h-5 w-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Preset & Optimization Options (Enabled once file uploaded) */}
      <div className={`space-y-6 transition-all duration-300 ${uploadedVideo ? "opacity-100" : "opacity-60 pointer-events-none"}`}>
        <div className="flex items-center gap-2 text-white font-semibold text-sm">
          <Sliders className="h-4 w-4 text-violet-400" />
          <span>Clipping Mode & AI Settings</span>
        </div>

        {/* 1. Core V3 Mode Selector */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            onClick={() => setMode("podcast")}
            className={`cursor-pointer rounded-2xl p-5 border transition-all duration-300 flex flex-col justify-between ${
              mode === "podcast"
                ? "bg-violet-600/15 border-violet-500 shadow-xl shadow-violet-500/10 ring-1 ring-violet-500/40"
                : "bg-white/[0.02] border-white/10 hover:border-white/20 hover:bg-white/[0.04]"
            }`}
          >
            <div className="flex items-center gap-3.5 mb-3">
              <div className={`flex h-11 w-11 items-center justify-center rounded-xl ${
                mode === "podcast" ? "bg-violet-500 text-white" : "bg-white/10 text-zinc-400"
              }`}>
                <Mic className="h-5 w-5" />
              </div>
              <div>
                <h4 className="font-semibold text-white text-sm">Regular Podcast Clipper</h4>
                <span className="text-[11px] text-violet-400 font-medium">Interviews & Discussions</span>
              </div>
            </div>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Optimized for conversation, banter, debates, and quotable life advice. Preserves natural speaker flow while discarding introductions and ad sponsors.
            </p>
          </div>

          <div
            onClick={() => setMode("viral_moments")}
            className={`cursor-pointer rounded-2xl p-5 border transition-all duration-300 flex flex-col justify-between ${
              mode === "viral_moments"
                ? "bg-amber-500/15 border-amber-500 shadow-xl shadow-amber-500/10 ring-1 ring-amber-500/40"
                : "bg-white/[0.02] border-white/10 hover:border-white/20 hover:bg-white/[0.04]"
            }`}
          >
            <div className="flex items-center gap-3.5 mb-3">
              <div className={`flex h-11 w-11 items-center justify-center rounded-xl ${
                mode === "viral_moments" ? "bg-amber-500 text-black" : "bg-white/10 text-zinc-400"
              }`}>
                <Zap className="h-5 w-5" />
              </div>
              <div>
                <h4 className="font-semibold text-white text-sm">Long Video Viral Moments</h4>
                <span className="text-[11px] text-amber-400 font-medium">Documentaries & Commentary</span>
              </div>
            </div>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Discovers surprising revelations, dramatic story peaks, mind-bending facts, and funny incidents with standalone story completion and strong payoff.
            </p>
          </div>
        </div>

        {/* 2. Framing & Aspect Ratio Selector */}
        <div className="glass-panel rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sliders className="h-4 w-4 text-cyan-400" />
              <div>
                <h4 className="text-xs font-semibold text-white">Framing & Aspect Ratio</h4>
                <p className="text-[11px] text-zinc-400">Choose output resolution format and canvas composition</p>
              </div>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              {framingMode === "crop_9_16" ? "9:16 Vertical Crop" : framingMode === "blur_fit_9_16" ? "16:9 Blurred Canvas" : "16:9 Landscape"}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-white/5">
            {/* Mode 1: 9:16 Smart Crop */}
            <div
              onClick={() => setFramingMode("crop_9_16")}
              className={`rounded-xl p-3.5 cursor-pointer border transition-all ${
                framingMode === "crop_9_16"
                  ? "bg-cyan-500/15 border-cyan-500 text-white shadow-lg shadow-cyan-500/10"
                  : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white hover:border-white/20"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm">📱</span>
                <span className="text-[9px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-white/10 text-zinc-300">
                  Default
                </span>
              </div>
              <h5 className="text-xs font-semibold text-white">9:16 Full Vertical</h5>
              <p className="text-[10px] text-cyan-400 font-medium mt-0.5">TikTok • Reels • Shorts</p>
              <p className="text-[10px] text-zinc-400 mt-2 leading-relaxed">
                Fills 1080x1920 vertical canvas. Centers subject and crops widescreen edges.
              </p>
            </div>

            {/* Mode 2: 16:9 in 9:16 Blurred Canvas */}
            <div
              onClick={() => setFramingMode("blur_fit_9_16")}
              className={`rounded-xl p-3.5 cursor-pointer border transition-all ${
                framingMode === "blur_fit_9_16"
                  ? "bg-cyan-500/15 border-cyan-500 text-white shadow-lg shadow-cyan-500/10"
                  : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white hover:border-white/20"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm">🖼️</span>
                <span className="text-[9px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300">
                  Popular
                </span>
              </div>
              <h5 className="text-xs font-semibold text-white">16:9 in 9:16 Blurred</h5>
              <p className="text-[10px] text-cyan-400 font-medium mt-0.5">Podcasts & Gameplay</p>
              <p className="text-[10px] text-zinc-400 mt-2 leading-relaxed">
                Fits 100% of widescreen video centered with an aesthetic frosted blurred background.
              </p>
            </div>

            {/* Mode 3: Original 16:9 Landscape */}
            <div
              onClick={() => setFramingMode("original_16_9")}
              className={`rounded-xl p-3.5 cursor-pointer border transition-all ${
                framingMode === "original_16_9"
                  ? "bg-cyan-500/15 border-cyan-500 text-white shadow-lg shadow-cyan-500/10"
                  : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white hover:border-white/20"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm">🖥️</span>
                <span className="text-[9px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-white/10 text-zinc-300">
                  Landscape
                </span>
              </div>
              <h5 className="text-xs font-semibold text-white">Native 16:9 Landscape</h5>
              <p className="text-[10px] text-cyan-400 font-medium mt-0.5">YouTube & Twitter</p>
              <p className="text-[10px] text-zinc-400 mt-2 leading-relaxed">
                Preserves original widescreen resolution with zero vertical cropping or transformation.
              </p>
            </div>
          </div>

          {/* If Blurred Canvas is chosen, show Blur Ratio Controls */}
          {framingMode === "blur_fit_9_16" && (
            <div className="rounded-xl bg-black/40 border border-cyan-500/30 p-4 space-y-3.5 animate-in fade-in duration-200">
              <div className="flex items-center justify-between">
                <label className="text-[11px] font-semibold text-cyan-300 flex items-center gap-1.5">
                  <span>Background Blur Ratio & Intensity:</span>
                  <span className="font-mono text-white bg-cyan-500/20 px-1.5 py-0.5 rounded text-[10px]">
                    {blurRadius}px
                  </span>
                </label>
                <span className="text-[10px] text-zinc-400">Dimmed 35% overlay</span>
              </div>

              {/* Preset Buttons */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {[
                  { label: "Light", radius: 15, desc: "Subtle motion" },
                  { label: "Medium", radius: 30, desc: "Standard aesthetic" },
                  { label: "Heavy", radius: 50, desc: "Frosted glass" },
                  { label: "Ultra", radius: 80, desc: "Ambient glow" },
                ].map((b) => (
                  <button
                    key={b.radius}
                    type="button"
                    onClick={() => setBlurRadius(b.radius)}
                    className={`rounded-lg py-2 px-2.5 text-left border transition-all ${
                      blurRadius === b.radius
                        ? "bg-cyan-500/20 border-cyan-400 text-white shadow-sm"
                        : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white hover:border-white/20"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold">{b.label}</span>
                      <span className="text-[10px] font-mono text-cyan-400">{b.radius}px</span>
                    </div>
                    <p className="text-[9px] text-zinc-500 mt-0.5">{b.desc}</p>
                  </button>
                ))}
              </div>

              {/* Slider */}
              <div className="space-y-1 pt-1">
                <input
                  type="range"
                  min={10}
                  max={80}
                  step={5}
                  value={blurRadius}
                  onChange={(e) => setBlurRadius(Number(e.target.value))}
                  className="w-full accent-cyan-400 h-1.5 bg-zinc-800 rounded-lg cursor-pointer"
                />
                <div className="flex justify-between text-[9px] text-zinc-500">
                  <span>10px (Sharpest)</span>
                  <span>30px (Default)</span>
                  <span>50px (Heavy)</span>
                  <span>80px (Softest)</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 3. Subtitle & Silence Toggles */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

          {/* Subtitle On/Off Toggle */}
          <div className="glass-panel rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Subtitles className="h-4 w-4 text-violet-400" />
                <div>
                  <h4 className="text-xs font-semibold text-white">Burn Animated Subtitles</h4>
                  <p className="text-[11px] text-zinc-400">Burn readable karaoke captions into video</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setBurnCaptions(!burnCaptions)}
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

            {burnCaptions ? (
              <div className="space-y-2 pt-2 border-t border-white/5">
                <label className="text-[11px] font-medium text-zinc-400">Select Caption Style:</label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {[
                    { id: "bold_yellow", name: "Bold Yellow", desc: "Active word pop-in" },
                    { id: "clean_white", name: "Clean White", desc: "Crisp & minimalist" },
                    { id: "podcast_box", name: "Podcast Box", desc: "Dark backing banner" },
                    { id: "cinematic", name: "Cinematic", desc: "Italic letterbox serif" },
                    { id: "meme_impact", name: "Meme Impact", desc: "Heavy outline punch" },
                    { id: "cyber_neon", name: "Cyber Neon", desc: "Cyan & Magenta glow" },
                  ].map((style) => (
                    <button
                      key={style.id}
                      type="button"
                      onClick={() => setCaptionStyle(style.id as any)}
                      className={`rounded-lg p-2 text-left border transition-all ${
                        captionStyle === style.id
                          ? "bg-violet-600/20 border-violet-500 text-white shadow-md"
                          : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white hover:border-white/20"
                      }`}
                    >
                      <p className="text-xs font-medium">{style.name}</p>
                      <p className="text-[9px] text-zinc-500 mt-0.5">{style.desc}</p>
                    </button>
                  ))}
                </div>

                {/* Subtitle Vertical Position Slider & Phone Preview */}
                <div className="pt-3 border-t border-white/5 space-y-3">
                  <div className="flex items-center justify-between">
                    <label className="text-[11px] font-semibold text-violet-300 flex items-center gap-1.5">
                      <span>Subtitle Screen Position:</span>
                      <span className="font-mono text-white bg-violet-500/20 px-1.5 py-0.5 rounded text-[10px]">
                        {subtitlePosition}% from Top
                      </span>
                    </label>
                    <span className="text-[10px] text-zinc-400">
                      {subtitlePosition <= 25 ? "Top Banner" : subtitlePosition <= 45 ? "Upper-Mid" : subtitlePosition <= 60 ? "Center Screen" : subtitlePosition <= 80 ? "Lower-Third (Standard)" : "Bottom Anchor"}
                    </span>
                  </div>

                  {/* Position Presets */}
                  <div className="grid grid-cols-3 sm:grid-cols-5 gap-1.5">
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
                        onClick={() => setSubtitlePosition(p.pos)}
                        className={`rounded-lg py-1.5 px-2 text-center text-[10px] font-medium border transition-all ${
                          subtitlePosition === p.pos
                            ? "bg-violet-600/30 border-violet-400 text-white shadow-sm"
                            : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white"
                        }`}
                      >
                        {p.label} ({p.pos}%)
                      </button>
                    ))}
                  </div>

                  {/* Slider with Mini Interactive Phone Mockup */}
                  <div className="flex items-center gap-3 pt-1">
                    <div className="flex-1 space-y-1">
                      <input
                        type="range"
                        min={15}
                        max={88}
                        step={1}
                        value={subtitlePosition}
                        onChange={(e) => setSubtitlePosition(Number(e.target.value))}
                        className="w-full accent-violet-500 h-1.5 bg-zinc-800 rounded-lg cursor-pointer"
                      />
                      <div className="flex justify-between text-[9px] text-zinc-500">
                        <span>Top (15%)</span>
                        <span>Center (50%)</span>
                        <span>Lower (75%)</span>
                        <span>Bottom (88%)</span>
                      </div>
                    </div>

                    {/* Mini visual 9:16 phone screen preview indicator */}
                    <div className="w-10 h-16 rounded-md bg-black/60 border border-violet-500/40 relative overflow-hidden flex-shrink-0 shadow-inner">
                      {/* Dynamic subtitle placeholder line */}
                      <div
                        className="absolute left-1 right-1 h-1.5 bg-yellow-400 rounded-full shadow-sm shadow-yellow-400/50 transition-all duration-150"
                        style={{ top: `${subtitlePosition}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-[11px] text-zinc-500 pt-2 border-t border-white/5">
                Video will export cleanly with zero burned captions. Standalone .SRT and .ASS subtitle files will still be available for download.
              </p>
            )}
          </div>


          {/* Dead-Air Removal Toggle */}
          <div className="glass-panel rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Scissors className="h-4 w-4 text-amber-400" />
                <div>
                  <h4 className="text-xs font-semibold text-white">Cut Silence & Dead Air</h4>
                  <p className="text-[11px] text-zinc-400">Detect silence &gt;1.2s and splice dead air</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setRemoveDeadAir(!removeDeadAir)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  removeDeadAir ? "bg-amber-500" : "bg-zinc-800"
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    removeDeadAir ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
            </div>

            <p className="text-[11px] text-zinc-400 leading-relaxed pt-2 border-t border-white/5">
              {removeDeadAir
                ? "Aggressively detects awkward pauses and long silences via audio decibel analysis, creating seamless concatenated timeline cuts while keeping speech cadence natural."
                : "Keeps continuous video without audio timeline trimming."}
            </p>
          </div>
        </div>

        {/* 3. Duration & Target Count */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Target Duration Range */}
          <div className="glass-panel rounded-xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-zinc-300 flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5 text-violet-400" /> Target Duration
              </label>
              <span className="text-[11px] text-zinc-500">Story Priority</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {(["15-30s", "30-45s", "45-60s", "60-90s"] as const).map((preset) => (
                <button
                  key={preset}
                  type="button"
                  onClick={() => setDurationPreset(preset)}
                  className={`rounded-lg py-2 text-xs font-medium border transition-all ${
                    durationPreset === preset
                      ? "bg-violet-600/20 border-violet-500 text-white shadow-lg shadow-violet-500/10"
                      : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white hover:border-white/20"
                  }`}
                >
                  {preset}
                </button>
              ))}
            </div>
          </div>

          {/* Number of Clips to Discover */}
          <div className="glass-panel rounded-xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-zinc-300 flex items-center gap-1.5">
                <Layers className="h-3.5 w-3.5 text-violet-400" /> Requested Clips
              </label>
              <span className="text-xs font-semibold text-violet-400">{targetClipsCount} Top Clips</span>
            </div>
            <input
              type="range"
              min={3}
              max={25}
              step={1}
              value={targetClipsCount}
              onChange={(e) => setTargetClipsCount(Number(e.target.value))}
              className="w-full accent-violet-500 h-1.5 bg-zinc-800 rounded-lg cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-zinc-500">
              <span>3 clips</span>
              <span>10 clips (Recommended)</span>
              <span>25 clips</span>
            </div>
          </div>
        </div>

        {/* Custom Instructions Prompt */}
        <div className="glass-panel rounded-xl p-5 space-y-2">
          <label className="text-xs font-medium text-zinc-300">
            Custom Editorial Focus (Optional)
          </label>
          <input
            type="text"
            placeholder="e.g. Focus on debate arguments, shocking statistics, funny moments, or business strategies..."
            value={customInstructions}
            onChange={(e) => setCustomInstructions(e.target.value)}
            className="w-full rounded-lg bg-black/40 border border-white/10 px-3.5 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-violet-500 transition-colors"
          />
        </div>

        {/* Launch Button */}
        <div className="flex justify-end pt-2">
          <button
            onClick={handleStartProcessing}
            disabled={!uploadedVideo || isLaunching}
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 px-8 py-3.5 font-semibold text-white shadow-xl shadow-violet-500/25 hover:from-violet-500 hover:to-indigo-500 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
          >
            {isLaunching ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Launching 21-Stage Pipeline...</span>
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                <span>Discover & Render {mode === "podcast" ? "Podcast" : "Viral"} Clips</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
