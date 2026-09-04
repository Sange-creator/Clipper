"use client";

import { useState } from "react";
import {
  Sparkles,
  Zap,
  Clock,
  BookOpen,
  ArrowRight,
  Palette,
  X,
  RefreshCw,
  FileText,
  MessageSquare,
} from "lucide-react";
import { CaptionPresetPicker } from "./CaptionPresetPicker";
import { CaptionStyleType } from "@/lib/types";

interface RegenerateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRegenerate: (intent: string, captionStyle?: string, note?: string, hookHeaderStyle?: string) => Promise<void>;
  currentStyle: string;
  currentHookHeaderStyle?: string;
}

const INTENTS = [
  {
    id: "stronger_hook",
    title: "Stronger Opening Hook",
    desc: "Trims filler introduction and opens directly on high-curiosity dialogue",
    icon: Zap,
    color: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  },
  {
    id: "shorter_duration",
    title: "Shorter & Punchier",
    desc: "Cuts 25% of setup to optimize for high completion rate on Shorts/Reels",
    icon: Clock,
    color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  },
  {
    id: "longer_context",
    title: "More Story Context",
    desc: "Expands timeline backwards by 6-8 seconds for complete narrative setup",
    icon: BookOpen,
    color: "text-sky-400 bg-sky-500/10 border-sky-500/20",
  },
  {
    id: "different_payoff",
    title: "Extend Payoff / Takeaway",
    desc: "Includes the subsequent conclusion sentence for stronger emotional payoff",
    icon: ArrowRight,
    color: "text-violet-400 bg-violet-500/10 border-violet-500/20",
  },
  {
    id: "style_change",
    title: "Change Visual Style Only",
    desc: "Preserves exact boundaries while applying a new caption font preset",
    icon: Palette,
    color: "text-pink-400 bg-pink-500/10 border-pink-500/20",
  },
];

export function RegenerateModal({
  isOpen,
  onClose,
  onRegenerate,
  currentStyle,
  currentHookHeaderStyle,
}: RegenerateModalProps) {
  const [selectedIntent, setSelectedIntent] = useState<string>("stronger_hook");
  const [captionStyle, setCaptionStyle] = useState<CaptionStyleType>((currentStyle as any) || "tiktok_viral");
  const [hookHeaderStyle, setHookHeaderStyle] = useState<string>(currentHookHeaderStyle || "viral_creator");
  const [customNote, setCustomNote] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await onRegenerate(selectedIntent, captionStyle, customNote, hookHeaderStyle);
      onClose();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl rounded-2xl bg-zinc-900 border border-white/10 p-6 sm:p-8 shadow-2xl space-y-6 max-h-[90vh] overflow-y-auto">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-zinc-400 hover:text-white"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-violet-400" />
            <h2 className="text-lg font-bold text-white">Regenerate Clip with AI</h2>
          </div>
          <p className="text-xs text-zinc-400">
            Direct the AI on how to enhance this clip’s hook, duration, or narrative payoff.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Intent Grid */}
          <div className="space-y-3">
            <label className="text-xs font-semibold uppercase tracking-wider text-zinc-300">
              Strategic Intent
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {INTENTS.map((item) => {
                const Icon = item.icon;
                const isSelected = selectedIntent === item.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setSelectedIntent(item.id)}
                    className={`flex items-start gap-3 p-3.5 rounded-xl border text-left transition-all ${
                      isSelected
                        ? "bg-violet-600/15 border-violet-500 ring-1 ring-violet-500 shadow-md"
                        : "bg-white/[0.02] border-white/10 hover:border-white/20 hover:bg-white/[0.04]"
                    }`}
                  >
                    <div className={`flex h-8 w-8 items-center justify-center rounded-lg border ${item.color} shrink-0`}>
                      <Icon className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-white">{item.title}</p>
                      <p className="text-[11px] text-zinc-400 mt-0.5 leading-snug">{item.desc}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Caption Preset Picker */}
          <CaptionPresetPicker
            selected={captionStyle}
            onChange={setCaptionStyle}
          />

          {/* Hook Header Visual Style */}
          <div className="space-y-2 pt-1 border-t border-white/5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold uppercase tracking-wider text-zinc-300">
                Hook Header Visual Style
              </label>
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
          </div>

          {/* Custom Note */}
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-zinc-300">
              Custom Direction (Optional)
            </label>
            <input
              type="text"
              value={customNote}
              onChange={(e) => setCustomNote(e.target.value)}
              placeholder="e.g. Focus specifically on the quote about habits"
              className="w-full rounded-xl bg-black/40 border border-white/10 px-4 py-2.5 text-xs text-white placeholder-zinc-500 focus:border-violet-500 focus:outline-none"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl px-4 py-2 text-xs font-semibold text-zinc-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 px-5 py-2.5 text-xs font-semibold text-white shadow-lg shadow-violet-500/20 hover:from-violet-500 hover:to-indigo-500 disabled:opacity-50 transition-all"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
              <span>{isLoading ? "Regenerating..." : "Apply & Re-render Clip"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
