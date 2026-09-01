"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Heart,
  Download,
  Share2,
  Sparkles,
  Award,
  Zap,
  AlertCircle,
  FileVideo,
  RefreshCw,
  ThumbsDown,
} from "lucide-react";
import { api } from "@/lib/api";
import { RenderedClipResponse } from "@/lib/types";
import { ClipPlayer } from "@/components/review/ClipPlayer";
import { TimelineScrubber } from "@/components/review/TimelineScrubber";
import { ScoreRadar } from "@/components/review/ScoreRadar";
import { PlatformMetadataCard } from "@/components/review/PlatformMetadataCard";
import { RegenerateModal } from "@/components/review/RegenerateModal";

export default function ClipDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const clipId = resolvedParams.id;

  const [clip, setClip] = useState<RenderedClipResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRegenerateOpen, setIsRegenerateOpen] = useState(false);

  const fetchClip = async () => {
    try {
      const data = await api.getClip(clipId);
      setClip(data);
    } catch (err: any) {
      setError(err.message || "Failed to load clip details");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchClip();
  }, [clipId]);

  const handleFavoriteToggle = async () => {
    if (!clip) return;
    try {
      const res = await api.toggleFavorite(clip.id);
      setClip({ ...clip, is_favorite: res.is_favorite });
    } catch {
      // ignore
    }
  };

  const handleReject = async () => {
    if (!clip) return;
    try {
      await api.submitFeedback(clip.id, "rejected");
      setClip({ ...clip, is_rejected: true });
    } catch {
      // ignore
    }
  };

  const handleRerender = async (startTime: number, endTime: number, framingMode?: string, blurRadius?: number, subtitlePosition?: number) => {
    if (!clip) return;
    const updated = await api.rerenderClip(clip.id, {
      start_time: startTime,
      end_time: endTime,
      framing_mode: framingMode,
      blur_radius: blurRadius,
      subtitle_position: subtitlePosition,
    });
    setClip(updated);
  };



  const handleRegenerate = async (intent: string, captionStyle?: string, note?: string) => {
    if (!clip) return;
    const updated = await api.regenerateClip(clip.id, {
      intent,
      caption_style: captionStyle,
      custom_note: note,
    });
    setClip(updated);
  };

  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-24 text-center space-y-4">
        <div className="h-10 w-10 border-2 border-violet-500 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-zinc-400 text-sm font-medium">Loading Clip Review Workstation...</p>
      </div>
    );
  }

  if (error || !clip) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-16 text-center space-y-4">
        <AlertCircle className="h-12 w-12 text-rose-400 mx-auto" />
        <h2 className="text-xl font-bold text-white">Clip Not Found</h2>
        <p className="text-zinc-400 text-sm">{error || "Could not retrieve clip data."}</p>
        <Link href="/" className="inline-flex items-center gap-2 text-violet-400 hover:text-violet-300 text-sm">
          <ArrowLeft className="h-4 w-4" /> Return to Home
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      {/* Top Navigation & Actions Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/[0.08] pb-6">
        <div className="flex items-center gap-4">
          <Link
            href={`/jobs/${clip.job_id}`}
            className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/[0.04] border border-white/10 text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg sm:text-xl font-bold text-white line-clamp-1">
                {clip.hook_text || clip.metadata.tiktok_title || "Clip Review Workstation"}
              </h1>
              <span className="rounded-md bg-violet-600/20 border border-violet-500/30 px-2 py-0.5 text-xs font-bold text-violet-300">
                Score {clip.scores.composite_score.toFixed(0)}
              </span>
            </div>
            <p className="text-xs text-zinc-400">
              9:16 Vertical Short • {clip.duration.toFixed(1)}s duration ({clip.start_time.toFixed(1)}s - {clip.end_time.toFixed(1)}s)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsRegenerateOpen(true)}
            className="flex items-center gap-1.5 rounded-xl bg-white/[0.04] border border-white/10 px-4 py-2 text-xs font-semibold text-zinc-200 hover:text-white hover:bg-white/10 transition-all"
          >
            <Sparkles className="h-4 w-4 text-violet-400" />
            <span>Regenerate with AI</span>
          </button>

          <button
            onClick={handleFavoriteToggle}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold border transition-all ${
              clip.is_favorite
                ? "bg-rose-500/20 border-rose-500/50 text-rose-300"
                : "bg-white/[0.03] border-white/10 text-zinc-400 hover:text-white"
            }`}
          >
            <Heart className={`h-4 w-4 ${clip.is_favorite ? "fill-rose-400 text-rose-400" : ""}`} />
            <span>{clip.is_favorite ? "Favorited" : "Favorite"}</span>
          </button>

          <button
            onClick={handleReject}
            className={`flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-semibold border transition-all ${
              clip.is_rejected
                ? "bg-zinc-800 border-zinc-700 text-zinc-500 line-through"
                : "bg-white/[0.03] border-white/10 text-zinc-400 hover:text-rose-400"
            }`}
          >
            <ThumbsDown className="h-3.5 w-3.5" />
          </button>

          <a
            href={api.getDirectMp4Url(clip.id)}
            download
            className="flex items-center gap-2 rounded-xl bg-emerald-600/20 border border-emerald-500/40 px-4 py-2 text-xs font-semibold text-emerald-300 hover:bg-emerald-600 hover:text-white transition-all shadow-md shadow-emerald-500/10"
          >
            <Download className="h-4 w-4" />
            <span>Download MP4</span>
          </a>

          <a
            href={api.getSingleExportUrl(clip.id)}
            download
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-violet-500/20 hover:from-violet-500 hover:to-indigo-500 transition-all"
          >
            <Download className="h-4 w-4" />
            <span>Export Package (.ZIP)</span>
          </a>
        </div>
      </div>


      {/* Dual Pane Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: 9:16 Video Player */}
        <div className="lg:col-span-5 flex flex-col items-center">
          <div className="sticky top-24 w-full flex flex-col items-center">
            <ClipPlayer
              videoUrl={clip.video_url}
              thumbnailUrl={clip.thumbnail_url}
              duration={clip.duration}
            />
          </div>
        </div>

        {/* Right Column: Workstation Controls & Analytics */}
        <div className="lg:col-span-7 space-y-6">
          {/* Timeline Re-trimmer & Framing Selector */}
          <TimelineScrubber
            initialStart={clip.start_time}
            initialEnd={clip.end_time}
            maxVideoDuration={clip.end_time + 60.0}
            initialFramingMode={clip.framing_mode}
            initialBlurRadius={clip.blur_radius}
            initialSubtitlePosition={clip.subtitle_position}
            onRerender={handleRerender}
          />


          {/* 12-Dimensional Score Breakdown */}
          <ScoreRadar
            scores={clip.scores}
            reason={clip.reason}
          />

          {/* Platform Metadata & Copy */}
          <PlatformMetadataCard
            metadata={clip.metadata}
            clipId={clip.id}
          />
        </div>
      </div>

      {/* Regeneration Modal */}
      <RegenerateModal
        isOpen={isRegenerateOpen}
        onClose={() => setIsRegenerateOpen(false)}
        onRegenerate={handleRegenerate}
        currentStyle={clip.caption_style}
      />
    </div>
  );
}
