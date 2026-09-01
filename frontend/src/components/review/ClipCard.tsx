"use client";

import Link from "next/link";
import { useState } from "react";
import { Play, Heart, Zap, Award, Sparkles, Mic, Subtitles, Scissors, Download } from "lucide-react";



import { RenderedClipResponse } from "@/lib/types";
import { api } from "@/lib/api";

interface ClipCardProps {
  clip: RenderedClipResponse;
  rank: number;
}

export function ClipCard({ clip, rank }: ClipCardProps) {
  const [isFav, setIsFav] = useState(clip.is_favorite);

  const handleFavoriteToggle = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      const res = await api.toggleFavorite(clip.id);
      setIsFav(res.is_favorite);
    } catch {
      // ignore
    }
  };

  const deadAirSec = clip.timeline_edit?.dead_air_removed_seconds || 0;

  return (
    <div className="group relative overflow-hidden rounded-2xl glass-panel glass-panel-hover flex flex-col justify-between">
      {/* Thumbnail & Video Preview Area */}
      <Link href={`/clips/${clip.id}`} className="block relative aspect-[9/16] bg-black/60 overflow-hidden">
        {clip.thumbnail_url ? (
          <img
            src={clip.thumbnail_url}
            alt={clip.hook_text || "Clip preview"}
            className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="h-full w-full flex items-center justify-center text-zinc-600 bg-zinc-900">
            <Play className="h-10 w-10 opacity-40" />
          </div>
        )}

        {/* Gradient overlay on hover */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/30 opacity-60 group-hover:opacity-80 transition-opacity" />

        {/* Top Badges: Rank & Score */}
        <div className="absolute top-3 left-3 right-3 flex items-center justify-between z-10">
          <div className="flex items-center gap-1.5">
            <span className="rounded-md bg-zinc-950/80 backdrop-blur-md border border-white/10 px-2 py-0.5 text-[10px] font-bold text-zinc-300 font-mono">
              #{rank}
            </span>
            <span className="rounded-md bg-zinc-900/90 backdrop-blur-md border border-white/10 px-2 py-0.5 text-[10px] font-semibold text-zinc-300 uppercase tracking-wider">
              {clip.mode === "viral_moments" ? "Viral Hook" : "Context Unit"}
            </span>
          </div>

          <div className="flex items-center gap-1 rounded-md bg-violet-600/90 backdrop-blur-md border border-violet-400/30 px-2 py-0.5 text-[11px] font-bold text-white shadow-md">
            <span>{clip.scores.composite_score.toFixed(0)}</span>
            <span className="text-[9px] text-violet-200 font-mono">PTS</span>
          </div>
        </div>


        {/* Favorite & Quick Download Buttons */}
        <div className="absolute bottom-3 right-3 z-10 flex items-center gap-1.5">
          <a
            href={api.getDirectMp4Url(clip.id)}
            download
            onClick={(e) => e.stopPropagation()}
            className="flex h-8 w-8 items-center justify-center rounded-full bg-black/60 backdrop-blur-md border border-white/20 text-zinc-300 hover:text-white hover:bg-violet-600/80 transition-all"
            title="Download MP4 Video"
          >
            <Download className="h-3.5 w-3.5" />
          </a>

          <button
            onClick={handleFavoriteToggle}
            className={`flex h-8 w-8 items-center justify-center rounded-full backdrop-blur-md border transition-all ${
              isFav
                ? "bg-rose-500 border-rose-400 text-white"
                : "bg-black/60 border-white/20 text-zinc-300 hover:text-white hover:bg-black/80"
            }`}
            title={isFav ? "Favorited" : "Add to Favorites"}
          >
            <Heart className={`h-3.5 w-3.5 ${isFav ? "fill-white" : ""}`} />
          </button>
        </div>


        {/* Play Icon on Hover */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-violet-600/90 text-white shadow-xl">
            <Play className="h-6 w-6 ml-0.5" />
          </div>
        </div>

        {/* Bottom Feature Badges */}
        <div className="absolute bottom-3 left-3 z-10 flex items-center gap-1.5">
          <span className="rounded-md bg-black/70 backdrop-blur-md px-2 py-0.5 text-[10px] font-mono text-zinc-300">
            {clip.duration.toFixed(1)}s
          </span>
          {deadAirSec > 0.5 && (
            <span className="rounded-md bg-amber-500/80 backdrop-blur-md px-1.5 py-0.5 text-[9px] font-bold text-black flex items-center gap-0.5" title={`Trimmed ${deadAirSec.toFixed(1)}s dead air`}>
              <Scissors className="h-2.5 w-2.5" /> -{deadAirSec.toFixed(1)}s
            </span>
          )}
          {clip.burn_captions && (
            <span className="rounded-md bg-violet-500/80 backdrop-blur-md px-1.5 py-0.5 text-[9px] font-bold text-white flex items-center gap-0.5" title="Burned-in Captions">
              <Subtitles className="h-2.5 w-2.5" /> CC
            </span>
          )}
        </div>
      </Link>

      {/* Info & Metadata */}
      <div className="p-4 space-y-3">
        <Link href={`/clips/${clip.id}`}>
          <h4 className="font-semibold text-sm text-white line-clamp-2 hover:text-violet-400 transition-colors">
            {clip.hook_text || clip.metadata.tiktok_title || "High-Impact Short Clip"}
          </h4>
        </Link>

        <div className="flex items-center justify-between text-xs text-zinc-400 pt-2 border-t border-white/[0.06]">
          <div className="flex items-center gap-1 text-amber-400">
            <Zap className="h-3 w-3" />
            <span className="font-medium">Hook: {clip.scores.hook_score.toFixed(0)}</span>
          </div>

          <div className="flex items-center gap-1 text-violet-400">
            <Award className="h-3 w-3" />
            <span className="font-medium">Payoff: {clip.scores.payoff_score.toFixed(0)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
