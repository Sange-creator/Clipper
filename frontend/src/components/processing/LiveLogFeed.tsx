"use client";

import { useEffect, useRef, useState } from "react";
import { Terminal, Clock, ChevronDown, ChevronUp, ArrowDown } from "lucide-react";
import { JobLog } from "@/lib/types";

interface LiveLogFeedProps {
  logs: JobLog[];
  defaultCollapsed?: boolean;
}

export function LiveLogFeed({ logs, defaultCollapsed = false }: LiveLogFeedProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);

  // Monitor internal container scroll to toggle auto-scroll
  const handleScroll = () => {
    if (!containerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 35;
    setAutoScroll(isAtBottom);
  };

  // Internal-only scroll: Never affects window/browser viewport
  useEffect(() => {
    if (autoScroll && containerRef.current && !isCollapsed) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs, autoScroll, isCollapsed]);

  const scrollToBottom = () => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
      setAutoScroll(true);
    }
  };

  return (
    <div className="glass-panel rounded-2xl overflow-hidden border border-white/[0.08]">
      <div className="flex items-center justify-between px-5 py-3.5 bg-black/40 border-b border-white/[0.06]">
        <button
          type="button"
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="flex items-center gap-2 text-left hover:text-white transition-colors"
        >
          <Terminal className="h-4 w-4 text-violet-400" />
          <span className="text-xs font-semibold text-zinc-300">Live Pipeline Diagnostic Terminal</span>
          {isCollapsed ? (
            <ChevronDown className="h-3.5 w-3.5 text-zinc-500 ml-1" />
          ) : (
            <ChevronUp className="h-3.5 w-3.5 text-zinc-500 ml-1" />
          )}
        </button>

        <div className="flex items-center gap-3">
          {!isCollapsed && !autoScroll && (
            <button
              onClick={scrollToBottom}
              className="flex items-center gap-1 rounded-md bg-violet-600/30 border border-violet-500/40 px-2 py-0.5 text-[10px] font-semibold text-violet-300 hover:bg-violet-600 hover:text-white transition-all animate-pulse"
            >
              <ArrowDown className="h-2.5 w-2.5" />
              <span>Resume Auto-Scroll</span>
            </button>
          )}

          <span className="text-[11px] font-mono text-zinc-500">{logs.length} events logged</span>
        </div>
      </div>

      {!isCollapsed && (
        <div
          ref={containerRef}
          onScroll={handleScroll}
          className="p-4 font-mono text-xs max-h-64 overflow-y-auto space-y-2 bg-black/20"
        >
          {logs.length === 0 ? (
            <p className="text-zinc-600 italic">Waiting for pipeline events...</p>
          ) : (
            logs.map((log, idx) => (
              <div key={idx} className="flex items-start gap-3 text-zinc-300 leading-relaxed">
                <span className="text-zinc-600 flex-shrink-0 text-[10px] pt-0.5">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
                <span className="inline-block rounded bg-violet-500/10 px-1.5 py-0.2 text-[10px] text-violet-400 border border-violet-500/20 flex-shrink-0">
                  Stage {log.stage}
                </span>
                <span className="text-zinc-200">{log.message}</span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
