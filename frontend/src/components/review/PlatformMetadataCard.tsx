"use client";

import { useState } from "react";
import { Copy, Check, Download, Share2, Tag, FileText } from "lucide-react";
import { PlatformMetadata } from "@/lib/types";
import { api } from "@/lib/api";

interface PlatformMetadataCardProps {
  metadata: PlatformMetadata;
  clipId: string;
}

export function PlatformMetadataCard({ metadata, clipId }: PlatformMetadataCardProps) {
  const [activeTab, setActivePlatform] = useState<"tiktok" | "reels" | "shorts">("tiktok");
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const copyToClipboard = (text: string, fieldName: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(fieldName);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const activeContent = {
    tiktok: {
      title: metadata.tiktok_title || "High Retention Moment",
      caption: metadata.tiktok_caption || "",
      hashtags: metadata.tiktok_hashtags || [],
    },
    reels: {
      title: "Instagram Reel",
      caption: metadata.reels_caption || "",
      hashtags: metadata.reels_hashtags || [],
    },
    shorts: {
      title: metadata.shorts_title || "Must-Watch Short",
      caption: metadata.shorts_description || "",
      hashtags: metadata.shorts_hashtags || [],
    },
  }[activeTab];

  const fullCopyText = `${activeContent.title}\n\n${activeContent.caption}\n\n${activeContent.hashtags.join(" ")}`;

  // Dedicated single-paragraph ready-to-paste block requested by user
  const singleParaText = metadata.single_para_copy || (() => {
    const partPrefix = metadata.part_index && metadata.total_parts && metadata.total_parts > 1
      ? `Part ${metadata.part_index}/${metadata.total_parts}: `
      : "";
    const cleanCap = (activeContent.caption || "").replace(/\n+/g, " ").trim();
    const tags = activeContent.hashtags.slice(0, 5).join(" ");
    return `${partPrefix}${activeContent.title} — ${cleanCap} ${tags}`.trim();
  })();

  return (
    <div className="glass-panel rounded-2xl p-6 space-y-6">
      {/* Header & Platform Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/[0.08] pb-4">
        <div>
          <h3 className="text-sm font-semibold text-white">Platform-Specific Copy & Hashtags</h3>
          <p className="text-xs text-zinc-400">Pre-optimized for maximum short-form algorithm reach</p>
        </div>

        {/* Platform Switcher */}
        <div className="flex items-center rounded-xl bg-black/40 p-1 border border-white/10">
          {[
            { id: "tiktok", name: "TikTok" },
            { id: "reels", name: "Instagram Reels" },
            { id: "shorts", name: "YouTube Shorts" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActivePlatform(tab.id as any)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                activeTab === tab.id
                  ? "bg-violet-600 text-white shadow-md shadow-violet-500/20"
                  : "text-zinc-400 hover:text-white"
              }`}
            >
              {tab.name}
            </button>
          ))}
        </div>
      </div>

      {/* 1-Click Single Paragraph Post Banner */}
      <div className="rounded-xl border border-violet-500/30 bg-violet-950/20 p-4 space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-violet-400" />
            <span className="text-xs font-bold text-white uppercase tracking-wider">
              Single-Paragraph Ready-To-Post
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => copyToClipboard(singleParaText, "single_para")}
              className="flex items-center gap-1.5 rounded-lg bg-violet-600 px-3 py-1.5 text-xs font-semibold text-white shadow-md shadow-violet-600/30 hover:bg-violet-500 transition-colors"
            >
              {copiedField === "single_para" ? <Check className="h-3.5 w-3.5 text-emerald-300" /> : <Copy className="h-3.5 w-3.5" />}
              <span>{copiedField === "single_para" ? "Copied Paragraph!" : "Copy Single Paragraph"}</span>
            </button>
            <a
              href={api.getSingleClipSingleParaUrl(clipId, true)}
              download
              className="flex items-center gap-1 rounded-lg bg-white/5 border border-white/10 px-2.5 py-1.5 text-xs font-medium text-zinc-300 hover:bg-white/10 transition-colors"
              title="Download text file"
            >
              <Download className="h-3.5 w-3.5" />
              <span>.TXT</span>
            </a>
          </div>
        </div>
        <p className="text-xs text-zinc-300 leading-relaxed bg-black/40 border border-white/5 p-3 rounded-lg font-mono selection:bg-violet-500 selection:text-white">
          {singleParaText}
        </p>
      </div>

      {/* Content Fields */}
      <div className="space-y-4">
        {/* Title */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="font-medium text-zinc-300">Generated Video Title</span>
            <button
              onClick={() => copyToClipboard(activeContent.title, "title")}
              className="flex items-center gap-1 text-[11px] text-violet-400 hover:text-violet-300"
            >
              {copiedField === "title" ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
              <span>{copiedField === "title" ? "Copied" : "Copy Title"}</span>
            </button>
          </div>
          <div className="rounded-xl bg-black/30 border border-white/5 p-3 text-xs text-white font-medium">
            {activeContent.title}
          </div>
        </div>

        {/* Caption */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="font-medium text-zinc-300">Caption / Description</span>
            <button
              onClick={() => copyToClipboard(activeContent.caption, "caption")}
              className="flex items-center gap-1 text-[11px] text-violet-400 hover:text-violet-300"
            >
              {copiedField === "caption" ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
              <span>{copiedField === "caption" ? "Copied" : "Copy Caption"}</span>
            </button>
          </div>
          <div className="rounded-xl bg-black/30 border border-white/5 p-3 text-xs text-zinc-200 whitespace-pre-line leading-relaxed">
            {activeContent.caption}
          </div>
        </div>

        {/* Hashtags */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="font-medium text-zinc-300">Niche Algorithm Hashtags</span>
            <button
              onClick={() => copyToClipboard(activeContent.hashtags.join(" "), "hashtags")}
              className="flex items-center gap-1 text-[11px] text-violet-400 hover:text-violet-300"
            >
              {copiedField === "hashtags" ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
              <span>{copiedField === "hashtags" ? "Copied" : "Copy All Tags"}</span>
            </button>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {activeContent.hashtags.map((tag, idx) => (
              <span
                key={idx}
                className="rounded-lg bg-violet-500/10 border border-violet-500/20 px-2.5 py-1 text-xs font-mono text-violet-300"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Export Actions Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-white/[0.08]">
        <button
          onClick={() => copyToClipboard(fullCopyText, "all")}
          className="w-full sm:w-auto flex items-center justify-center gap-2 rounded-xl bg-white/[0.05] border border-white/10 px-4 py-2.5 text-xs font-semibold text-zinc-200 hover:bg-white/10 hover:text-white transition-colors"
        >
          {copiedField === "all" ? <Check className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />}
          <span>{copiedField === "all" ? "Copied Everything!" : "Copy Title + Caption + Tags"}</span>
        </button>

        <a
          href={api.getSingleExportUrl(clipId)}
          download
          className="w-full sm:w-auto flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 px-5 py-2.5 text-xs font-semibold text-white shadow-lg shadow-emerald-500/20 hover:from-emerald-500 hover:to-teal-500 transition-all"
        >
          <Download className="h-4 w-4" />
          <span>Download MP4 + Subtitles (.ZIP)</span>
        </a>
      </div>
    </div>
  );
}
