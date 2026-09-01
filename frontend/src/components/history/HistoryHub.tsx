"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Film,
  Sparkles,
  Layers,
  Download,
  Trash2,
  ExternalLink,
  CheckCircle2,
  Clock,
  AlertCircle,
  Play,
  Heart,
  Search,
  Filter,
  CheckSquare,
  Square,
  Mic,
  Zap,
  RefreshCw,
  Eye,
  Sliders,
} from "lucide-react";
import { api } from "@/lib/api";
import { JobStatusResponse, RenderedClipResponse } from "@/lib/types";
import { ClipCard } from "@/components/review/ClipCard";
import { formatDuration } from "@/lib/utils";

export function HistoryHub() {
  const [activeTab, setActiveTab] = useState<"clips" | "jobs">("clips");
  const [clips, setClips] = useState<RenderedClipResponse[]>([]);
  const [jobs, setJobs] = useState<JobStatusResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Filter & Search
  const [searchQuery, setSearchQuery] = useState("");
  const [modeFilter, setModeFilter] = useState<"all" | "podcast" | "viral_moments">("all");
  const [favoriteOnly, setFavoriteOnly] = useState(false);

  // Multi-select for clips
  const [selectedClipIds, setSelectedClipIds] = useState<string[]>([]);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchHistory = async () => {
    setIsLoading(true);
    try {
      const [clipsData, jobsData] = await Promise.all([
        api.listAllClips({ limit: 100 }).catch(() => []),
        api.listAllJobs(50).catch(() => []),
      ]);
      setClips(clipsData);
      setJobs(jobsData);
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  // Filtered clips
  const filteredClips = clips.filter((c) => {
    if (favoriteOnly && !c.is_favorite) return false;
    if (modeFilter !== "all" && c.mode !== modeFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchHook = c.hook_text?.toLowerCase().includes(q);
      const matchReason = c.reason?.toLowerCase().includes(q);
      const matchTiktok = c.metadata?.tiktok_title?.toLowerCase().includes(q);
      const matchShorts = c.metadata?.shorts_title?.toLowerCase().includes(q);
      if (!matchHook && !matchReason && !matchTiktok && !matchShorts) return false;
    }
    return true;
  });

  const toggleSelectClip = (id: string) => {
    setSelectedClipIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const toggleSelectAllClips = () => {
    if (selectedClipIds.length === filteredClips.length) {
      setSelectedClipIds([]);
    } else {
      setSelectedClipIds(filteredClips.map((c) => c.id));
    }
  };

  const handleDeleteClip = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    if (!confirm("Are you sure you want to permanently delete this clip?")) return;
    try {
      await api.deleteClip(id);
      setClips((prev) => prev.filter((c) => c.id !== id));
      setSelectedClipIds((prev) => prev.filter((i) => i !== id));
    } catch (err: any) {
      alert(err.message || "Failed to delete clip");
    }
  };

  const handleBulkDeleteClips = async () => {
    if (selectedClipIds.length === 0) return;
    if (!confirm(`Permanently delete ${selectedClipIds.length} selected clips?`)) return;
    setIsDeleting(true);
    try {
      await api.bulkDeleteClips(selectedClipIds);
      setClips((prev) => prev.filter((c) => !selectedClipIds.includes(c.id)));
      setSelectedClipIds([]);
    } catch (err: any) {
      alert(err.message || "Failed to delete clips");
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDeleteJob = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    if (!confirm("Are you sure you want to delete this job and its generated clips?")) return;
    try {
      await api.deleteJob(id);
      setJobs((prev) => prev.filter((j) => j.id !== id));
      // Refresh clips too
      api.listAllClips({ limit: 100 }).then(setClips).catch(() => {});
    } catch (err: any) {
      alert(err.message || "Failed to delete job");
    }
  };

  const [isExportingBulk, setIsExportingBulk] = useState(false);

  const handleBulkDownloadClips = async () => {
    if (selectedClipIds.length === 0) return;
    setIsExportingBulk(true);
    try {
      const blob = await api.downloadSelectedClipsZip(selectedClipIds);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `clips_batch_${selectedClipIds.length}_clips.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      alert(err.message || "Failed to download selected clips ZIP");
    } finally {
      setIsExportingBulk(false);
    }
  };

  return (
    <div className="space-y-6 pt-10 border-t border-white/[0.08]">
      {/* Header & Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Film className="h-5 w-5 text-violet-400" />
            <h2 className="text-xl font-bold text-white">History & Saved Library</h2>
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            Preserved historical clips, batch exports, and 21-stage pipeline execution runs
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchHistory}
            className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/[0.04] border border-white/10 text-zinc-400 hover:text-white transition-colors"
            title="Refresh History"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          </button>

          <div className="flex items-center rounded-xl bg-white/[0.03] border border-white/10 p-1">
            <button
              onClick={() => setActiveTab("clips")}
              className={`flex items-center gap-2 rounded-lg px-4 py-1.5 text-xs font-semibold transition-all ${
                activeTab === "clips"
                  ? "bg-violet-600 text-white shadow"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>Extracted Clips ({clips.length})</span>
            </button>

            <button
              onClick={() => setActiveTab("jobs")}
              className={`flex items-center gap-2 rounded-lg px-4 py-1.5 text-xs font-semibold transition-all ${
                activeTab === "jobs"
                  ? "bg-violet-600 text-white shadow"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              <Clock className="h-3.5 w-3.5" />
              <span>Pipeline Jobs ({jobs.length})</span>
            </button>
          </div>
        </div>
      </div>

      {/* TAB 1: EXTRACTED CLIPS LIBRARY */}
      {activeTab === "clips" && (
        <div className="space-y-6">
          {/* Filter Bar */}
          <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 rounded-2xl bg-white/[0.02] border border-white/10 p-4">
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-3 h-4 w-4 text-zinc-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search clips by hook line, title, or topic..."
                className="w-full rounded-xl bg-black/40 border border-white/10 pl-10 pr-4 py-2 text-xs text-white placeholder-zinc-500 focus:border-violet-500 focus:outline-none"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {/* Mode filter */}
              <div className="flex items-center rounded-xl bg-black/40 border border-white/10 p-1">
                <button
                  onClick={() => setModeFilter("all")}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                    modeFilter === "all" ? "bg-white/10 text-white" : "text-zinc-400 hover:text-white"
                  }`}
                >
                  All Modes
                </button>
                <button
                  onClick={() => setModeFilter("podcast")}
                  className={`flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                    modeFilter === "podcast" ? "bg-violet-600/30 text-violet-300" : "text-zinc-400 hover:text-white"
                  }`}
                >
                  <Mic className="h-3 w-3" /> Podcast
                </button>
                <button
                  onClick={() => setModeFilter("viral_moments")}
                  className={`flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                    modeFilter === "viral_moments" ? "bg-amber-500/30 text-amber-300" : "text-zinc-400 hover:text-white"
                  }`}
                >
                  <Zap className="h-3 w-3" /> Viral
                </button>
              </div>

              {/* Favorites toggle */}
              <button
                onClick={() => setFavoriteOnly(!favoriteOnly)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all ${
                  favoriteOnly
                    ? "bg-rose-500/20 border-rose-500/40 text-rose-300"
                    : "bg-black/40 border-white/10 text-zinc-400 hover:text-white"
                }`}
              >
                <Heart className={`h-3.5 w-3.5 ${favoriteOnly ? "fill-rose-400 text-rose-400" : ""}`} />
                <span>Favorites</span>
              </button>
            </div>
          </div>

          {/* Bulk Selection Bar */}
          {filteredClips.length > 0 && (
            <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-zinc-400 px-1">
              <button
                onClick={toggleSelectAllClips}
                className="flex items-center gap-2 font-medium hover:text-white transition-colors"
              >
                {selectedClipIds.length === filteredClips.length ? (
                  <CheckSquare className="h-4 w-4 text-violet-400" />
                ) : (
                  <Square className="h-4 w-4 text-zinc-600" />
                )}
                <span>Select All ({selectedClipIds.length}/{filteredClips.length})</span>
              </button>

              {selectedClipIds.length > 0 && (
                <div className="flex items-center gap-2 animate-in fade-in">
                  <button
                    onClick={handleBulkDownloadClips}
                    disabled={isExportingBulk}
                    className="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-violet-600 to-indigo-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow-md shadow-violet-500/20 hover:from-violet-500 hover:to-indigo-500 transition-all disabled:opacity-50"
                  >
                    <Download className="h-3.5 w-3.5" />
                    <span>{isExportingBulk ? "Zipping..." : `Download Selected (${selectedClipIds.length}) ZIP`}</span>
                  </button>

                  <button
                    onClick={handleBulkDeleteClips}
                    disabled={isDeleting}
                    className="flex items-center gap-1.5 rounded-lg bg-rose-600/20 border border-rose-500/30 px-3 py-1.5 text-xs font-semibold text-rose-400 hover:bg-rose-600 hover:text-white transition-all disabled:opacity-50"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    <span>Delete Selected ({selectedClipIds.length})</span>
                  </button>
                </div>
              )}
            </div>
          )}


          {/* Clips Grid */}
          {isLoading ? (
            <div className="py-16 text-center space-y-3">
              <div className="h-8 w-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-xs text-zinc-400">Loading clips history...</p>
            </div>
          ) : filteredClips.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-white/15 bg-white/[0.02] p-12 text-center space-y-3">
              <Film className="h-8 w-8 text-zinc-500 mx-auto" />
              <h3 className="text-sm font-semibold text-white">No Clips Found</h3>
              <p className="text-xs text-zinc-400 max-w-sm mx-auto">
                {searchQuery || favoriteOnly || modeFilter !== "all"
                  ? "No clips match your active search or filters."
                  : "Upload a video above or batch process a project to generate vertical clips."}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {filteredClips.map((clip, idx) => {
                const isSelected = selectedClipIds.includes(clip.id);
                return (
                  <div key={clip.id} className="relative group">
                    {/* Top Checkbox & Delete Overlay */}
                    <div className="absolute top-3 left-3 right-3 z-30 flex items-center justify-between pointer-events-none">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleSelectClip(clip.id);
                        }}
                        className="pointer-events-auto flex h-6 w-6 items-center justify-center rounded-md bg-black/70 backdrop-blur-sm border border-white/20 text-white hover:border-violet-500 transition-all"
                      >
                        {isSelected ? (
                          <CheckSquare className="h-4 w-4 text-violet-400" />
                        ) : (
                          <Square className="h-4 w-4 text-zinc-400" />
                        )}
                      </button>

                      <button
                        type="button"
                        onClick={(e) => handleDeleteClip(clip.id, e)}
                        className="pointer-events-auto flex h-6 w-6 items-center justify-center rounded-md bg-black/70 backdrop-blur-sm border border-white/20 text-zinc-400 hover:text-rose-400 hover:border-rose-500/50 transition-all opacity-0 group-hover:opacity-100"
                        title="Delete Clip"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>

                    <ClipCard clip={clip} rank={idx + 1} />
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: PIPELINE JOBS */}
      {activeTab === "jobs" && (
        <div className="space-y-4">
          {isLoading ? (
            <div className="py-16 text-center space-y-3">
              <div className="h-8 w-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-xs text-zinc-400">Loading jobs...</p>
            </div>
          ) : jobs.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-white/15 bg-white/[0.02] p-12 text-center space-y-3">
              <Clock className="h-8 w-8 text-zinc-500 mx-auto" />
              <h3 className="text-sm font-semibold text-white">No Processing Runs Recorded</h3>
              <p className="text-xs text-zinc-400">
                Start a single video upload or project batch to see 21-stage job execution logs here.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-white/[0.06] rounded-2xl border border-white/10 bg-white/[0.02] overflow-hidden">
              {jobs.map((job) => {
                const isCompleted = job.status === "completed";
                const isFailed = job.status === "failed";
                const isRunning = job.status === "processing" || job.status === "queued";

                return (
                  <div
                    key={job.id}
                    className="flex flex-col sm:flex-row sm:items-center justify-between p-4 sm:p-5 gap-4 hover:bg-white/[0.02] transition-colors"
                  >
                    <div className="space-y-1.5 flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs font-bold text-white">
                          Job #{job.id.slice(0, 8)}
                        </span>

                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                            isCompleted
                              ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400"
                              : isFailed
                              ? "bg-rose-500/10 border border-rose-500/20 text-rose-400"
                              : "bg-violet-500/10 border border-violet-500/20 text-violet-400 animate-pulse"
                          }`}
                        >
                          {job.status}
                        </span>

                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                          job.mode === "viral_moments"
                            ? "bg-amber-500/10 border border-amber-500/30 text-amber-300"
                            : "bg-violet-500/10 border border-violet-500/30 text-violet-300"
                        }`}>
                          {job.mode === "viral_moments" ? <Zap className="h-2.5 w-2.5" /> : <Mic className="h-2.5 w-2.5" />}
                          {job.mode === "viral_moments" ? "Viral Moments" : "Podcast"}
                        </span>
                      </div>

                      <p className="text-xs text-zinc-400 flex items-center gap-2">
                        <span>Stage {job.current_stage}/21: {job.stage_name}</span>
                        {(job.total_clips_rendered ?? 0) > 0 && (
                          <>
                            <span>•</span>
                            <span className="text-emerald-400 font-semibold">{job.total_clips_rendered} clips rendered</span>
                          </>
                        )}
                        {(job.total_candidates_found ?? 0) > 0 && (
                          <>
                            <span>•</span>
                            <span className="text-violet-300">{job.total_candidates_found} candidates found</span>
                          </>
                        )}
                      </p>


                      {/* Mini progress bar if active */}
                      {isRunning && (
                        <div className="w-full max-w-md h-1.5 rounded-full bg-white/10 overflow-hidden mt-1">
                          <div
                            className="h-full bg-gradient-to-r from-violet-500 to-indigo-500 transition-all duration-300"
                            style={{ width: `${Math.round(job.progress * 100)}%` }}
                          />
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <span className="text-xs text-zinc-500">
                        {new Date(job.created_at).toLocaleString()}
                      </span>

                      <Link
                        href={`/jobs/${job.id}`}
                        className="flex items-center gap-1.5 rounded-xl bg-white/[0.04] border border-white/10 px-3.5 py-2 text-xs font-semibold text-zinc-200 hover:text-white hover:bg-white/10 transition-all"
                      >
                        <Eye className="h-3.5 w-3.5 text-violet-400" />
                        <span>Inspect Run</span>
                      </Link>

                      <button
                        onClick={(e) => handleDeleteJob(job.id, e)}
                        className="flex h-8 w-8 items-center justify-center rounded-xl text-zinc-500 hover:text-rose-400 hover:bg-rose-500/10 transition-all"
                        title="Delete Job"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
