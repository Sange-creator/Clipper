"use client";

import React from "react";

interface BrandLogoProps {
  size?: "sm" | "md" | "lg";
  showSubtitle?: boolean;
}

export function BrandLogo({ size = "md", showSubtitle = true }: BrandLogoProps) {
  const sizeMap = {
    sm: { icon: "h-8 w-8", text: "text-base", sub: "text-[10px]" },
    md: { icon: "h-10 w-10", text: "text-lg", sub: "text-[11px]" },
    lg: { icon: "h-14 w-14", text: "text-2xl", sub: "text-xs" },
  };

  const { icon, text, sub } = sizeMap[size];

  return (
    <div className="flex items-center gap-3 select-none">
      {/* Dynamic Animated Logo Emblem */}
      <div className={`relative ${icon} flex-shrink-0 group/logo`}>
        {/* Ambient Glow Halo */}
        <div className="absolute -inset-1 rounded-2xl bg-gradient-to-r from-violet-600 via-indigo-600 to-cyan-500 opacity-40 blur-md group-hover/logo:opacity-75 transition duration-500" />
        
        {/* Squircle Surface */}
        <div className="relative h-full w-full rounded-xl bg-gradient-to-br from-[#1b153b] via-[#101326] to-[#0a0c16] border border-violet-500/30 p-1.5 shadow-xl flex items-center justify-center overflow-hidden">
          <svg viewBox="0 0 100 100" className="w-full h-full" fill="none">
            <defs>
              <linearGradient id="prismGradComp" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#C084FC" />
                <stop offset="50%" stop-color="#6366F1" />
                <stop offset="100%" stop-color="#06B6D4" />
              </linearGradient>
              <linearGradient id="sparkGradComp" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#F59E0B" />
                <stop offset="100%" stop-color="#EF4444" />
              </linearGradient>
            </defs>

            {/* Film guides */}
            <rect x="18" y="24" width="6" height="52" rx="3" fill="#6366F1" fillOpacity="0.5" />
            <rect x="28" y="16" width="6" height="68" rx="3" fill="url(#prismGradComp)" fillOpacity="0.8" />
            
            {/* Play/Clipper apex */}
            <path d="M42 20 L78 47 C80 49 80 53 78 55 L42 82 C39 84 36 82 36 78 L36 24 C36 20 39 18 42 20 Z" fill="url(#prismGradComp)" />
            <path d="M42 24 L70 48 L42 48 Z" fill="#FFFFFF" fillOpacity="0.3" />
            <line x1="30" y1="50" x2="76" y2="50" stroke="#090B14" strokeWidth="3" strokeLinecap="round" />
            
            {/* Viral spark */}
            <circle cx="74" cy="24" r="5" fill="url(#sparkGradComp)" />
            <circle cx="74" cy="24" r="2" fill="#FFFFFF" />
          </svg>
        </div>
      </div>

      {/* Typography */}
      <div>
        <div className="flex items-center gap-2">
          <span className={`font-black ${text} text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-100 to-slate-300 tracking-tight`}>
            CLIPPER<span className="text-violet-400 font-extrabold ml-1">PRO</span>
          </span>
          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wider uppercase bg-violet-500/10 text-violet-300 border border-violet-500/25">
            AI V3
          </span>
        </div>
        {showSubtitle && (
          <p className={`${sub} text-slate-400 font-medium tracking-tight -mt-0.5`}>
            Short-Form Content Engine
          </p>
        )}
      </div>
    </div>
  );
}
