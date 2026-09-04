"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Layers,
  Film,
  Sparkles,
  ArrowLeft,
  Play,
  FileVideo,
  Heart,
  CheckSquare,
  Square,
  AlertCircle,
  Mic,
  Zap,
  Subtitles,
  Scissors,
  Trash2,
  AlertTriangle,
  Smartphone,
  Maximize2,
  Monitor,
  Flame,
  Eraser,
  Wand2,
  Download,
  FileText,
  MessageSquare,
  Clock,
  BookOpen,
} from "lucide-react";


import { api } from "@/lib/api";
import { CaptionStyleType, ProjectDetailResponse, VideoInfo } from "@/lib/types";
import { BatchUploader } from "@/components/upload/BatchUploader";
import { CaptionPresetPicker } from "@/components/review/CaptionPresetPicker";
import { ClipCard } from "@/components/review/ClipCard";
import { formatBytes, formatDuration } from "@/lib/utils";

export default function ProjectDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: projectId } = use(params);
  const router = useRouter();

  const [project, setProject] = useState<ProjectDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"sources" | "process" | "clips">("sources");

  // V3 Discovery & Batch Processing Settings
  const [mode, setMode] = useState<"podcast" | "viral_moments">("podcast");
  const [burnCaptions, setBurnCaptions] = useState<boolean>(true);
  const [addHookHeader, setAddHookHeader] = useState<boolean>(true);
  const [hookHeaderPosition, setHookHeaderPosition] = useState<number>(12);
  const [hookHeaderStyle, setHookHeaderStyle] = useState<string>("viral_creator");
  const [removeWatermark, setRemoveWatermark] = useState<boolean>(false);
  const [watermarkPosition, setWatermarkPosition] = useState<"top_right" | "bottom_right" | "top_left" | "bottom_left">("top_right");
  const [enhanceQuality, setEnhanceQuality] = useState<boolean>(true);
  const [removeDeadAir, setRemoveDeadAir] = useState<boolean>(true);
  const [framingMode, setFramingMode] = useState<"crop_9_16" | "blur_fit_9_16" | "original_16_9">("crop_9_16");
  const [blurRadius, setBlurRadius] = useState<number>(30);
  const [subtitlePosition, setSubtitlePosition] = useState<number>(75);
  const [targetClips, setTargetClips] = useState(20);
  const [durationPreset, setDurationPreset] = useState("30-45s");
  const [captionStyle, setCaptionStyle] = useState<CaptionStyleType>("tiktok_viral");
  const [diversityWeight, setDiversityWeight] = useState(0.35);
  const [isStartingJob, setIsStartingJob] = useState(false);

  // Deletion & Bulk actions state
  const [selectedClips, setSelectedClips] = useState<string[]>([]);
  const [bulkStyle, setBulkStyle] = useState<CaptionStyleType>("tiktok_viral");
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isExportingBatch, setIsExportingBatch] = useState(false);
  const [isDeletingProject, setIsDeletingProject] = useState(false);

  const fetchProject = async () => {
    try {
      const data = await api.getProject(projectId);
      setProject(data);
      if (data.mode === "viral_moments" || data.mode === "podcast") {
        setMode(data.mode);
      }
      if (data.clips.length > 0 && activeTab === "sources") {
        setActiveTab("clips");
      }
    } catch (err: any) {
      setError(err.message || "Failed to load project");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProject();
  }, [projectId]);

  const handleUploadSuccess = (newVideos: VideoInfo[]) => {
    if (project) {
      setProject({
        ...project,
        videos: [...newVideos, ...project.videos],
        total_videos: project.videos.length + newVideos.length,
      });
    }
  };

  const handleStartProcessing = async () => {
    if (!project || project.videos.length === 0) return;
    setIsStartingJob(true);
    try {
      const res = await api.processProject(projectId, {
        mode: mode,
        target_clips_count: targetClips,
        duration_preset: durationPreset as any,
        caption_style: burnCaptions ? captionStyle : "none",
        burn_captions: burnCaptions,
        add_hook_header: addHookHeader,
        hook_header_position: hookHeaderPosition,
        hook_header_style: hookHeaderStyle,
        remove_watermark: removeWatermark,
        watermark_position: watermarkPosition,
        enhance_quality: enhanceQuality,
        remove_dead_air: removeDeadAir,
        framing_mode: framingMode,
        blur_radius: blurRadius,
        subtitle_position: subtitlePosition,
        reframing_mode: "center_crop",
        source_diversity_weight: diversityWeight,
      });
      router.push(`/jobs/${res.job_id}`);
    } catch (err: any) {
      alert(err.message || "Failed to trigger project processing");
    } finally {
      setIsStartingJob(false);
    }
  };

  const handleBatchDownload = async () => {
    if (selectedClips.length === 0) return;
    setIsExportingBatch(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/export/clips/batch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ clip_ids: selectedClips }),
      });
      if (!res.ok) throw new Error("Bulk export download failed");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `project_${projectId.slice(0, 8)}_selected_clips_batch.zip`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(err.message || "Failed to download batch ZIP");
    } finally {
      setIsExportingBatch(false);
    }
  };



  const toggleSelectClip = (id: string) => {
    setSelectedClips((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleSelectAllClips = () => {
    if (!project) return;
    if (selectedClips.length === project.clips.length) {
      setSelectedClips([]);
    } else {
      setSelectedClips(project.clips.map((c) => c.id));
    }
  };

  const handleBulkAction = async (action: string) => {
    if (selectedClips.length === 0) return;
    if (action === "delete") {
      if (confirm(`Are you sure you want to permanently delete ${selectedClips.length} clips?`)) {
        await api.bulkDeleteClips(selectedClips);
        fetchProject();
        setSelectedClips([]);
      }
      return;
    }
    await api.bulkClipAction(projectId, selectedClips, action, bulkStyle);
    fetchProject();
    setSelectedClips([]);
  };

  const handleDeleteProject = async () => {
    setIsDeletingProject(true);
    try {
      await api.deleteProject(projectId);
      router.push("/projects");
    } catch (err: any) {
      alert(err.message || "Failed to delete project");
    } finally {
      setIsDeletingProject(false);
      setShowDeleteModal(false);
    }
  };

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-24 text-center space-y-3">
        <div className="h-8 w-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs text-zinc-400">Loading Project Studio...</p>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-16 text-center space-y-4">
        <AlertCircle className="h-10 w-10 text-rose-400 mx-auto" />
        <h2 className="text-lg font-bold text-white">Project Not Found</h2>
        <Link href="/projects" className="inline-flex items-center gap-2 text-violet-400 text-xs">
          <ArrowLeft className="h-4 w-4" /> Return to Projects
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/[0.08] pb-6">
        <div className="flex items-center gap-4">
          <Link
            href="/projects"
            className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/[0.04] border border-white/10 text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-bold text-white">{project.name}</h1>
              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${
                project.mode === "viral_moments"
                  ? "bg-amber-500/10 border border-amber-500/30 text-amber-300"
                  : "bg-violet-500/10 border border-violet-500/30 text-violet-300"
              }`}>
                {project.mode === "viral_moments" ? <Zap className="h-3 w-3" /> : <Mic className="h-3 w-3" />}
                {project.mode === "viral_moments" ? "Viral Moments" : "Podcast"}
              </span>
            </div>
            <p className="text-xs text-zinc-400 mt-0.5">
              {project.total_videos} Videos • {project.total_clips} Generated Clips
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Tab Navigation */}
          <div className="flex items-center rounded-xl bg-white/[0.03] border border-white/10 p-1">
            <button
              onClick={() => setActiveTab("sources")}
              className={`flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold transition-all ${
                activeTab === "sources"
                  ? "bg-violet-600 text-white shadow"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              <Film className="h-3.5 w-3.5" />
              <span>Sources ({project.total_videos})</span>
            </button>
            <button
              onClick={() => setActiveTab("process")}
              className={`flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold transition-all ${
                activeTab === "process"
                  ? "bg-violet-600 text-white shadow"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>Global Discovery</span>
            </button>
            <button
              onClick={() => setActiveTab("clips")}
              className={`flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold transition-all ${
                activeTab === "clips"
                  ? "bg-violet-600 text-white shadow"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              <Layers className="h-3.5 w-3.5" />
              <span>Clips ({project.total_clips})</span>
            </button>
          </div>

          {/* Delete Project Action */}
          <button
            type="button"
            onClick={() => setShowDeleteModal(true)}
            className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 hover:bg-rose-600 hover:text-white transition-all"
            title="Delete Project Workspace"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>


      {/* Tab 1: Sources & Batch Upload */}
      {activeTab === "sources" && (
        <div className="space-y-8">
          <BatchUploader
            projectId={project.id}
            onUploadSuccess={handleUploadSuccess}
          />

          <div className="space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-zinc-300">
              Source Videos in Project ({project.videos.length})
            </h3>

            {project.videos.length === 0 ? (
              <p className="text-xs text-zinc-500 italic">No videos uploaded to this project yet.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {project.videos.map((v) => (
                  <div
                    key={v.id}
                    className="flex flex-col rounded-xl border border-white/10 bg-white/[0.02] p-4 space-y-3"
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-600/10 border border-violet-500/20 text-violet-400 shrink-0">
                        <FileVideo className="h-4 w-4" />
                      </div>
                      <div className="min-w-0">
                        <h4 className="text-xs font-bold text-white truncate">{v.filename}</h4>
                        <p className="text-[11px] text-zinc-400">
                          {formatDuration(v.duration_seconds)} • {formatBytes(v.file_size_bytes)}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 text-[10px] text-zinc-500 border-t border-white/5 pt-2">
                      <span className="rounded bg-black/40 px-1.5 py-0.5">{v.width}x{v.height}</span>
                      <span className="rounded bg-black/40 px-1.5 py-0.5">{v.fps.toFixed(0)} FPS</span>
                      <span className="rounded bg-black/40 px-1.5 py-0.5">{v.video_codec}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Global AI Discovery Configuration */}
      {activeTab === "process" && (
        <div className="max-w-3xl mx-auto space-y-8 rounded-2xl border border-white/10 bg-white/[0.02] p-6 sm:p-8">
          <div className="space-y-1">
            <h2 className="text-lg font-bold text-white">Cross-Video Global Discovery</h2>
            <p className="text-xs text-zinc-400">
              Discovers candidate moments across all {project.total_videos} videos and ranks the strongest clips into a unified pool.
            </p>
          </div>

          <div className="space-y-6">
            {/* Mode Selector */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-zinc-300">Clipping Mode</label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setMode("podcast")}
                  className={`rounded-xl p-3.5 text-left border transition-all ${
                    mode === "podcast"
                      ? "bg-violet-600/20 border-violet-500 text-white"
                      : "bg-white/[0.02] border-white/10 text-zinc-400 hover:border-white/20"
                  }`}
                >
                  <div className="flex items-center gap-1.5 font-bold text-xs text-violet-300 mb-1">
                    <Mic className="h-4 w-4" /> Regular Podcast Clipper
                  </div>
                  <p className="text-[10px] text-zinc-400">Conversations, debates & advice</p>
                </button>

                <button
                  type="button"
                  onClick={() => setMode("viral_moments")}
                  className={`rounded-xl p-3.5 text-left border transition-all ${
                    mode === "viral_moments"
                      ? "bg-amber-500/20 border-amber-500 text-white"
                      : "bg-white/[0.02] border-white/10 text-zinc-400 hover:border-white/20"
                  }`}
                >
                  <div className="flex items-center gap-1.5 font-bold text-xs text-amber-300 mb-1">
                    <Zap className="h-4 w-4" /> Long Video Viral Moments
                  </div>
                  <p className="text-[10px] text-zinc-400">Documentaries, commentary & peaks</p>
                </button>
              </div>
            </div>

            {/* Subtitles & Silence Toggles */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="rounded-xl border border-white/10 bg-black/20 p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-white flex items-center gap-1.5">
                    <Subtitles className="h-3.5 w-3.5 text-violet-400" /> Burn Animated Captions
                  </span>
                  <button
                    type="button"
                    onClick={() => setBurnCaptions(!burnCaptions)}
                    className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                      burnCaptions ? "bg-violet-600" : "bg-zinc-800"
                    }`}
                  >
                    <span
                      className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                        burnCaptions ? "translate-x-4.5" : "translate-x-0.5"
                      }`}
                    />
                  </button>
                </div>
                <p className="text-[10px] text-zinc-500">
                  {burnCaptions ? "Burn styled subtitles into video." : "Clean video without burned subtitles."}
                </p>
              </div>

              <div className="rounded-xl border border-white/10 bg-black/20 p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-white flex items-center gap-1.5">
                    <Scissors className="h-3.5 w-3.5 text-amber-400" /> Cut Dead Air & Silence
                  </span>
                  <button
                    type="button"
                    onClick={() => setRemoveDeadAir(!removeDeadAir)}
                    className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                      removeDeadAir ? "bg-amber-500" : "bg-zinc-800"
                    }`}
                  >
                    <span
                      className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                        removeDeadAir ? "translate-x-4.5" : "translate-x-0.5"
                      }`}
                    />
                  </button>
                </div>
                <p className="text-[10px] text-zinc-500">
                  {removeDeadAir ? "Trim pauses >1.2s to boost retention." : "Keep uncut speech pauses."}
                </p>
              </div>
            </div>

            {/* Target Clips */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-zinc-300">Target Output Clips</span>
                <span className="font-bold text-violet-400">{targetClips} Clips</span>
              </div>
              <input
                type="range"
                min="5"
                max="50"
                step="5"
                value={targetClips}
                onChange={(e) => setTargetClips(parseInt(e.target.value))}
                className="w-full accent-violet-500 cursor-pointer"
              />
            </div>

            {/* Target Duration Preset */}
            <div className="space-y-2">
              <span className="text-xs font-semibold text-zinc-300">Duration Range</span>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {["15-30s", "30-45s", "45-60s", "60-90s"].map((d) => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => setDurationPreset(d)}
                    className={`rounded-xl px-3 py-2 text-xs font-semibold border transition-all ${
                      durationPreset === d
                        ? "bg-violet-600/20 border-violet-500 text-violet-300"
                        : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white"
                    }`}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>

            {/* Framing & Aspect Ratio */}
            <div className="space-y-3 pt-2 border-t border-white/5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-zinc-300">Framing & Aspect Ratio</span>
                <span className="text-[10px] font-mono text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
                  {framingMode === "crop_9_16" ? "9:16 Vertical Crop" : framingMode === "blur_fit_9_16" ? "16:9 Blurred Canvas" : "16:9 Landscape"}
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => setFramingMode("crop_9_16")}
                  className={`rounded-xl p-2.5 text-left border transition-all ${
                    framingMode === "crop_9_16"
                      ? "bg-violet-500/15 border-violet-400 text-white"
                      : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white"
                  }`}
                >
                  <div className="flex items-center gap-1.5">
                    <Smartphone className="h-3.5 w-3.5 text-violet-400" />
                    <p className="text-xs font-semibold">9:16 Vertical</p>
                  </div>
                  <p className="text-[10px] text-zinc-400 mt-0.5">Crop & fill canvas</p>
                </button>
                <button
                  type="button"
                  onClick={() => setFramingMode("blur_fit_9_16")}
                  className={`rounded-xl p-2.5 text-left border transition-all ${
                    framingMode === "blur_fit_9_16"
                      ? "bg-violet-500/15 border-violet-400 text-white"
                      : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white"
                  }`}
                >
                  <div className="flex items-center gap-1.5">
                    <Maximize2 className="h-3.5 w-3.5 text-cyan-400" />
                    <p className="text-xs font-semibold">16:9 Frosted Blur</p>
                  </div>
                  <p className="text-[10px] text-zinc-400 mt-0.5">Fit with canvas blur</p>
                </button>
                <button
                  type="button"
                  onClick={() => setFramingMode("original_16_9")}
                  className={`rounded-xl p-2.5 text-left border transition-all ${
                    framingMode === "original_16_9"
                      ? "bg-violet-500/15 border-violet-400 text-white"
                      : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white"
                  }`}
                >
                  <div className="flex items-center gap-1.5">
                    <Monitor className="h-3.5 w-3.5 text-emerald-400" />
                    <p className="text-xs font-semibold">16:9 Landscape</p>
                  </div>
                  <p className="text-[10px] text-zinc-400 mt-0.5">Landscape widescreen</p>
                </button>
              </div>


              {framingMode === "blur_fit_9_16" && (
                <div className="rounded-xl bg-black/40 border border-cyan-500/30 p-3 space-y-2">
                  <div className="flex items-center justify-between text-[11px] text-cyan-300 font-semibold">
                    <span>Background Blur: {blurRadius}px</span>
                    <span className="text-zinc-500 text-[10px]">35% Dimmed</span>
                  </div>
                  <input
                    type="range"
                    min={10}
                    max={80}
                    step={5}
                    value={blurRadius}
                    onChange={(e) => setBlurRadius(Number(e.target.value))}
                    className="w-full accent-cyan-400 h-1.5 bg-zinc-800 rounded-lg cursor-pointer"
                  />
                </div>
              )}
            </div>

            {/* Source Diversity Weight */}
            <div className="space-y-2">

              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-zinc-300">Source Diversity Balance</span>
                <span className="font-bold text-violet-400">{(diversityWeight * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={diversityWeight}
                onChange={(e) => setDiversityWeight(parseFloat(e.target.value))}
                className="w-full accent-violet-500 cursor-pointer"
              />
              <p className="text-[11px] text-zinc-500">
                Higher balance distributes clips evenly across videos; lower balance selects purely by highest raw score.
              </p>
            </div>

            {/* Caption Preset (only if enabled) */}
            {burnCaptions && (
              <div className="space-y-4">
                <CaptionPresetPicker
                  selected={captionStyle}
                  onChange={setCaptionStyle}
                />

                {/* Subtitle Vertical Position */}
                <div className="rounded-xl border border-white/10 bg-black/20 p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-zinc-300">Subtitle Screen Position</span>
                    <span className="text-[10px] font-mono text-violet-400 bg-violet-500/10 px-2 py-0.5 rounded border border-violet-500/20">
                      {subtitlePosition}% ({subtitlePosition <= 25 ? "Top" : subtitlePosition <= 45 ? "Upper-Mid" : subtitlePosition <= 60 ? "Center" : subtitlePosition <= 80 ? "Lower-Third" : "Bottom"})
                    </span>
                  </div>

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

                    <div className="w-9 h-14 rounded-md bg-black/80 border border-violet-500/40 relative overflow-hidden flex-shrink-0 shadow-inner">
                      <div
                        className="absolute left-1 right-1 h-1.5 bg-yellow-400 rounded-full shadow-sm shadow-yellow-400/50 transition-all duration-150"
                        style={{ top: `${subtitlePosition}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Persistent Hook Header Toggle & Position */}
            <div className="rounded-xl border border-white/10 bg-black/20 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Flame className="h-4 w-4 text-amber-400" />
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-semibold text-white">Sticky TikTok Hook Header</span>
                      <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">VIRAL CREATOR</span>
                    </div>
                    <p className="text-[10px] text-zinc-400">Keep catchy hook title with contextual emojis visible throughout entire clip</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setAddHookHeader(!addHookHeader)}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                    addHookHeader ? "bg-amber-500" : "bg-zinc-800"
                  }`}
                >
                  <span
                    className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                      addHookHeader ? "translate-x-4.5" : "translate-x-0.5"
                    }`}
                  />
                </button>
              </div>

              {addHookHeader && (
                <div className="space-y-3 pt-2 border-t border-white/5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-zinc-300">Hook Screen Position</span>
                    <span className="text-[10px] font-mono text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                      {hookHeaderPosition}% ({hookHeaderPosition <= 15 ? "Top Banner" : hookHeaderPosition <= 30 ? "Upper 3rd" : hookHeaderPosition <= 55 ? "Center" : "Bottom"})
                    </span>
                  </div>

                  <div className="grid grid-cols-4 gap-1.5">
                    {[
                      { label: "Top Banner", pos: 12 },
                      { label: "Upper 3rd", pos: 25 },
                      { label: "Center", pos: 50 },
                      { label: "Bottom", pos: 85 },
                    ].map((p) => (
                      <button
                        key={p.pos}
                        type="button"
                        onClick={() => setHookHeaderPosition(p.pos)}
                        className={`rounded-lg py-1.5 px-2 text-center text-[10px] font-medium border transition-all ${
                          hookHeaderPosition === p.pos
                            ? "bg-amber-500/25 border-amber-400 text-white shadow-sm"
                            : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white"
                        }`}
                      >
                        {p.label} ({p.pos}%)
                      </button>
                    ))}
                  </div>

                  <div className="flex items-center gap-3 pt-1">
                    <div className="flex-1 space-y-1">
                      <input
                        type="range"
                        min={8}
                        max={85}
                        step={1}
                        value={hookHeaderPosition}
                        onChange={(e) => setHookHeaderPosition(Number(e.target.value))}
                        className="w-full accent-amber-400 h-1.5 bg-zinc-800 rounded-lg cursor-pointer"
                      />
                      <div className="flex justify-between text-[9px] text-zinc-500">
                        <span>Top (8%)</span>
                        <span>Upper (25%)</span>
                        <span>Center (50%)</span>
                        <span>Bottom (85%)</span>
                      </div>
                    </div>

                    <div className="w-9 h-14 rounded-md bg-black/80 border border-amber-500/40 relative overflow-hidden flex-shrink-0 shadow-inner">
                      <div
                        className="absolute left-1 right-1 h-1.5 bg-amber-400 rounded-full shadow-sm shadow-amber-400/80 transition-all duration-150"
                        style={{ top: `${hookHeaderPosition}%` }}
                      />
                      {burnCaptions && (
                        <div
                          className="absolute left-1 right-1 h-1 bg-yellow-300/50 rounded-full transition-all duration-150"
                          style={{ top: `${subtitlePosition}%` }}
                        />
                      )}
                    </div>
                  </div>

                  {/* Hook Header Visual Style Selection */}
                  <div className="space-y-2 pt-2 border-t border-white/5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-zinc-300">Hook Visual Style & Typography</span>
                      <span className="text-[10px] text-amber-400 font-mono">
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
                            onClick={() => setHookHeaderStyle(styleOpt.id)}
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
                        {hookHeaderStyle === "white_box"
                          ? "WAIT TILL THE END"
                          : hookHeaderStyle === "meme"
                          ? "NOBODY EXPECTED THIS"
                          : hookHeaderStyle === "nostalgic"
                          ? "CHAPTER I: THE BEGINNING"
                          : hookHeaderStyle === "old_history"
                          ? "HISTORICAL CHRONICLES"
                          : hookHeaderStyle === "neon_cyber"
                          ? "FUTURE TECH REVEALED"
                          : "WHY NOBODY TALKS ABOUT THIS"}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Watermark / Logo / Trademark Eraser Toggle */}
            <div className="glass-panel rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Eraser className="h-4 w-4 text-cyan-400" />
                  <div>
                    <div className="flex items-center gap-1.5">
                      <h4 className="text-xs font-semibold text-white">Erase Watermark / Logo</h4>
                      <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">DELOGO</span>
                    </div>
                    <p className="text-[11px] text-zinc-400">Remove channel logo or watermark before clipping</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setRemoveWatermark(!removeWatermark)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    removeWatermark ? "bg-cyan-500" : "bg-zinc-800"
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      removeWatermark ? "translate-x-6" : "translate-x-1"
                    }`}
                  />
                </button>
              </div>

              {removeWatermark && (
                <div className="space-y-3 pt-2 border-t border-white/5">
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
                        onClick={() => setWatermarkPosition(pos.value as any)}
                        className={`rounded-lg py-1.5 px-2 text-center text-[10px] font-medium border transition-all ${
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

            {/* Studio Enhancement & Color Boost */}
            <div className="glass-panel rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Wand2 className="h-4 w-4 text-emerald-400" />
                  <div>
                    <div className="flex items-center gap-1.5">
                      <h4 className="text-xs font-semibold text-white">Studio Enhancement &amp; Color Boost</h4>
                      <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">AI EDITING</span>
                    </div>
                    <p className="text-[11px] text-zinc-400">Vibrant grading, mobile sharpening &amp; loudness normalization</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setEnhanceQuality(!enhanceQuality)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    enhanceQuality ? "bg-emerald-500" : "bg-zinc-800"
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      enhanceQuality ? "translate-x-6" : "translate-x-1"
                    }`}
                  />
                </button>
              </div>
            </div>

            {/* Launch Button */}
            <button
              onClick={handleStartProcessing}
              disabled={isStartingJob || project.videos.length === 0}
              className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 py-3.5 text-xs font-bold text-white shadow-lg shadow-violet-500/25 hover:from-violet-500 hover:to-indigo-500 disabled:opacity-50 transition-all"
            >
              {isStartingJob ? (
                <>
                  <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Launching Pipeline...</span>
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 fill-white" />
                  <span>Discover & Render {targetClips} {mode === "podcast" ? "Podcast" : "Viral"} Clips</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Tab 3: Project Ranked Clips & Bulk Actions */}
      {activeTab === "clips" && (
        <div className="space-y-6">
          {project.clips.length > 0 && (
            <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl bg-white/[0.02] border border-white/10 p-4">
              <div className="flex items-center gap-3">
                <button
                  onClick={handleSelectAllClips}
                  className="flex items-center gap-2 text-xs font-semibold text-zinc-300 hover:text-white"
                >
                  {selectedClips.length === project.clips.length ? (
                    <CheckSquare className="h-4 w-4 text-violet-400" />
                  ) : (
                    <Square className="h-4 w-4 text-zinc-500" />
                  )}
                  <span>Select All ({selectedClips.length}/{project.clips.length})</span>
                </button>
              </div>

              {selectedClips.length > 0 && (
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleBatchDownload}
                    disabled={isExportingBatch}
                    className="flex items-center gap-1.5 rounded-lg bg-emerald-600/20 border border-emerald-500/30 px-3 py-1.5 text-xs font-semibold text-emerald-400 hover:bg-emerald-600 hover:text-white transition-all disabled:opacity-50"
                  >
                    <Download className="h-3.5 w-3.5" />
                    {isExportingBatch ? "Packaging..." : `Bulk Download (${selectedClips.length})`}
                  </button>
                  <button
                    onClick={() => handleBulkAction("favorite")}
                    className="flex items-center gap-1.5 rounded-lg bg-white/[0.04] border border-white/10 px-3 py-1.5 text-xs font-semibold text-zinc-300 hover:text-white"
                  >
                    <Heart className="h-3.5 w-3.5 text-rose-400" /> Favorite Selected
                  </button>
                  <button
                    onClick={() => handleBulkAction("reject")}
                    className="flex items-center gap-1.5 rounded-lg bg-white/[0.04] border border-white/10 px-3 py-1.5 text-xs font-semibold text-zinc-300 hover:text-white"
                  >
                    Reject Selected
                  </button>
                  <button
                    onClick={() => handleBulkAction("delete")}
                    className="flex items-center gap-1.5 rounded-lg bg-rose-600/20 border border-rose-500/30 px-3 py-1.5 text-xs font-semibold text-rose-400 hover:bg-rose-600 hover:text-white transition-all"
                  >
                    <Trash2 className="h-3.5 w-3.5" /> Delete Selected ({selectedClips.length})
                  </button>
                </div>
              )}
            </div>
          )}

          {project.clips.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-white/15 bg-white/[0.02] p-12 text-center space-y-3">
              <Sparkles className="h-8 w-8 text-zinc-500 mx-auto" />
              <h3 className="text-sm font-semibold text-white">No Clips Generated Yet</h3>
              <p className="text-xs text-zinc-400">
                Go to the Global Discovery tab to trigger multi-video processing.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {project.clips.map((clip, idx) => (
                <div key={clip.id} className="relative group">
                  <button
                    onClick={() => toggleSelectClip(clip.id)}
                    className="absolute top-3 left-3 z-30 flex h-6 w-6 items-center justify-center rounded-md bg-black/60 backdrop-blur-sm border border-white/20 text-white"
                  >
                    {selectedClips.includes(clip.id) ? (
                      <CheckSquare className="h-4 w-4 text-violet-400" />
                    ) : (
                      <Square className="h-4 w-4 text-zinc-400" />
                    )}
                  </button>
                  <ClipCard clip={clip} rank={idx + 1} />
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Delete Project Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="relative w-full max-w-md rounded-2xl bg-zinc-900 border border-rose-500/30 p-6 shadow-2xl space-y-5">
            <div className="flex items-center gap-3 text-rose-400">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500/10 border border-rose-500/20">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Delete Workspace?</h3>
                <p className="text-xs text-zinc-400">This action will delete "{project.name}".</p>
              </div>
            </div>

            <p className="text-xs text-zinc-300 leading-relaxed">
              All {project.total_videos} videos, transcripts, AI candidate pools, and {project.total_clips} generated clips will be permanently removed.
            </p>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowDeleteModal(false)}
                className="rounded-xl px-4 py-2 text-xs font-semibold text-zinc-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isDeletingProject}
                onClick={handleDeleteProject}
                className="flex items-center gap-2 rounded-xl bg-rose-600 px-5 py-2.5 text-xs font-semibold text-white hover:bg-rose-500 disabled:opacity-50 transition-all"
              >
                <Trash2 className="h-3.5 w-3.5" />
                <span>{isDeletingProject ? "Deleting..." : "Confirm & Delete Project"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

