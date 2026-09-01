"use client";

import { useState, useRef } from "react";
import {
  Upload,
  Film,
  CheckCircle2,
  AlertCircle,
  X,
  FileVideo,
  Layers,
  ArrowUpRight,
} from "lucide-react";
import { formatBytes, formatDuration } from "@/lib/utils";
import { api } from "@/lib/api";
import { VideoInfo } from "@/lib/types";

interface BatchUploaderProps {
  projectId: string;
  onUploadSuccess: (videos: VideoInfo[]) => void;
}

interface QueuedFile {
  id: string;
  file: File;
  progress: number;
  status: "idle" | "uploading" | "done" | "error";
  error?: string;
}

export function BatchUploader({ projectId, onUploadSuccess }: BatchUploaderProps) {
  const [queue, setQueue] = useState<QueuedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = (files: FileList | null) => {
    if (!files) return;
    const newItems: QueuedFile[] = Array.from(files).map((f) => ({
      id: Math.random().toString(36).substring(2, 9),
      file: f,
      progress: 0,
      status: "idle",
    }));
    setQueue((prev) => [...prev, ...newItems]);
  };

  const removeFile = (id: string) => {
    setQueue((prev) => prev.filter((item) => item.id !== id));
  };

  const startBatchUpload = async () => {
    if (queue.length === 0 || isUploading) return;
    setIsUploading(true);

    try {
      // Mark all as uploading
      setQueue((prev) => prev.map((q) => ({ ...q, status: "uploading", progress: 45 })));
      const rawFiles = queue.map((q) => q.file);
      const res = await api.batchUploadVideos(projectId, rawFiles);

      setQueue((prev) => prev.map((q) => ({ ...q, status: "done", progress: 100 })));
      onUploadSuccess(res.uploaded_videos);
    } catch (err: any) {
      setQueue((prev) =>
        prev.map((q) => ({
          ...q,
          status: "error",
          error: err.message || "Upload failed",
        }))
      );
    } finally {
      setIsUploading(false);
    }
  };

  const totalBytes = queue.reduce((acc, q) => acc + q.file.size, 0);

  return (
    <div className="space-y-6">
      {/* Drop Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragOver(false);
          handleFiles(e.dataTransfer.files);
        }}
        onClick={() => fileInputRef.current?.click()}
        className={`relative cursor-pointer rounded-2xl border-2 border-dashed p-8 text-center transition-all duration-300 ${
          isDragOver
            ? "border-violet-500 bg-violet-500/10 scale-[1.01]"
            : "border-white/15 bg-white/[0.02] hover:border-violet-500/50 hover:bg-white/[0.04]"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="video/mp4,video/quicktime,video/x-matroska,video/webm"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />

        <div className="flex flex-col items-center gap-3">
          <div className="relative group/emblem">
            <div className="absolute -inset-1.5 rounded-2xl bg-gradient-to-r from-violet-600 via-indigo-600 to-cyan-500 opacity-30 blur group-hover/emblem:opacity-60 transition duration-300" />
            <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-[#101322] border border-violet-500/30 p-2 shadow-xl group-hover/emblem:scale-105 transition-transform duration-300">
              <img src="/logo.svg" alt="Clipper Pro" className="w-full h-full" />
            </div>
          </div>
          <div className="space-y-1">
            <p className="text-base font-bold text-white">
              Drop 20–30+ Videos or <span className="text-violet-400 underline underline-offset-4">Browse Files</span>
            </p>
            <p className="text-xs text-slate-400">
              Supports MP4, MOV, MKV, WebM up to 2GB per video • Global Cross-Video Ranking
            </p>
          </div>
        </div>
      </div>


      {/* Queued Videos List */}
      {queue.length > 0 && (
        <div className="space-y-4 rounded-2xl border border-white/10 bg-white/[0.02] p-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Film className="h-4 w-4 text-violet-400" />
              <span className="text-sm font-semibold text-white">
                Queued Files ({queue.length}) • {formatBytes(totalBytes)}
              </span>
            </div>
            <button
              onClick={startBatchUpload}
              disabled={isUploading}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 px-5 py-2 text-xs font-semibold text-white shadow-lg shadow-violet-500/20 hover:from-violet-500 hover:to-indigo-500 disabled:opacity-50 transition-all"
            >
              {isUploading ? (
                <>
                  <div className="h-3 w-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Uploading {queue.length} Videos...</span>
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4" />
                  <span>Upload All ({queue.length} Videos)</span>
                </>
              )}
            </button>
          </div>

          <div className="max-h-60 overflow-y-auto space-y-2 pr-1">
            {queue.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between rounded-xl bg-black/40 border border-white/5 px-4 py-2.5"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <FileVideo className="h-4 w-4 text-zinc-400 shrink-0" />
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-white truncate max-w-md">
                      {item.file.name}
                    </p>
                    <p className="text-[10px] text-zinc-500">
                      {formatBytes(item.file.size)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {item.status === "done" && (
                    <span className="flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
                      <CheckCircle2 className="h-3.5 w-3.5" /> Uploaded
                    </span>
                  )}
                  {item.status === "error" && (
                    <span className="flex items-center gap-1 text-[11px] text-rose-400 font-medium">
                      <AlertCircle className="h-3.5 w-3.5" /> {item.error}
                    </span>
                  )}
                  {!isUploading && item.status !== "done" && (
                    <button
                      onClick={() => removeFile(item.id)}
                      className="text-zinc-500 hover:text-zinc-300"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
