"use client";

import { Check, Sparkles } from "lucide-react";

export interface CaptionPreset {
  id: CaptionStyleType;
  label: string;
  desc: string;
  previewClass: string;
  fontTag?: string;
}

const PRESETS: CaptionPreset[] = [
  {
    id: "tiktok_rounded_box",
    label: "TikTok Rounded Box",
    desc: "Rounded translucent pill background with active neon yellow word highlight",
    previewClass: "font-black text-yellow-300 bg-black/85 px-3 py-1 rounded-full uppercase tracking-wide border border-white/10 shadow-lg inline-block",
    fontTag: "TikTok Pill",
  },
  {
    id: "capcut_black_pill",
    label: "CapCut Black Pill",
    desc: "Solid deep black rounded pill with neon lime green active pop",
    previewClass: "font-black text-lime-400 bg-black px-3 py-1 rounded-full uppercase tracking-wider shadow-lg inline-block",
    fontTag: "Rounded Pill",
  },
  {
    id: "tiktok_viral",
    label: "TikTok Viral",
    desc: "Active word electric yellow & crisp white pop with bold shadow",
    previewClass: "font-black text-yellow-300 drop-shadow-[0_2px_4px_rgba(0,0,0,1)] uppercase tracking-wider",
    fontTag: "Arial Black",
  },
  {
    id: "meme",
    label: "Meme Classic",
    desc: "Heavy Impact all-caps solid white with thick black outline",
    previewClass: "font-black text-white uppercase tracking-wider drop-shadow-[0_4px_8px_rgba(0,0,0,1)] text-[13px]",
    fontTag: "Impact",
  },
  {
    id: "white_background",
    label: "White Background Box",
    desc: "High-contrast deep black text on solid pure white card box",
    previewClass: "font-black text-black bg-white px-2.5 py-0.5 rounded uppercase tracking-tight shadow-md",
    fontTag: "Arial Black",
  },
  {
    id: "nostalgic",
    label: "Nostalgic Vintage",
    desc: "Warm amber Courier typewriter aesthetic with sepia shadow",
    previewClass: "font-mono font-bold text-amber-200 drop-shadow-[0_2px_4px_rgba(30,20,10,0.9)] tracking-widest",
    fontTag: "Courier New",
  },
  {
    id: "old_history",
    label: "Old History",
    desc: "Parchment ivory Georgia serif for historical chronicle aesthetics",
    previewClass: "font-serif font-semibold text-amber-100/90 italic drop-shadow-[0_2px_4px_rgba(20,25,35,0.9)] tracking-wide",
    fontTag: "Georgia Serif",
  },
  {
    id: "hormozi_bold",
    label: "Hormozi Punch",
    desc: "High-retention neon lime green & yellow impact block text",
    previewClass: "font-black text-lime-400 drop-shadow-[0_2px_5px_rgba(0,0,0,1)] uppercase",
    fontTag: "Impact",
  },
  {
    id: "bold_yellow",
    label: "Bold Yellow",
    desc: "High-energy Shorts & TikTok active word pop-in",
    previewClass: "font-black text-yellow-300 drop-shadow-[0_2px_4px_rgba(0,0,0,0.9)] uppercase",
    fontTag: "Arial Black",
  },
  {
    id: "clean_white",
    label: "Clean White",
    desc: "Minimalist crisp white with subtle dark backing",
    previewClass: "font-sans font-medium text-white tracking-wide",
    fontTag: "Arial",
  },
  {
    id: "podcast_box",
    label: "Podcast Box",
    desc: "Semi-opaque dark backing box for readability",
    previewClass: "font-semibold text-white bg-black/80 px-2 py-0.5 rounded",
    fontTag: "Trebuchet MS",
  },
  {
    id: "cinematic",
    label: "Cinematic",
    desc: "Serif letterboxed aesthetic for dramatic storytelling",
    previewClass: "font-serif italic text-zinc-200 tracking-wider",
    fontTag: "Georgia",
  },
  {
    id: "playful_comic",
    label: "Comic Playful",
    desc: "Casual cartoon comedy typography with bubblegum accents",
    previewClass: "font-sans font-bold text-white drop-shadow-[0_2px_4px_rgba(255,30,160,0.8)]",
    fontTag: "Comic Sans",
  },
  {
    id: "editorial_serif",
    label: "Editorial Luxury",
    desc: "Refined Times New Roman serif with warm gold accents",
    previewClass: "font-serif text-zinc-100 drop-shadow-[0_2px_3px_rgba(0,0,0,0.8)] tracking-wide",
    fontTag: "Times Serif",
  },
  {
    id: "cyber_neon",
    label: "Cyber Neon",
    desc: "Cyan & Magenta glowing retro pop aesthetic",
    previewClass: "font-black text-cyan-300 drop-shadow-[0_0_8px_rgba(255,0,255,0.8)] uppercase",
    fontTag: "Arial Black",
  },
  {
    id: "capcut_black_box",
    label: "CapCut Black Box",
    desc: "Creator crisp white text on solid opaque black box",
    previewClass: "font-bold text-white bg-black px-2 py-0.5 rounded uppercase text-yellow-300",
    fontTag: "Arial Black",
  },
  {
    id: "capcut_yellow_box",
    label: "CapCut Yellow Box",
    desc: "High-contrast black text on neon yellow box",
    previewClass: "font-black text-black bg-yellow-400 px-2 py-0.5 rounded uppercase",
    fontTag: "Impact",
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
                <div className="flex items-center gap-1.5">
                  {preset.fontTag && (
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-zinc-400 font-mono">
                      {preset.fontTag}
                    </span>
                  )}
                  {isSelected && <Check className="h-3.5 w-3.5 text-violet-400" />}
                </div>
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
