"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Download,
  Sparkles,
  Layers,
  ArrowLeft,
  AlertCircle,
  CheckCircle2,
  Share2,
  Film,
  Trash2,
  AlertTriangle,
} from "lucide-react";
import { api } from "@/lib/api";
import { CandidateDetail, JobStatusResponse, RenderedClipResponse } from "@/lib/types";
import { StageProgress } from "@/components/processing/StageProgress";
import { LiveLogFeed } from "@/components/processing/LiveLogFeed";
import { CandidatePoolVisualizer } from "@/components/processing/CandidatePoolVisualizer";
import { ClipCard } from "@/components/review/ClipCard";

export default function JobDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const jobId = resolvedParams.id;
  const router = useRouter();

  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [candidates, setCandidates] = useState<CandidateDetail[]>([]);
  const [clips, setClips] = useState<RenderedClipResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchJobData = async () => {
    try {
      const data = await api.getJob(jobId);
      setJob(data);

      if (data.current_stage >= 8 || (data.total_candidates_found ?? 0) > 0) {
        api.getJobCandidates(jobId).then((cands) => {
          if (cands.length > 0) setCandidates(cands);
        }).catch(() => {});
      }

      if (data.status === "completed" || (data.total_clips_rendered ?? 0) > 0) {
        api.getJobClips(jobId).then((loadedClips) => {
          if (loadedClips.length > 0) setClips(loadedClips);
        }).catch(() => {});
      }

    } catch (err: any) {
      setError(err.message || "Failed to load job");
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchJobData();

    // Connect SSE Stream for real-time live events with safe error handling
    let eventSource: EventSource | null = null;
    try {
      const sseUrl = `${api.getBaseUrl()}/jobs/${jobId}/events`;
      eventSource = new EventSource(sseUrl);

      eventSource.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.job_id === jobId) {
            setJob((prev) => {
              if (!prev) return prev;
              return {
                ...prev,
                current_stage: data.current_stage || prev.current_stage,
                stage_name: data.stage_name || prev.stage_name,
                progress: data.progress !== undefined ? data.progress : prev.progress,
                status: data.status || prev.status,
                logs: [
                  ...prev.logs,
                  {
                    stage: data.current_stage || 1,
                    stage_name: data.stage_name || "",
                    message: data.message || "",
                    timestamp: data.timestamp || new Date().toISOString(),
                  },
                ],
              };
            });

            // If stage 8+ reached, fetch candidates
            if (data.current_stage >= 8) {
              api.getJobCandidates(jobId).then((cands) => {
                if (cands.length > 0) setCandidates(cands);
              }).catch(() => {});
            }

            // If completed or rendered clips are ready
            if (data.status === "completed" || data.current_stage >= 16) {
              api.getJobClips(jobId).then((loadedClips) => {
                if (loadedClips.length > 0) setClips(loadedClips);
              }).catch(() => {});
            }
          }
        } catch {
          // ignore parse error
        }
      };

      eventSource.onerror = () => {
        // Gracefully close on Mixed Content / loopback restriction and rely on active polling below
        eventSource?.close();
      };
    } catch {
      // EventSource not available
    }

    // Active polling fallback every 2s ensures smooth progress even if SSE is restricted
    const interval = setInterval(() => {
      fetchJobData();
    }, 2000);

    return () => {
      if (eventSource) eventSource.close();
      clearInterval(interval);
    };
  }, [jobId]);

  const handleDeleteJob = async () => {
    setIsDeleting(true);
    try {
      await api.deleteJob(jobId);
      router.push("/");
    } catch (err: any) {
      alert(err.message || "Failed to delete job");
    } finally {
      setIsDeleting(false);
      setShowDeleteModal(false);
    }
  };

  if (error) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-16 text-center space-y-4">
        <AlertCircle className="h-12 w-12 text-rose-400 mx-auto" />
        <h2 className="text-xl font-bold text-white">Failed to Load Job</h2>
        <p className="text-zinc-400 text-sm">{error}</p>
        <Link href="/" className="inline-flex items-center gap-2 text-violet-400 hover:text-violet-300 text-sm">
          <ArrowLeft className="h-4 w-4" /> Return to Home
        </Link>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-24 text-center space-y-4">
        <div className="h-10 w-10 border-2 border-violet-500 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-zinc-400 text-sm font-medium">Connecting to pipeline stream...</p>
      </div>
    );
  }

  const isCompleted = job.status === "completed";

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-10">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/[0.04] border border-white/10 text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl sm:text-2xl font-bold text-white">Pipeline Execution</h1>
              <span className="rounded-lg bg-zinc-800 px-2 py-0.5 font-mono text-xs text-zinc-400">
                Job #{jobId.slice(0, 8)}
              </span>
            </div>
            <p className="text-xs text-zinc-400">Deterministic 21-stage video processing & AI discovery</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {isCompleted && clips.length > 0 && (
            <a
              href={api.getBatchExportUrl(jobId)}
              download
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 px-5 py-2.5 text-xs font-semibold text-white shadow-lg shadow-emerald-500/20 hover:from-emerald-500 hover:to-teal-500 transition-all"
            >
              <Download className="h-4 w-4" />
              <span>Bulk Download ({clips.length} Clips Dual-Folder ZIP)</span>
            </a>
          )}

          <button
            onClick={() => setShowDeleteModal(true)}
            className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 hover:bg-rose-600 hover:text-white transition-all"
            title="Delete Job"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* 21-Stage Progress Tracker */}
      <StageProgress job={job} />

      {/* Rendered Clips Grid (Persistently displayed) */}
      {clips.length > 0 && (
        <div className="space-y-6 pt-4 border-t border-white/[0.08]">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-violet-400" />
                <h2 className="text-xl font-bold text-white">Selected High-Retention Clips</h2>
              </div>
              <p className="text-xs text-zinc-400">
                Ranked by 12-dimensional composite scores • Click any clip to review, re-trim, or export
              </p>
            </div>
            <span className="rounded-full bg-violet-500/10 border border-violet-500/20 px-3 py-1 text-xs font-semibold text-violet-300">
              {clips.length} Clips Generated
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {clips.map((clip, idx) => (
              <ClipCard key={clip.id} clip={clip} rank={idx + 1} />
            ))}
          </div>
        </div>
      )}

      {/* Candidate Pool Discovery Visualizer */}
      {candidates.length > 0 && (
        <CandidatePoolVisualizer
          candidates={candidates}
          totalFound={job.total_candidates_found || candidates.length}
        />
      )}

      {/* Live Terminal Logs */}
      <LiveLogFeed logs={job.logs || []} defaultCollapsed={job.status === "completed"} />


      {/* Delete Job Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="relative w-full max-w-md rounded-2xl bg-zinc-900 border border-rose-500/30 p-6 shadow-2xl space-y-5">
            <div className="flex items-center gap-3 text-rose-400">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500/10 border border-rose-500/20">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Delete Job Run?</h3>
                <p className="text-xs text-zinc-400">Job #{jobId.slice(0, 8)}</p>
              </div>
            </div>

            <p className="text-xs text-zinc-300 leading-relaxed">
              This will permanently delete this job, its candidate pool, and all {clips.length} generated clips.
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
                disabled={isDeleting}
                onClick={handleDeleteJob}
                className="flex items-center gap-2 rounded-xl bg-rose-600 px-5 py-2.5 text-xs font-semibold text-white hover:bg-rose-500 disabled:opacity-50 transition-all"
              >
                <Trash2 className="h-3.5 w-3.5" />
                <span>{isDeleting ? "Deleting..." : "Confirm & Delete"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
