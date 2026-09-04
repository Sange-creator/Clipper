"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Film, Sparkles, Layers, Activity, Upload, Key, AlertTriangle } from "lucide-react";
import { BrandLogo } from "@/components/ui/BrandLogo";
import { api } from "@/lib/api";

export function Navbar() {
  const pathname = usePathname();
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");

  useEffect(() => {
    let isMounted = true;
    const check = async () => {
      const res = await api.checkHealth();
      if (isMounted) {
        setBackendStatus(res ? "online" : "offline");
      }
    };
    check();
    const interval = setInterval(check, 8000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const links = [
    { href: "/", label: "Single Video", icon: Upload },
    { href: "/projects", label: "Project Workspaces", icon: Layers },
    { href: "/history", label: "Clips & History", icon: Film },
    { href: "/admin", label: "Observability", icon: Activity },
    { href: "/settings", label: "AI & API Keys", icon: Key },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/[0.08] bg-[#07090e]/85 backdrop-blur-2xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand */}
        <Link href="/" className="hover:opacity-95 transition-opacity">
          <BrandLogo size="md" />
        </Link>

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center gap-1.5 bg-slate-900/50 p-1 rounded-2xl border border-white/[0.06]">
          {links.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center gap-2 rounded-xl px-3.5 py-1.5 text-xs font-semibold transition-all duration-200 ${
                  isActive
                    ? "bg-gradient-to-r from-violet-600/90 to-indigo-600/90 text-white shadow-md shadow-violet-600/25 border border-violet-400/30"
                    : "text-slate-400 hover:text-white hover:bg-white/[0.05]"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Status Indicator */}
        <div className="flex items-center gap-3">
          {backendStatus === "online" && (
            <div className="flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 shadow-sm shadow-emerald-500/10">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="tracking-tight">Engine Ready</span>
            </div>
          )}

          {backendStatus === "offline" && (
            <div
              title="FastAPI backend is offline (127.0.0.1:8000). Start with: ./dev.sh"
              className="flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30 shadow-sm shadow-rose-500/10"
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
              </span>
              <span className="tracking-tight">Backend Offline (Port 8000)</span>
            </div>
          )}

          {backendStatus === "checking" && (
            <div className="flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold bg-zinc-800 text-zinc-400 border border-zinc-700">
              <span className="relative flex h-2 w-2">
                <span className="relative inline-flex rounded-full h-2 w-2 bg-zinc-400"></span>
              </span>
              <span className="tracking-tight">Connecting...</span>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

