"use client";

import { Check, Sparkles } from "lucide-react";

export interface CaptionPreset {
  id: "tiktok_viral" | "hormozi_bold" | "clean_white" | "bold_yellow" | "podcast_box" | "cinematic" | "meme_impact" | "cyber_neon";
  label: string;
  desc: string;
  previewClass: string;
}

const PRESETS: CaptionPreset[] = [
  {
    id: "tiktok_viral",
    label: "TikTok Viral (Top Pick)",
    desc: "Active word electric yellow & crisp white pop with bold shadow",
    previewClass: "font-black text-yellow-300 drop-shadow-[0_2px_4px_rgba(0,0,0,1)] uppercase tracking-wider",
  },
  {
    id: "hormozi_bold",
    label: "Hormozi Punch",
    desc: "High-retention neon lime green & yellow impact block text",
    previewClass: "font-black text-lime-400 drop-shadow-[0_2px_5px_rgba(0,0,0,1)] uppercase",
  },
  {
    id: "bold_yellow",
    label: "Bold Yellow",
    desc: "High-energy Shorts & TikTok active word pop-in",
    previewClass: "font-black text-yellow-300 drop-shadow-[0_2px_4px_rgba(0,0,0,0.9)] uppercase",
  },
  {
    id: "clean_white",
    label: "Clean White",
    desc: "Minimalist crisp white with subtle dark backing",
    previewClass: "font-sans font-medium text-white tracking-wide",
  },
  {
    id: "podcast_box",
    label: "Podcast Box",
    desc: "Semi-opaque dark backing box for readability",
    previewClass: "font-semibold text-white bg-black/80 px-2 py-0.5 rounded",
  },
  {
    id: "cinematic",
    label: "Cinematic",
    desc: "Serif letterboxed aesthetic for storytelling",
    previewClass: "font-serif italic text-zinc-200 tracking-wider",
  },
  {
    id: "meme_impact",
    label: "Meme Impact",
    desc: "Upper-case bold punch with heavy outline",
    previewClass: "font-black text-white uppercase drop-shadow-[0_4px_6px_rgba(0,0,0,1)]",
  },
  {
    id: "cyber_neon",
    label: "Cyber Neon",
    desc: "Cyan & Magenta glowing retro pop aesthetic",
    previewClass: "font-black text-cyan-300 drop-shadow-[0_0_8px_rgba(255,0,255,0.8)] uppercase",
  },
];

import { CaptionStyleType } from "@/lib/types";

interface CaptionPresetPickerProps {
  selected: string;
  onChange: (id: CaptionStyleType) => void;
}

export function CaptionPresetPicker({ selected, onChange }: CaptionPresetPickerProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-violet-400" />
        <label className="text-xs font-semibold uppercase tracking-wider text-zinc-300">
          Caption Visual Styling Preset
        </label>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {PRESETS.map((preset) => {
          const isSelected = selected === preset.id;
          return (
            <button
              key={preset.id}
              type="button"
              onClick={() => onChange(preset.id)}
              className={`flex flex-col text-left p-3.5 rounded-xl border transition-all ${
                isSelected
                  ? "bg-violet-600/15 border-violet-500 ring-1 ring-violet-500 shadow-md"
                  : "bg-white/[0.02] border-white/10 hover:border-white/20 hover:bg-white/[0.04]"
              }`}
            >
              <div className="flex items-center justify-between w-full mb-1">
                <span className="text-xs font-bold text-white">{preset.label}</span>
                {isSelected && <Check className="h-3.5 w-3.5 text-violet-400" />}
              </div>
              <p className="text-[11px] text-zinc-400 mb-2.5 line-clamp-1">{preset.desc}</p>
              
              {/* Preview chip */}
              <div className="mt-auto rounded-lg bg-zinc-950/60 border border-white/5 p-2 text-center text-xs">
                <span className={preset.previewClass}>VIRAL HOOK</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
