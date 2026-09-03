"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Key,
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  Eye,
  EyeOff,
  Sparkles,
  Zap,
  Cpu,
  Save,
  ArrowLeft,
  RefreshCw,
  Sliders,
  ShieldCheck,
  ClipboardPaste,
  Trash2,
  Mic,
  Radio,
  Subtitles,
  Workflow,
  Check,
  Smartphone,
  Maximize2,
  Monitor,
  Film,
  Layers,
  HardDrive,
  Flame,
  Eraser,
  Wand2,
  Play,
} from "lucide-react";


import { api } from "@/lib/api";
import { SettingsResponse } from "@/lib/types";

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Active AI Provider Mode
  const [aiProvider, setAiProvider] = useState<"gemini" | "groq" | "mock">("groq");
  const [transcriberProvider, setTranscriberProvider] = useState<"auto" | "deepgram" | "whisper">("auto");

  // Deepgram states (First)
  const [deepgramKey, setDeepgramKey] = useState("");
  const [deepgramModel, setDeepgramModel] = useState("nova-3");
  const [showDeepgramKey, setShowDeepgramKey] = useState(false);
  const [testingDeepgram, setTestingDeepgram] = useState(false);
  const [deepgramTestResult, setDeepgramTestResult] = useState<{ valid: boolean; message: string } | null>(null);

  // Groq states (Second)
  const [groqKey, setGroqKey] = useState("");
  const [groqModel, setGroqModel] = useState("llama-3.1-70b-versatile");
  const [showGroqKey, setShowGroqKey] = useState(false);
  const [testingGroq, setTestingGroq] = useState(false);
  const [groqTestResult, setGroqTestResult] = useState<{ valid: boolean; message: string } | null>(null);

  // Gemini states (Third - Fallback)
  const [geminiKey, setGeminiKey] = useState("");
  const [geminiModel, setGeminiModel] = useState("gemini-2.0-flash");
  const [showGeminiKey, setShowGeminiKey] = useState(false);
  const [testingGemini, setTestingGemini] = useState(false);
  const [geminiTestResult, setGeminiTestResult] = useState<{ valid: boolean; message: string } | null>(null);

  // Framing & Aspect Ratio defaults
  const [defaultFramingMode, setDefaultFramingMode] = useState<"crop_9_16" | "blur_fit_9_16" | "original_16_9">("crop_9_16");
  const [defaultBlurRadius, setDefaultBlurRadius] = useState<number>(30);
  const [defaultSubtitlePosition, setDefaultSubtitlePosition] = useState<number>(75);
  const [defaultAddHookHeader, setDefaultAddHookHeader] = useState<boolean>(true);
  const [defaultHookHeaderPosition, setDefaultHookHeaderPosition] = useState<number>(12);
  const [defaultRemoveWatermark, setDefaultRemoveWatermark] = useState<boolean>(false);
  const [defaultWatermarkPosition, setDefaultWatermarkPosition] = useState<string>("top_right");
  const [defaultEnhanceQuality, setDefaultEnhanceQuality] = useState<boolean>(true);
  const [defaultHookStrategy, setDefaultHookStrategy] = useState<"teaser_climax_hook" | "direct_chronological">("teaser_climax_hook");

  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const fetchSettings = async () => {
    try {
      const data = await api.getSettings();
      setSettings(data);
      if (data.ai_provider) setAiProvider(data.ai_provider as any);
      setGeminiModel(data.gemini_model || "gemini-2.0-flash");
      setGroqModel(data.groq_model || "llama-3.1-70b-versatile");
      setDeepgramModel(data.deepgram_model || "nova-3");
      setTranscriberProvider((data.transcriber_provider as any) || "auto");
      if (data.default_framing_mode) setDefaultFramingMode(data.default_framing_mode as any);
      if (data.default_blur_radius) setDefaultBlurRadius(data.default_blur_radius);
      if (data.default_subtitle_position) setDefaultSubtitlePosition(data.default_subtitle_position);
      if (data.default_add_hook_header !== undefined) setDefaultAddHookHeader(data.default_add_hook_header);
      if (data.default_hook_header_position) setDefaultHookHeaderPosition(data.default_hook_header_position);
      if (data.default_remove_watermark !== undefined) setDefaultRemoveWatermark(data.default_remove_watermark);
      if (data.default_watermark_position) setDefaultWatermarkPosition(data.default_watermark_position as any);
      if (data.default_enhance_quality !== undefined) setDefaultEnhanceQuality(data.default_enhance_quality);
      if (data.default_hook_strategy) setDefaultHookStrategy(data.default_hook_strategy as any);

      // Hydrate plain keys from localStorage if available
      if (typeof window !== "undefined") {
        const savedDeepgram = localStorage.getItem("clipper_deepgram_key");
        if (savedDeepgram && !deepgramKey) setDeepgramKey(savedDeepgram);

        const savedGroq = localStorage.getItem("clipper_groq_key");
        if (savedGroq && !groqKey) setGroqKey(savedGroq);

        const savedGemini = localStorage.getItem("clipper_gemini_key");
        if (savedGemini && !geminiKey) setGeminiKey(savedGemini);
      }
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handlePasteFromClipboard = async (type: "deepgram" | "groq" | "gemini") => {
    try {
      const text = await navigator.clipboard.readText();
      if (text && text.trim()) {
        const cleaned = text.trim();
        if (type === "deepgram") {
          setDeepgramKey(cleaned);
          setDeepgramTestResult(null);
          if (typeof window !== "undefined") localStorage.setItem("clipper_deepgram_key", cleaned);
        } else if (type === "groq") {
          setGroqKey(cleaned);
          setGroqTestResult(null);
          if (typeof window !== "undefined") localStorage.setItem("clipper_groq_key", cleaned);
        } else if (type === "gemini") {
          setGeminiKey(cleaned);
          setGeminiTestResult(null);
          if (typeof window !== "undefined") localStorage.setItem("clipper_gemini_key", cleaned);
        }
      }
    } catch {
      // Clipboard fallback
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSaveSuccess(false);

    // Save to localStorage
    if (typeof window !== "undefined") {
      if (deepgramKey.trim()) localStorage.setItem("clipper_deepgram_key", deepgramKey.trim());
      if (groqKey.trim()) localStorage.setItem("clipper_groq_key", groqKey.trim());
      if (geminiKey.trim()) localStorage.setItem("clipper_gemini_key", geminiKey.trim());
    }

    try {
      const updated = await api.updateSettings({
        ai_provider: aiProvider,
        deepgram_api_key: deepgramKey.trim() || undefined,
        deepgram_model: deepgramModel,
        groq_api_key: groqKey.trim() || undefined,
        groq_model: groqModel,
        gemini_api_key: geminiKey.trim() || undefined,
        gemini_model: geminiModel,
        transcriber_provider: transcriberProvider,
        default_framing_mode: defaultFramingMode,
        default_blur_radius: defaultBlurRadius,
        default_subtitle_position: defaultSubtitlePosition,
        default_add_hook_header: defaultAddHookHeader,
        default_hook_header_position: defaultHookHeaderPosition,
        default_remove_watermark: defaultRemoveWatermark,
        default_watermark_position: defaultWatermarkPosition,
        default_enhance_quality: defaultEnhanceQuality,
        default_hook_strategy: defaultHookStrategy,
      });
      setSettings(updated);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (err: any) {
      alert(err.message || "Failed to update settings");
    } finally {
      setIsSaving(false);
    }
  };

  const handleTestKey = async (provider: "deepgram" | "groq" | "gemini") => {
    if (provider === "deepgram") {
      const keyToTest = deepgramKey.trim();
      if (!keyToTest && !settings?.deepgram_api_key_configured) {
        setDeepgramTestResult({ valid: false, message: "Please enter or paste your Deepgram API key first." });
        return;
      }
      setTestingDeepgram(true);
      setDeepgramTestResult(null);
      try {
        const res = await api.testApiKey("deepgram", keyToTest, deepgramModel);
        setDeepgramTestResult(res);
      } catch (err: any) {
        setDeepgramTestResult({ valid: false, message: err.message || "Connection failed" });
      } finally {
        setTestingDeepgram(false);
      }
    } else if (provider === "groq") {
      const keyToTest = groqKey.trim();
      if (!keyToTest && !settings?.groq_api_key_configured) {
        setGroqTestResult({ valid: false, message: "Please enter or paste your Groq API key first." });
        return;
      }
      setTestingGroq(true);
      setGroqTestResult(null);
      try {
        const res = await api.testApiKey("groq", keyToTest, groqModel);
        setGroqTestResult(res);
        if (res.valid && res.model_tested) {
          setGroqModel(res.model_tested);
        }
      } catch (err: any) {
        setGroqTestResult({ valid: false, message: err.message || "Connection failed" });
      } finally {
        setTestingGroq(false);
      }
    } else if (provider === "gemini") {
      const keyToTest = geminiKey.trim();
      if (!keyToTest && !settings?.gemini_api_key_configured) {
        setGeminiTestResult({ valid: false, message: "Please enter or paste your Gemini API key first." });
        return;
      }
      setTestingGemini(true);
      setGeminiTestResult(null);
      try {
        const res = await api.testApiKey("gemini", keyToTest, geminiModel);
        setGeminiTestResult(res);
        if (res.valid && res.model_tested) {
          setGeminiModel(res.model_tested);
        }
      } catch (err: any) {
        setGeminiTestResult({ valid: false, message: err.message || "Connection failed" });
      } finally {
        setTestingGemini(false);
      }
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8 space-y-8 animate-in fade-in duration-300">
      {/* Top Header */}
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
              <h1 className="text-2xl font-bold text-white tracking-tight">AI Engine & API Configuration</h1>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-violet-500/10 text-violet-400 border border-violet-500/20">
                Multi-Tier Failover
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Manage your Deepgram, Groq, and Gemini credentials. Securely stored in local database.
            </p>
          </div>
        </div>


        {saveSuccess && (
          <div className="flex items-center gap-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 px-4 py-2 text-xs font-semibold text-emerald-400 animate-in fade-in">
            <CheckCircle2 className="h-4 w-4" />
            <span>Settings saved internally & active!</span>
          </div>
        )}
      </div>

      {/* Pipeline Architecture & Resiliency Hierarchy */}
      <div className="rounded-2xl border border-white/10 bg-zinc-950/60 p-5 space-y-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-zinc-300 uppercase tracking-wider">
          <Workflow className="h-4 w-4 text-violet-400" />
          <span>Execution Hierarchy & Fallback Resilience</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-2.5 text-xs">
          <div className="rounded-xl p-3 bg-white/[0.02] border border-white/10">
            <div className="flex items-center justify-between text-cyan-400 font-bold text-[11px] mb-1">
              <span>1. SPEECH RECOGNITION</span>
              <Mic className="h-3.5 w-3.5" />
            </div>
            <p className="font-semibold text-white">Deepgram Nova-3</p>
            <p className="text-[10px] text-zinc-400 mt-0.5">Word timestamps & diarization</p>
          </div>

          <div className="rounded-xl p-3 bg-white/[0.02] border border-white/10">
            <div className="flex items-center justify-between text-amber-400 font-bold text-[11px] mb-1">
              <span>2. PRIMARY REASONING</span>
              <Zap className="h-3.5 w-3.5" />
            </div>
            <p className="font-semibold text-white">Groq Llama 3</p>
            <p className="text-[10px] text-zinc-400 mt-0.5">Sub-second hook discovery</p>
          </div>

          <div className="rounded-xl p-3 bg-white/[0.02] border border-white/10">
            <div className="flex items-center justify-between text-violet-400 font-bold text-[11px] mb-1">
              <span>3. FAILOVER ENGINE</span>
              <Layers className="h-3.5 w-3.5" />
            </div>
            <p className="font-semibold text-white">Google Gemini 2.0</p>
            <p className="text-[10px] text-zinc-400 mt-0.5">Automatic failover on rate limit</p>
          </div>

          <div className="rounded-xl p-3 bg-white/[0.02] border border-white/10">
            <div className="flex items-center justify-between text-emerald-400 font-bold text-[11px] mb-1">
              <span>4. RENDER ENGINE</span>
              <Film className="h-3.5 w-3.5" />
            </div>
            <p className="font-semibold text-white">FFmpeg 9.0 Pro</p>
            <p className="text-[10px] text-zinc-400 mt-0.5">Vertical crop & subtitle burn-in</p>
          </div>
        </div>
      </div>


      <form onSubmit={handleSave} className="space-y-8">
        {/* 1. Global Provider & Model Priority Selectors */}
        <div className="glass-panel rounded-2xl p-6 space-y-6 border border-white/[0.08]">
          <div className="flex items-center gap-2">
            <Sliders className="h-4 w-4 text-violet-400" />
            <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-200">
              Provider Preferences & Engine Selectors
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* AI Reasoning Provider */}
            <div className="space-y-2.5">
              <label className="text-xs font-semibold text-zinc-300">
                Primary AI Reasoning Provider
              </label>
              <div className="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => setAiProvider("groq")}
                  className={`rounded-xl p-3 text-left border transition-all ${
                    aiProvider === "groq"
                      ? "bg-amber-500/15 border-amber-400 text-white shadow-md ring-1 ring-amber-400"
                      : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white"
                  }`}
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    <Zap className="h-3.5 w-3.5 text-amber-400" />
                    <span className="text-xs font-bold text-amber-300">Groq LPU</span>
                  </div>
                  <p className="text-[10px] text-zinc-400">Fastest (0.5s)</p>
                </button>

                <button
                  type="button"
                  onClick={() => setAiProvider("gemini")}
                  className={`rounded-xl p-3 text-left border transition-all ${
                    aiProvider === "gemini"
                      ? "bg-violet-600/20 border-violet-400 text-white shadow-md ring-1 ring-violet-400"
                      : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white"
                  }`}
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    <Cpu className="h-3.5 w-3.5 text-violet-400" />
                    <span className="text-xs font-bold text-violet-300">Gemini 2.0</span>
                  </div>
                  <p className="text-[10px] text-zinc-400">Deep Reasoning</p>
                </button>

                <button
                  type="button"
                  onClick={() => setAiProvider("mock")}
                  className={`rounded-xl p-3 text-left border transition-all ${
                    aiProvider === "mock"
                      ? "bg-emerald-600/15 border-emerald-400 text-white shadow-md ring-1 ring-emerald-400"
                      : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white"
                  }`}
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    <HardDrive className="h-3.5 w-3.5 text-emerald-400" />
                    <span className="text-xs font-bold text-emerald-300">Offline</span>
                  </div>
                  <p className="text-[10px] text-zinc-400">Local Heuristic</p>
                </button>
              </div>
              <p className="text-[10px] text-zinc-500">
                If Groq encounters rate limits or errors, the pipeline automatically falls back to Gemini.
              </p>
            </div>

            {/* Speech-to-Text Transcription Engine */}
            <div className="space-y-2.5">
              <label className="text-xs font-semibold text-zinc-300">
                Speech-to-Text Transcriber Engine
              </label>
              <div className="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => setTranscriberProvider("deepgram")}
                  className={`rounded-xl p-3 text-left border transition-all ${
                    transcriberProvider === "deepgram"
                      ? "bg-cyan-500/15 border-cyan-400 text-white shadow-md ring-1 ring-cyan-400"
                      : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white"
                  }`}
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    <Mic className="h-3.5 w-3.5 text-cyan-400" />
                    <span className="text-xs font-bold text-cyan-300">Deepgram</span>
                  </div>
                  <p className="text-[10px] text-zinc-400">Lightning Fast</p>
                </button>

                <button
                  type="button"
                  onClick={() => setTranscriberProvider("auto")}
                  className={`rounded-xl p-3 text-left border transition-all ${
                    transcriberProvider === "auto"
                      ? "bg-violet-600/20 border-violet-400 text-white shadow-md ring-1 ring-violet-400"
                      : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white"
                  }`}
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    <RefreshCw className="h-3.5 w-3.5 text-violet-400" />
                    <span className="text-xs font-bold text-violet-300">Auto Hybrid</span>
                  </div>
                  <p className="text-[10px] text-zinc-400">Smart Failover</p>
                </button>

                <button
                  type="button"
                  onClick={() => setTranscriberProvider("whisper")}
                  className={`rounded-xl p-3 text-left border transition-all ${
                    transcriberProvider === "whisper"
                      ? "bg-emerald-600/15 border-emerald-400 text-white shadow-md ring-1 ring-emerald-400"
                      : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white"
                  }`}
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    <Cpu className="h-3.5 w-3.5 text-emerald-400" />
                    <span className="text-xs font-bold text-emerald-300">Whisper Local</span>
                  </div>
                  <p className="text-[10px] text-zinc-400">On-Device</p>
                </button>
              </div>

              <p className="text-[10px] text-zinc-500">
                Deepgram delivers timestamp accuracy and handles background noise in seconds.
              </p>
            </div>
          </div>
        </div>

        {/* 2. CARD 1: Deepgram Speech AI (FIRST) */}
        <div className="rounded-2xl border border-cyan-500/25 bg-gradient-to-b from-cyan-950/20 to-black/40 p-6 space-y-5 shadow-lg">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/20 border border-cyan-500/40 text-cyan-400 shadow-md">
                <Mic className="h-5 w-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-white">1. Deepgram Speech AI</h3>
                  <span className="rounded-full bg-cyan-500/10 border border-cyan-500/30 px-2.5 py-0.5 text-[9px] font-bold text-cyan-300">
                    Primary Transcriber
                  </span>
                </div>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Ultra-accurate word-level timestamp transcription and speaker recognition.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {settings?.deepgram_api_key_configured ? (
                <span className="flex items-center gap-1.5 text-[11px] font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full">
                  <CheckCircle2 className="h-3.5 w-3.5" /> Stored ({settings.deepgram_api_key_masked})
                </span>
              ) : (
                <span className="flex items-center gap-1.5 text-[11px] font-medium text-amber-400 bg-amber-500/10 border border-amber-500/20 px-3 py-1 rounded-full">
                  <AlertCircle className="h-3.5 w-3.5" /> Not Configured
                </span>
              )}

              <a
                href="https://console.deepgram.com/"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 px-3 py-1.5 text-xs font-semibold text-cyan-300 hover:text-white hover:bg-cyan-500/20 transition-all"
              >
                <span>Get Deepgram Key</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-12 gap-4">
            <div className="sm:col-span-8 space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-zinc-300">
                  Deepgram API Key
                </label>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handlePasteFromClipboard("deepgram")}
                    className="flex items-center gap-1 text-[11px] text-cyan-400 hover:text-cyan-300 font-medium"
                  >
                    <ClipboardPaste className="h-3 w-3" /> Paste from Clipboard
                  </button>
                  {deepgramKey && (
                    <button
                      type="button"
                      onClick={() => {
                        setDeepgramKey("");
                        setDeepgramTestResult(null);
                        if (typeof window !== "undefined") localStorage.removeItem("clipper_deepgram_key");
                      }}
                      className="flex items-center gap-1 text-[11px] text-zinc-400 hover:text-rose-400 font-medium"
                    >
                      <Trash2 className="h-3 w-3" /> Clear
                    </button>
                  )}
                </div>
              </div>

              <div className="relative">
                <input
                  type={showDeepgramKey ? "text" : "password"}
                  value={deepgramKey}
                  onChange={(e) => setDeepgramKey(e.target.value)}
                  placeholder={settings?.deepgram_api_key_configured ? "Enter new key or keep configured..." : "Paste your Deepgram API Key..."}
                  className="w-full rounded-xl bg-black/50 border border-cyan-500/30 px-4 py-2.5 pr-10 text-xs font-mono text-white placeholder-zinc-500 focus:border-cyan-400 focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => setShowDeepgramKey(!showDeepgramKey)}
                  className="absolute right-3 top-2.5 text-zinc-500 hover:text-zinc-300"
                >
                  {showDeepgramKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <div className="sm:col-span-4 space-y-1.5">
              <label className="text-xs font-medium text-zinc-300">Model</label>
              <select
                value={deepgramModel}
                onChange={(e) => setDeepgramModel(e.target.value)}
                className="w-full rounded-xl bg-black/50 border border-cyan-500/30 px-3 py-2.5 text-xs text-white focus:border-cyan-400 focus:outline-none"
              >
                <option value="nova-3">nova-3 (Highest Accuracy / Recommended)</option>
                <option value="nova-2">nova-2 (General Purpose)</option>
                <option value="nova-2-conversational">nova-2-conversational (Podcasts & Banter)</option>
                <option value="nova-2-meeting">nova-2-meeting (Multi-Speaker)</option>
                <option value="enhanced">enhanced (Enhanced)</option>
              </select>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-white/5">
            <div className="text-xs">
              {deepgramTestResult && (
                <span className={`flex items-center gap-1.5 ${deepgramTestResult.valid ? "text-emerald-400" : "text-rose-400"}`}>
                  {deepgramTestResult.valid ? <CheckCircle2 className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
                  {deepgramTestResult.message}
                </span>
              )}
            </div>

            <button
              type="button"
              onClick={() => handleTestKey("deepgram")}
              disabled={testingDeepgram}
              className="flex items-center gap-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/30 px-3 py-1.5 text-xs font-semibold text-cyan-300 hover:text-white hover:bg-cyan-500/20 transition-all"
            >
              <RefreshCw className={`h-3 w-3 ${testingDeepgram ? "animate-spin" : ""}`} />
              <span>{testingDeepgram ? "Testing Connection..." : "Test Deepgram Connection"}</span>
            </button>
          </div>
        </div>

        {/* 3. CARD 2: Groq Cloud AI (SECOND) */}
        <div className="rounded-2xl border border-amber-500/25 bg-gradient-to-b from-amber-950/20 to-black/40 p-6 space-y-5 shadow-lg">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/20 border border-amber-500/40 text-amber-400 shadow-md">
                <Zap className="h-5 w-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-white">2. Groq Cloud Llama 3 AI</h3>
                  <span className="rounded-full bg-amber-500/10 border border-amber-500/30 px-2.5 py-0.5 text-[9px] font-bold text-amber-300">
                    Fast Candidate Discovery
                  </span>
                </div>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Sub-second candidate discovery and viral moment extraction on Groq LPUs.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {settings?.groq_api_key_configured ? (
                <span className="flex items-center gap-1.5 text-[11px] font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full">
                  <CheckCircle2 className="h-3.5 w-3.5" /> Stored ({settings.groq_api_key_masked})
                </span>
              ) : (
                <span className="flex items-center gap-1.5 text-[11px] font-medium text-amber-400 bg-amber-500/10 border border-amber-500/20 px-3 py-1 rounded-full">
                  <AlertCircle className="h-3.5 w-3.5" /> Not Configured
                </span>
              )}

              <a
                href="https://console.groq.com/keys"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 rounded-xl bg-amber-500/10 border border-amber-500/30 px-3 py-1.5 text-xs font-semibold text-amber-300 hover:text-white hover:bg-amber-500/20 transition-all"
              >
                <span>Get Groq Key</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-12 gap-4">
            <div className="sm:col-span-8 space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-zinc-300">
                  Groq API Key
                </label>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handlePasteFromClipboard("groq")}
                    className="flex items-center gap-1 text-[11px] text-amber-400 hover:text-amber-300 font-medium"
                  >
                    <ClipboardPaste className="h-3 w-3" /> Paste from Clipboard
                  </button>
                  {groqKey && (
                    <button
                      type="button"
                      onClick={() => {
                        setGroqKey("");
                        setGroqTestResult(null);
                        if (typeof window !== "undefined") localStorage.removeItem("clipper_groq_key");
                      }}
                      className="flex items-center gap-1 text-[11px] text-zinc-400 hover:text-rose-400 font-medium"
                    >
                      <Trash2 className="h-3 w-3" /> Clear
                    </button>
                  )}
                </div>
              </div>

              <div className="relative">
                <input
                  type={showGroqKey ? "text" : "password"}
                  value={groqKey}
                  onChange={(e) => setGroqKey(e.target.value)}
                  placeholder={settings?.groq_api_key_configured ? "Enter new key or keep configured..." : "gsk_..."}
                  className="w-full rounded-xl bg-black/50 border border-amber-500/30 px-4 py-2.5 pr-10 text-xs font-mono text-white placeholder-zinc-500 focus:border-amber-400 focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => setShowGroqKey(!showGroqKey)}
                  className="absolute right-3 top-2.5 text-zinc-500 hover:text-zinc-300"
                >
                  {showGroqKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <div className="sm:col-span-4 space-y-1.5">
              <label className="text-xs font-medium text-zinc-300">Model</label>
              <select
                value={groqModel}
                onChange={(e) => setGroqModel(e.target.value)}
                className="w-full rounded-xl bg-black/50 border border-amber-500/30 px-3 py-2.5 text-xs text-white focus:border-amber-400 focus:outline-none"
              >
                <option value="llama-3.1-70b-versatile">llama-3.1-70b-versatile (Recommended)</option>
                <option value="llama-3.1-8b-instant">llama-3.1-8b-instant (Fastest 8B)</option>
                <option value="llama3-70b-8192">llama3-70b-8192 (Llama 3 70B)</option>
                <option value="mixtral-8x7b-32768">mixtral-8x7b-32768 (Mixtral 8x7B)</option>
              </select>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-white/5">
            <div className="text-xs">
              {groqTestResult && (
                <span className={`flex items-center gap-1.5 ${groqTestResult.valid ? "text-emerald-400" : "text-rose-400"}`}>
                  {groqTestResult.valid ? <CheckCircle2 className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
                  {groqTestResult.message}
                </span>
              )}
            </div>

            <button
              type="button"
              onClick={() => handleTestKey("groq")}
              disabled={testingGroq}
              className="flex items-center gap-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 px-3 py-1.5 text-xs font-semibold text-amber-300 hover:text-white hover:bg-amber-500/20 transition-all"
            >
              <RefreshCw className={`h-3 w-3 ${testingGroq ? "animate-spin" : ""}`} />
              <span>{testingGroq ? "Testing Connection..." : "Test Groq Connection"}</span>
            </button>
          </div>
        </div>

        {/* 4. CARD 3: Google Gemini AI (THIRD - FALLBACK & MULTIMODAL) */}
        <div className="rounded-2xl border border-violet-500/25 bg-gradient-to-b from-violet-950/20 to-black/40 p-6 space-y-5 shadow-lg">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/20 border border-violet-500/40 text-violet-400 shadow-md">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-white">3. Google Gemini AI</h3>
                  <span className="rounded-full bg-violet-500/10 border border-violet-500/30 px-2.5 py-0.5 text-[9px] font-bold text-violet-300">
                    Deep Reasoning & Auto-Fallback
                  </span>
                </div>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Deep multi-modal storytelling, 12-factor scoring, and automatic failover when Groq reaches limits.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {settings?.gemini_api_key_configured ? (
                <span className="flex items-center gap-1.5 text-[11px] font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full">
                  <CheckCircle2 className="h-3.5 w-3.5" /> Stored ({settings.gemini_api_key_masked})
                </span>
              ) : (
                <span className="flex items-center gap-1.5 text-[11px] font-medium text-amber-400 bg-amber-500/10 border border-amber-500/20 px-3 py-1 rounded-full">
                  <AlertCircle className="h-3.5 w-3.5" /> Not Configured
                </span>
              )}

              <a
                href="https://aistudio.google.com/app/apikey"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 rounded-xl bg-violet-500/10 border border-violet-500/30 px-3 py-1.5 text-xs font-semibold text-violet-300 hover:text-white hover:bg-violet-500/20 transition-all"
              >
                <span>Get Gemini Key</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-12 gap-4">
            <div className="sm:col-span-8 space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-zinc-300">
                  Gemini API Key
                </label>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handlePasteFromClipboard("gemini")}
                    className="flex items-center gap-1 text-[11px] text-violet-400 hover:text-violet-300 font-medium"
                  >
                    <ClipboardPaste className="h-3 w-3" /> Paste from Clipboard
                  </button>
                  {geminiKey && (
                    <button
                      type="button"
                      onClick={() => {
                        setGeminiKey("");
                        setGeminiTestResult(null);
                        if (typeof window !== "undefined") localStorage.removeItem("clipper_gemini_key");
                      }}
                      className="flex items-center gap-1 text-[11px] text-zinc-400 hover:text-rose-400 font-medium"
                    >
                      <Trash2 className="h-3 w-3" /> Clear
                    </button>
                  )}
                </div>
              </div>

              <div className="relative">
                <input
                  type={showGeminiKey ? "text" : "password"}
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  placeholder={settings?.gemini_api_key_configured ? "Enter new key or keep configured..." : "AIzaSy..."}
                  className="w-full rounded-xl bg-black/50 border border-violet-500/30 px-4 py-2.5 pr-10 text-xs font-mono text-white placeholder-zinc-500 focus:border-violet-400 focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => setShowGeminiKey(!showGeminiKey)}
                  className="absolute right-3 top-2.5 text-zinc-500 hover:text-zinc-300"
                >
                  {showGeminiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <div className="sm:col-span-4 space-y-1.5">
              <label className="text-xs font-medium text-zinc-300">Model</label>
              <select
                value={geminiModel}
                onChange={(e) => setGeminiModel(e.target.value)}
                className="w-full rounded-xl bg-black/50 border border-violet-500/30 px-3 py-2.5 text-xs text-white focus:border-violet-400 focus:outline-none"
              >
                <option value="gemini-2.0-flash">gemini-2.0-flash (Recommended / Fast)</option>
                <option value="gemini-1.5-flash">gemini-1.5-flash (Standard Flash)</option>
                <option value="gemini-1.5-pro">gemini-1.5-pro (High Reasoning)</option>
              </select>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-white/5">
            <div className="text-xs">
              {geminiTestResult && (
                <span className={`flex items-center gap-1.5 ${geminiTestResult.valid ? "text-emerald-400" : "text-rose-400"}`}>
                  {geminiTestResult.valid ? <CheckCircle2 className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
                  {geminiTestResult.message}
                </span>
              )}
            </div>

            <button
              type="button"
              onClick={() => handleTestKey("gemini")}
              disabled={testingGemini}
              className="flex items-center gap-1.5 rounded-lg bg-violet-500/10 border border-violet-500/30 px-3 py-1.5 text-xs font-semibold text-violet-300 hover:text-white hover:bg-violet-500/20 transition-all"
            >
              <RefreshCw className={`h-3 w-3 ${testingGemini ? "animate-spin" : ""}`} />
              <span>{testingGemini ? "Testing Connection..." : "Test Gemini Connection"}</span>
            </button>
          </div>
        </div>

        {/* 4.5 Hook Strategy Default */}
        <div className="glass-panel rounded-2xl p-6 space-y-4 border border-violet-500/20 bg-gradient-to-b from-violet-950/20 to-transparent">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-red-500/20 text-red-400 border border-red-500/30 font-bold text-sm">
                ⚡
              </div>
              <div>
                <h3 className="text-sm font-semibold uppercase tracking-wider text-zinc-200 flex items-center gap-2">
                  Default Hook & Story Structure
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-500/20 text-red-300 border border-red-500/30">
                    Dual Option
                  </span>
                </h3>
                <p className="text-xs text-zinc-400">Choose default editing structure applied when auto-generating clips</p>
              </div>
            </div>
            <span className="text-xs font-mono px-2.5 py-1 rounded bg-zinc-900 border border-white/10 text-zinc-300">
              {defaultHookStrategy === "teaser_climax_hook" ? "⚡ 5s Climax Teaser First" : "▶ Direct Chronological Cut"}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
            <div
              onClick={() => setDefaultHookStrategy("teaser_climax_hook")}
              className={`cursor-pointer rounded-xl p-4.5 border transition-all duration-300 flex flex-col justify-between ${
                defaultHookStrategy === "teaser_climax_hook"
                  ? "bg-gradient-to-br from-red-500/15 via-violet-600/15 to-zinc-900/60 border-red-500/60 shadow-xl shadow-red-500/10 ring-1 ring-red-500/40"
                  : "bg-white/[0.02] border-white/10 hover:border-white/20 hover:bg-white/[0.04]"
              }`}
            >
              <div className="flex items-start justify-between gap-3 mb-2.5">
                <div className="flex items-center gap-2.5">
                  <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${
                    defaultHookStrategy === "teaser_climax_hook" ? "bg-red-500 text-white" : "bg-white/10 text-zinc-400"
                  }`}>
                    <Zap className="h-4 w-4" />
                  </div>
                  <div>
                    <h5 className="font-semibold text-white text-xs sm:text-sm flex items-center gap-1.5">
                      5s Climax Teaser Hook
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300">
                        Viral Meta
                      </span>
                    </h5>
                    <span className="text-[11px] text-red-400 font-medium">In Medias Res Cold-Open</span>
                  </div>
                </div>
                {defaultHookStrategy === "teaser_climax_hook" && (
                  <CheckCircle2 className="h-5 w-5 text-red-400 shrink-0" />
                )}
              </div>
              <p className="text-xs text-zinc-300 leading-relaxed mb-3">
                Slices the most intense 4–5s fight, clash, scream, or shocking revelation from the middle, plays it first to catch viewers off-guard, then rewinds to build up the full story.
              </p>
              <div className="flex items-center gap-1.5 text-[10px] text-zinc-400 bg-black/40 rounded-lg p-2 border border-white/5 font-mono">
                <span className="text-red-400 font-bold">[0-5s: PEAK CLASH]</span>
                <span>➔</span>
                <span className="text-zinc-300">[Story Build-up & Payoff]</span>
              </div>
            </div>

            <div
              onClick={() => setDefaultHookStrategy("direct_chronological")}
              className={`cursor-pointer rounded-xl p-4.5 border transition-all duration-300 flex flex-col justify-between ${
                defaultHookStrategy === "direct_chronological"
                  ? "bg-gradient-to-br from-violet-500/15 to-zinc-900/60 border-violet-500/60 shadow-xl shadow-violet-500/10 ring-1 ring-violet-500/40"
                  : "bg-white/[0.02] border-white/10 hover:border-white/20 hover:bg-white/[0.04]"
              }`}
            >
              <div className="flex items-start justify-between gap-3 mb-2.5">
                <div className="flex items-center gap-2.5">
                  <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${
                    defaultHookStrategy === "direct_chronological" ? "bg-violet-500 text-white" : "bg-white/10 text-zinc-400"
                  }`}>
                    <Play className="h-4 w-4" />
                  </div>
                  <div>
                    <h5 className="font-semibold text-white text-xs sm:text-sm flex items-center gap-1.5">
                      Direct Chronological Cut
                    </h5>
                    <span className="text-[11px] text-violet-400 font-medium">Traditional Linear Narrative</span>
                  </div>
                </div>
                {defaultHookStrategy === "direct_chronological" && (
                  <CheckCircle2 className="h-5 w-5 text-violet-400 shrink-0" />
                )}
              </div>
              <p className="text-xs text-zinc-300 leading-relaxed mb-3">
                Cuts the video directly from start to finish in normal order without moving or splicing scenes. Best for clean stories, tutorials, and monologues.
              </p>
              <div className="flex items-center gap-1.5 text-[10px] text-zinc-400 bg-black/40 rounded-lg p-2 border border-white/5 font-mono">
                <span className="text-violet-400 font-bold">[0s: Start]</span>
                <span>➔</span>
                <span className="text-zinc-300">[Progression]</span>
                <span>➔</span>
                <span className="text-emerald-400">[Payoff]</span>
              </div>
            </div>
          </div>
        </div>

        {/* 5. Framing, Blur & Aspect Ratio Presets */}
        <div className="glass-panel rounded-2xl p-6 space-y-5 border border-white/[0.08]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sliders className="h-4 w-4 text-cyan-400" />
              <h3 className="text-sm font-semibold uppercase tracking-wider text-zinc-300">
                Default Video Framing & Aspect Ratio
              </h3>
            </div>
            <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
              {defaultFramingMode === "crop_9_16" ? "9:16 Full Crop" : defaultFramingMode === "blur_fit_9_16" ? "16:9 in 9:16 Blurred Canvas" : "16:9 Widescreen"}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div
              onClick={() => setDefaultFramingMode("crop_9_16")}
              className={`rounded-xl p-4 cursor-pointer border transition-all ${
                defaultFramingMode === "crop_9_16"
                  ? "bg-violet-500/15 border-violet-500 text-white shadow-lg shadow-violet-500/10"
                  : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white hover:border-white/20"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <Smartphone className="h-5 w-5 text-violet-400" />
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-white/10 text-zinc-300">Full 9:16</span>
              </div>
              <h4 className="text-xs font-bold text-white">Vertical Dynamic Crop</h4>
              <p className="text-[11px] text-violet-400 font-medium mt-0.5">TikTok & Reels</p>
              <p className="text-[11px] text-zinc-400 mt-2 leading-relaxed">
                Smart reframing that fills entire 9:16 vertical canvas.
              </p>
            </div>

            <div
              onClick={() => setDefaultFramingMode("blur_fit_9_16")}
              className={`rounded-xl p-4 cursor-pointer border transition-all ${
                defaultFramingMode === "blur_fit_9_16"
                  ? "bg-violet-500/15 border-violet-500 text-white shadow-lg shadow-violet-500/10"
                  : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white hover:border-white/20"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <Maximize2 className="h-5 w-5 text-cyan-400" />
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300">Best for Podcasts</span>
              </div>
              <h4 className="text-xs font-bold text-white">16:9 in 9:16 (Blurred Canvas)</h4>
              <p className="text-[11px] text-cyan-400 font-medium mt-0.5">Podcasts & Interviews</p>
              <p className="text-[11px] text-zinc-400 mt-2 leading-relaxed">
                Keeps complete 16:9 widescreen video centered with an aesthetic frosted blurred background.
              </p>
            </div>

            <div
              onClick={() => setDefaultFramingMode("original_16_9")}
              className={`rounded-xl p-4 cursor-pointer border transition-all ${
                defaultFramingMode === "original_16_9"
                  ? "bg-violet-500/15 border-violet-500 text-white shadow-lg shadow-violet-500/10"
                  : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white hover:border-white/20"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <Monitor className="h-5 w-5 text-emerald-400" />
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-white/10 text-zinc-300">Widescreen</span>
              </div>
              <h4 className="text-xs font-bold text-white">Native 16:9 Landscape</h4>
              <p className="text-[11px] text-emerald-400 font-medium mt-0.5">YouTube & Twitter</p>
              <p className="text-[11px] text-zinc-400 mt-2 leading-relaxed">
                Preserves native landscape aspect ratio with zero vertical transformation.
              </p>
            </div>

          </div>

          {/* If Blurred Canvas is chosen, show Blur Ratio Controls */}
          {defaultFramingMode === "blur_fit_9_16" && (
            <div className="rounded-xl bg-black/40 border border-cyan-500/30 p-4 space-y-3.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-cyan-300 flex items-center gap-2">
                  <span>Default Background Blur Radius:</span>
                  <span className="font-mono text-white bg-cyan-500/20 px-2 py-0.5 rounded text-xs">
                    {defaultBlurRadius}px
                  </span>
                </label>
                <span className="text-xs text-zinc-400">Softened gaussian-style box blur</span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {[
                  { label: "Light", radius: 15, desc: "Subtle motion" },
                  { label: "Medium", radius: 30, desc: "Standard aesthetic" },
                  { label: "Heavy", radius: 50, desc: "Frosted glass" },
                  { label: "Ultra", radius: 80, desc: "Ambient glow" },
                ].map((b) => (
                  <button
                    key={b.radius}
                    type="button"
                    onClick={() => setDefaultBlurRadius(b.radius)}
                    className={`rounded-lg py-2 px-3 text-left border transition-all ${
                      defaultBlurRadius === b.radius
                        ? "bg-cyan-500/20 border-cyan-400 text-white shadow-sm"
                        : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white hover:border-white/20"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold">{b.label}</span>
                      <span className="text-[10px] font-mono text-cyan-400">{b.radius}px</span>
                    </div>
                    <p className="text-[10px] text-zinc-500 mt-0.5">{b.desc}</p>
                  </button>
                ))}
              </div>

              <div className="space-y-1.5 pt-1">
                <input
                  type="range"
                  min={10}
                  max={80}
                  step={5}
                  value={defaultBlurRadius}
                  onChange={(e) => setDefaultBlurRadius(Number(e.target.value))}
                  className="w-full accent-cyan-400 h-1.5 bg-zinc-800 rounded-lg cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-zinc-500">
                  <span>10px (Sharpest)</span>
                  <span>30px (Default)</span>
                  <span>50px (Heavy)</span>
                  <span>80px (Softest)</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 6. Subtitle Position & Placement Defaults */}
        <div className="glass-panel rounded-2xl p-6 space-y-5 border border-white/[0.08]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Subtitles className="h-4 w-4 text-violet-400" />
              <h3 className="text-sm font-semibold uppercase tracking-wider text-zinc-300">
                Default Subtitle Screen Position
              </h3>
            </div>
            <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-violet-500/10 text-violet-300 border border-violet-500/20">
              {defaultSubtitlePosition}% from Top ({defaultSubtitlePosition <= 25 ? "Top Banner" : defaultSubtitlePosition <= 45 ? "Upper-Mid" : defaultSubtitlePosition <= 60 ? "Center" : defaultSubtitlePosition <= 80 ? "Lower-Third (Standard)" : "Bottom Anchor"})
            </span>
          </div>

          <p className="text-xs text-zinc-400">
            Set where burned-in animated subtitles are positioned vertically on export by default.
          </p>

          {/* Position Presets */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
            {[
              { label: "Top Banner", pos: 20, desc: "Headers / gaming" },
              { label: "Upper-Mid", pos: 35, desc: "High clearance" },
              { label: "Center Screen", pos: 50, desc: "Cinematic focal" },
              { label: "Lower-Third", pos: 75, desc: "TikTok / Reels Standard" },
              { label: "Bottom Anchor", pos: 88, desc: "Maximum low" },
            ].map((p) => (
              <button
                key={p.pos}
                type="button"
                onClick={() => setDefaultSubtitlePosition(p.pos)}
                className={`rounded-xl p-3 text-left border transition-all ${
                  defaultSubtitlePosition === p.pos
                    ? "bg-violet-600/25 border-violet-400 text-white shadow-md"
                    : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white hover:border-white/20"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold">{p.label}</span>
                  <span className="text-[10px] font-mono text-violet-400">{p.pos}%</span>
                </div>
                <p className="text-[10px] text-zinc-500 mt-1">{p.desc}</p>
              </button>
            ))}
          </div>

          {/* Slider with Mini Interactive Phone Mockup */}
          <div className="flex items-center gap-4 pt-2">
            <div className="flex-1 space-y-1.5">
              <input
                type="range"
                min={15}
                max={88}
                step={1}
                value={defaultSubtitlePosition}
                onChange={(e) => setDefaultSubtitlePosition(Number(e.target.value))}
                className="w-full accent-violet-500 h-1.5 bg-zinc-800 rounded-lg cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-zinc-500">
                <span>Top (15%)</span>
                <span>Upper (35%)</span>
                <span>Center (50%)</span>
                <span>Lower-Third (75%)</span>
                <span>Bottom (88%)</span>
              </div>
            </div>

            {/* Mini phone screen preview */}
            <div className="w-12 h-20 rounded-xl bg-black/80 border border-violet-500/40 relative overflow-hidden flex-shrink-0 shadow-xl flex items-center justify-center">
              {defaultAddHookHeader && (
                <div
                  className="absolute left-1.5 right-1.5 h-1.5 bg-amber-400 rounded-full shadow-md shadow-amber-400/80 transition-all duration-150"
                  style={{ top: `${defaultHookHeaderPosition}%` }}
                />
              )}
              <div
                className="absolute left-1.5 right-1.5 h-2 bg-yellow-400 rounded-full shadow-md shadow-yellow-400/60 transition-all duration-150"
                style={{ top: `${defaultSubtitlePosition}%` }}
              />
            </div>
          </div>
        </div>

        {/* 7. Default Sticky TikTok Hook Header Defaults */}
        <div className="glass-panel rounded-2xl p-6 space-y-5 border border-white/[0.08]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Flame className="h-4 w-4 text-amber-400" />
              <div>
                <div className="flex items-center gap-1.5">
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-zinc-300">
                    Default Sticky TikTok Hook Header
                  </h3>
                  <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">VIRAL CREATOR</span>
                </div>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setDefaultAddHookHeader(!defaultAddHookHeader)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                defaultAddHookHeader ? "bg-amber-500" : "bg-zinc-800"
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  defaultAddHookHeader ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
          </div>

          <p className="text-xs text-zinc-400">
            Automatically burn a bold TikTok-style title overlay with contextual emojis throughout the entire video to maximize viewer retention.
          </p>

          {defaultAddHookHeader && (
            <div className="space-y-4 pt-2 border-t border-white/5 animate-in fade-in duration-200">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-zinc-300">Default Hook Screen Position</span>
                <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20">
                  {defaultHookHeaderPosition}% from Top ({defaultHookHeaderPosition <= 15 ? "Top Banner (Recommended)" : defaultHookHeaderPosition <= 30 ? "Upper-Third" : defaultHookHeaderPosition <= 55 ? "Center" : "Bottom"})
                </span>
              </div>

              {/* Position Presets */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {[
                  { label: "Top Banner", pos: 12, desc: "Standard TikTok header" },
                  { label: "Upper 3rd", pos: 25, desc: "Above subject head" },
                  { label: "Center Screen", pos: 50, desc: "Mid-frame focus" },
                  { label: "Bottom Anchor", pos: 85, desc: "Lower watermark" },
                ].map((p) => (
                  <button
                    key={p.pos}
                    type="button"
                    onClick={() => setDefaultHookHeaderPosition(p.pos)}
                    className={`rounded-xl p-3 text-left border transition-all ${
                      defaultHookHeaderPosition === p.pos
                        ? "bg-amber-500/25 border-amber-400 text-white shadow-md"
                        : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white hover:border-white/20"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold">{p.label}</span>
                      <span className="text-[10px] font-mono text-amber-400">{p.pos}%</span>
                    </div>
                    <p className="text-[10px] text-zinc-500 mt-1">{p.desc}</p>
                  </button>
                ))}
              </div>

              {/* Slider with Mini Interactive Phone Mockup */}
              <div className="flex items-center gap-4 pt-2">
                <div className="flex-1 space-y-1.5">
                  <input
                    type="range"
                    min={8}
                    max={85}
                    step={1}
                    value={defaultHookHeaderPosition}
                    onChange={(e) => setDefaultHookHeaderPosition(Number(e.target.value))}
                    className="w-full accent-amber-400 h-1.5 bg-zinc-800 rounded-lg cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-zinc-500">
                    <span>Top Banner (8%)</span>
                    <span>Upper (25%)</span>
                    <span>Center (50%)</span>
                    <span>Bottom (85%)</span>
                  </div>
                </div>

                {/* Mini phone screen preview */}
                <div className="w-12 h-20 rounded-xl bg-black/80 border border-amber-500/40 relative overflow-hidden flex-shrink-0 shadow-xl flex items-center justify-center">
                  <div
                    className="absolute left-1.5 right-1.5 h-1.5 bg-amber-400 rounded-full shadow-md shadow-amber-400/80 transition-all duration-150"
                    style={{ top: `${defaultHookHeaderPosition}%` }}
                  />
                  <div
                    className="absolute left-1.5 right-1.5 h-1.5 bg-yellow-300/50 rounded-full transition-all duration-150"
                    style={{ top: `${defaultSubtitlePosition}%` }}
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 8. Default Watermark / Logo Eraser */}
        <div className="glass-panel rounded-2xl p-6 space-y-5 border border-white/[0.08]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Eraser className="h-4 w-4 text-cyan-400" />
              <div>
                <div className="flex items-center gap-1.5">
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-zinc-300">
                    Default Watermark &amp; Logo Eraser
                  </h3>
                  <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">DELOGO</span>
                </div>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setDefaultRemoveWatermark(!defaultRemoveWatermark)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                defaultRemoveWatermark ? "bg-cyan-500" : "bg-zinc-800"
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  defaultRemoveWatermark ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
          </div>

          <p className="text-xs text-zinc-400">
            Automatically detect and interpolate channel logos, broadcast watermarks, or corner trademarks prior to 9:16 vertical re-framing.
          </p>

          {defaultRemoveWatermark && (
            <div className="space-y-4 pt-2 border-t border-white/5 animate-in fade-in duration-200">
              <span className="text-xs font-semibold text-zinc-300">Default Watermark Location</span>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {[
                  { label: "✨ Auto Detect (AI)", value: "auto", desc: "Computer vision scan & remove" },
                  { label: "TikTok Bounce", value: "tiktok_bounce", desc: "Top-Left & Bottom-Right" },
                  { label: "Top Right", value: "top_right", desc: "Default TV / YouTube corner" },
                  { label: "Bottom Right", value: "bottom_right", desc: "Lower watermark placement" },
                  { label: "Top Left", value: "top_left", desc: "Network bug / station ID" },
                  { label: "Bottom Left", value: "bottom_left", desc: "Lower corner branding" },
                  { label: "All 4 Corners", value: "all_corners", desc: "Full 4-corner wipe" },
                ].map((pos) => (
                  <button
                    key={pos.value}
                    type="button"
                    onClick={() => setDefaultWatermarkPosition(pos.value)}
                    className={`rounded-xl p-3 text-left border transition-all ${
                      defaultWatermarkPosition === pos.value
                        ? "bg-cyan-500/25 border-cyan-400 text-white shadow-md"
                        : "bg-white/[0.02] border-white/10 text-zinc-400 hover:text-white hover:border-white/20"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold">{pos.label}</span>
                    </div>
                    <p className="text-[10px] text-zinc-500 mt-1">{pos.desc}</p>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 9. Studio Enhancement & Color Boost */}
        <div className="glass-panel rounded-2xl p-6 space-y-5 border border-white/[0.08]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Wand2 className="h-4 w-4 text-emerald-400" />
              <div>
                <div className="flex items-center gap-1.5">
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-zinc-300">
                    Studio Enhancement &amp; Color Boost
                  </h3>
                  <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">AI EDITING</span>
                </div>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setDefaultEnhanceQuality(!defaultEnhanceQuality)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                defaultEnhanceQuality ? "bg-emerald-500" : "bg-zinc-800"
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  defaultEnhanceQuality ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
          </div>

          <p className="text-xs text-zinc-400">
            Automatically applies high-quality unsharp mask sharpening, contrast/saturation boost, and EBU R128 loudness normalization for crisp mobile screen playback.
          </p>
        </div>

        {/* Save Bar */}
        <div className="flex items-center justify-between pt-4 border-t border-white/[0.08]">
          <div className="flex items-center gap-2 text-xs text-zinc-400">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            <span>Credentials stored locally in internal database and .env configuration.</span>
          </div>

          <button
            type="submit"
            disabled={isSaving}
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 px-6 py-2.5 text-xs font-bold text-white shadow-lg shadow-violet-500/25 hover:from-violet-500 hover:to-indigo-500 disabled:opacity-50 transition-all active:scale-95"
          >
            {isSaving ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                <span>Saving Settings...</span>
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                <span>Save & Apply Settings</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
