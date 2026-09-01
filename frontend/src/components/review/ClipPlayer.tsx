"use client";

import { useEffect, useRef, useState } from "react";
import {
  Play,
  Pause,
  RotateCcw,
  Volume2,
  VolumeX,
  Maximize2,
  Smartphone,
  Eye,
  EyeOff,
  Heart,
  MessageCircle,
  Share2,
  Search,
  Music,
} from "lucide-react";

import { formatTimecode } from "@/lib/utils";

interface ClipPlayerProps {
  videoUrl: string;
  thumbnailUrl?: string | null;
  onTimeUpdate?: (currentTime: number) => void;
  duration?: number;
}

export function ClipPlayer({ videoUrl, thumbnailUrl, onTimeUpdate, duration }: ClipPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [totalDuration, setTotalDuration] = useState(duration || 0);
  const [isMuted, setIsMuted] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [isLooping, setIsLooping] = useState(true);
  const [showPlatformOverlay, setShowPlatformOverlay] = useState(false);
  const [activePlatform, setActivePlatform] = useState<"tiktok" | "reels" | "shorts">("tiktok");

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleTimeUpdate = () => {
    if (!videoRef.current) return;
    const curr = videoRef.current.currentTime;
    setCurrentTime(curr);
    if (onTimeUpdate) onTimeUpdate(curr);
  };

  const handleLoadedMetadata = () => {
    if (!videoRef.current) return;
    setTotalDuration(videoRef.current.duration);
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!videoRef.current) return;
    const time = Number(e.target.value);
    videoRef.current.currentTime = time;
    setCurrentTime(time);
  };

  const toggleMute = () => {
    if (!videoRef.current) return;
    videoRef.current.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const cycleSpeed = () => {
    if (!videoRef.current) return;
    const speeds = [1, 1.25, 1.5, 2];
    const nextIdx = (speeds.indexOf(playbackRate) + 1) % speeds.length;
    const nextSpeed = speeds[nextIdx];
    videoRef.current.playbackRate = nextSpeed;
    setPlaybackRate(nextSpeed);
  };

  return (
    <div className="flex flex-col items-center space-y-4">
      {/* 9:16 Video Player Frame */}
      <div className="relative group overflow-hidden rounded-3xl border-2 border-white/10 bg-black shadow-2xl video-container-9-16 flex items-center justify-center">
        <video
          ref={videoRef}
          src={videoUrl}
          poster={thumbnailUrl || undefined}
          loop={isLooping}
          playsInline
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
          onEnded={() => setIsPlaying(false)}
          onClick={togglePlay}
          className="h-full w-full object-cover cursor-pointer"
        />

        {/* Simulated Platform Safe-Zone Overlays */}
        {showPlatformOverlay && (
          <div className="absolute inset-0 pointer-events-none z-20 flex flex-col justify-between p-4">
            {/* Top area header safe-zone */}
            <div className="flex justify-between items-center text-[10px] text-white/70 font-semibold px-2">
              <span>LIVE</span>
              <span>Following | <strong className="text-white">For You</strong></span>
              <Search className="h-3.5 w-3.5 text-white/80" />
            </div>

            {/* Right-side action buttons */}
            <div className="self-end space-y-4 text-center pr-1 text-white/90">
              <div className="flex flex-col items-center gap-1">
                <div className="h-9 w-9 rounded-full bg-black/40 backdrop-blur-md flex items-center justify-center border border-white/10">
                  <Heart className="h-5 w-5 text-white fill-white/80" />
                </div>
                <span className="text-[10px] font-bold">142K</span>
              </div>
              <div className="flex flex-col items-center gap-1">
                <div className="h-9 w-9 rounded-full bg-black/40 backdrop-blur-md flex items-center justify-center border border-white/10">
                  <MessageCircle className="h-5 w-5 text-white" />
                </div>
                <span className="text-[10px] font-bold">1.8K</span>
              </div>
              <div className="flex flex-col items-center gap-1">
                <div className="h-9 w-9 rounded-full bg-black/40 backdrop-blur-md flex items-center justify-center border border-white/10">
                  <Share2 className="h-5 w-5 text-white" />
                </div>
                <span className="text-[10px] font-bold">24K</span>
              </div>
            </div>

            {/* Bottom title & sound area */}
            <div className="space-y-1.5 px-2 pb-2">
              <p className="text-xs font-bold text-white">@creator_channel</p>
              <p className="text-[11px] text-white/90 line-clamp-2">
                The high-retention hook strategy for short-form video discovery
              </p>
              <div className="flex items-center gap-1.5 text-[10px] text-white/60">
                <Music className="h-3 w-3" />
                <span>Original Audio Track</span>
              </div>
            </div>
          </div>

        )}

        {/* Big Center Play Overlay Button */}
        {!isPlaying && (
          <button
            onClick={togglePlay}
            className="absolute z-30 flex h-16 w-16 items-center justify-center rounded-full bg-violet-600/90 text-white backdrop-blur-md shadow-2xl transition-transform duration-200 hover:scale-110 active:scale-95"
          >
            <Play className="h-8 w-8 ml-1" />
          </button>
        )}
      </div>

      {/* Player Controls Bar */}
      <div className="w-full max-w-sm glass-panel rounded-2xl p-4 space-y-3">
        {/* Scrubber Range */}
        <div className="space-y-1">
          <input
            type="range"
            min={0}
            max={totalDuration || 100}
            step={0.1}
            value={currentTime}
            onChange={handleSeek}
            className="w-full accent-violet-500 h-1.5 bg-zinc-800 rounded-lg cursor-pointer"
          />
          <div className="flex justify-between text-[11px] font-mono text-zinc-400">
            <span>{formatTimecode(currentTime)}</span>
            <span>{formatTimecode(totalDuration)}</span>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={togglePlay}
              className="rounded-lg p-2 text-zinc-300 hover:text-white hover:bg-white/10 transition-colors"
            >
              {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            </button>
            <button
              onClick={toggleMute}
              className="rounded-lg p-2 text-zinc-300 hover:text-white hover:bg-white/10 transition-colors"
            >
              {isMuted ? <VolumeX className="h-4 w-4 text-rose-400" /> : <Volume2 className="h-4 w-4" />}
            </button>
            <button
              onClick={cycleSpeed}
              className="rounded-lg px-2 py-1 text-xs font-semibold text-zinc-300 hover:text-white hover:bg-white/10 transition-colors"
            >
              {playbackRate}x
            </button>
          </div>

          <div className="flex items-center gap-1.5">
            {/* Safe-zone overlay toggle */}
            <button
              onClick={() => setShowPlatformOverlay(!showPlatformOverlay)}
              className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium border transition-all ${
                showPlatformOverlay
                  ? "bg-violet-600/20 border-violet-500 text-violet-300"
                  : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white"
              }`}
            >
              <Smartphone className="h-3.5 w-3.5" />
              <span>Safe-Zone</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
