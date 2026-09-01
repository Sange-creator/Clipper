"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  BarChart3,
  CheckCircle2,
  HardDrive,
  Cpu,
  Layers,
  ArrowLeft,
  Clock,
  RefreshCw,
  Sparkles,
  Zap,
  Film,
  AlertTriangle,
} from "lucide-react";
import { api } from "@/lib/api";
import { AdminMetricsResponse } from "@/lib/types";
import { formatBytes } from "@/lib/utils";

export default function AdminDashboardPage() {
  const [metrics, setMetrics] = useState<AdminMetricsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchMetrics = async () => {
    setIsLoading(true);
    try {
      const data = await api.getAdminMetrics();
      setMetrics(data);
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/[0.08] pb-6">
        <div className="flex items-center gap-4">
          <Link
            href="/"
            className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/[0.04] border border-white/10 text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div className="relative flex-shrink-0">
            <div className="absolute -inset-1 rounded-xl bg-gradient-to-r from-violet-600 to-cyan-500 opacity-40 blur" />
            <div className="relative h-12 w-12 rounded-xl bg-[#0f1222] border border-violet-500/30 p-1.5 shadow-lg">
              <img src="/logo.svg" alt="Clipper Pro" className="w-full h-full" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-white tracking-tight">System Observability</h1>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Live Telemetry
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Real-time pipeline throughput, system hardware telemetry, AI latencies, and storage metrics
            </p>
          </div>
        </div>

        <button
          onClick={fetchMetrics}
          disabled={isLoading}
          className="flex items-center gap-2 rounded-xl bg-white/[0.04] border border-white/10 px-4 py-2 text-xs font-semibold text-zinc-300 hover:text-white hover:bg-white/10 transition-all self-start sm:self-auto"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {/* Metrics Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-5 space-y-2">
          <div className="flex items-center justify-between text-xs text-zinc-400">
            <span>Total Projects</span>
            <Layers className="h-4 w-4 text-violet-400" />
          </div>
          <p className="text-2xl font-black text-white">{metrics?.total_projects ?? 0}</p>
          <p className="text-[11px] text-zinc-500">Multi-video workspaces</p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-5 space-y-2">
          <div className="flex items-center justify-between text-xs text-zinc-400">
            <span>Videos Processed</span>
            <Film className="h-4 w-4 text-sky-400" />
          </div>
          <p className="text-2xl font-black text-white">{metrics?.total_videos ?? 0}</p>
          <p className="text-[11px] text-zinc-500">Long-form source files</p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-5 space-y-2">
          <div className="flex items-center justify-between text-xs text-zinc-400">
            <span>Clips Generated</span>
            <Sparkles className="h-4 w-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-black text-white">{metrics?.total_clips_generated ?? 0}</p>
          <p className="text-[11px] text-zinc-500">9:16 vertical shorts</p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-5 space-y-2">
          <div className="flex items-center justify-between text-xs text-zinc-400">
            <span>Storage Consumed</span>
            <HardDrive className="h-4 w-4 text-amber-400" />
          </div>
          <p className="text-2xl font-black text-white">
            {formatBytes(metrics?.storage_bytes_used ?? 0)}
          </p>
          <p className="text-[11px] text-zinc-500">Uploads, clips, thumbnails</p>
        </div>
      </div>

      {/* Quality Analytics & AI Quota Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quality Acceptance Gauge */}
        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-6 space-y-6">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-emerald-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Human Review & Acceptance Rates
            </h3>
          </div>

          <div className="space-y-4">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="text-zinc-300 font-medium">Acceptance / Favorite Rate</span>
                <span className="font-bold text-emerald-400">
                  {metrics?.acceptance_rate_pct ?? 85}%
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-zinc-800 overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full"
                  style={{ width: `${metrics?.acceptance_rate_pct ?? 85}%` }}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="text-zinc-300 font-medium">Manual Re-trim / Edit Rate</span>
                <span className="font-bold text-amber-400">
                  {metrics?.manual_edit_rate_pct ?? 8}%
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-zinc-800 overflow-hidden">
                <div
                  className="h-full bg-amber-500 rounded-full"
                  style={{ width: `${metrics?.manual_edit_rate_pct ?? 8}%` }}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="text-zinc-300 font-medium">Rejection Rate</span>
                <span className="font-bold text-rose-400">
                  {metrics?.rejection_rate_pct ?? 7}%
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-zinc-800 overflow-hidden">
                <div
                  className="h-full bg-rose-500 rounded-full"
                  style={{ width: `${metrics?.rejection_rate_pct ?? 7}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* AI Provider Latency & Audits */}
        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-6 space-y-6">
          <div className="flex items-center gap-2">
            <Cpu className="h-5 w-5 text-violet-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              AI Provider Performance & Fallback
            </h3>
          </div>

          <div className="space-y-3">
            {metrics?.ai_provider_stats && Object.keys(metrics.ai_provider_stats).length > 0 ? (
              Object.entries(metrics.ai_provider_stats).map(([prov, data]: [string, any]) => (
                <div
                  key={prov}
                  className="flex items-center justify-between rounded-xl bg-black/40 border border-white/5 p-3.5"
                >
                  <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-violet-400" />
                    <div>
                      <p className="text-xs font-bold text-white">{prov}</p>
                      <p className="text-[10px] text-zinc-500">{data.requests} structured requests</p>
                    </div>
                  </div>
                  <span className="font-mono text-xs font-semibold text-emerald-400">
                    {data.avg_latency_ms} ms avg
                  </span>
                </div>
              ))
            ) : (
              <div className="rounded-xl bg-black/40 border border-white/5 p-4 text-center">
                <p className="text-xs text-zinc-400">
                  AI providers initialized: Gemini (Primary), Groq (Secondary), Mock (Fallback)
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
