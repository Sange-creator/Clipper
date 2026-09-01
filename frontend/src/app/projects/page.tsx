"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  FolderPlus,
  Layers,
  Film,
  Sparkles,
  ArrowRight,
  Plus,
  X,
  Mic,
  Zap,
  Trash2,
  CheckSquare,
  Square,
  AlertTriangle,
} from "lucide-react";
import { api } from "@/lib/api";
import { ProjectListItem } from "@/lib/types";

export default function ProjectsListPage() {
  const [projects, setProjects] = useState<ProjectListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [name, setName] = useState("");
  const [mode, setMode] = useState<"podcast" | "viral_moments">("podcast");
  const [description, setDescription] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  // Selection & Deletion state
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteConfirmTarget, setDeleteConfirmTarget] = useState<{ id?: string; name?: string; count?: number } | null>(null);

  const fetchProjects = async () => {
    try {
      const data = await api.listProjects();
      setProjects(data);
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setIsCreating(true);
    try {
      const newProj = await api.createProject(name, mode, description);
      setProjects([newProj, ...projects]);
      setIsModalOpen(false);
      setName("");
      setDescription("");
    } finally {
      setIsCreating(false);
    }
  };

  const toggleSelect = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selectedIds.length === projects.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(projects.map((p) => p.id));
    }
  };

  const handleDeleteSingle = async (id: string) => {
    setIsDeleting(true);
    try {
      await api.deleteProject(id);
      setProjects((prev) => prev.filter((p) => p.id !== id));
      setSelectedIds((prev) => prev.filter((i) => i !== id));
      setDeleteConfirmTarget(null);
    } catch (err: any) {
      alert(err.message || "Failed to delete project");
    } finally {
      setIsDeleting(false);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) return;
    setIsDeleting(true);
    try {
      await api.bulkDeleteProjects(selectedIds);
      setProjects((prev) => prev.filter((p) => !selectedIds.includes(p.id)));
      setSelectedIds([]);
      setDeleteConfirmTarget(null);
    } catch (err: any) {
      alert(err.message || "Failed to delete projects");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/[0.08] pb-6">
        <div className="flex items-center gap-4">
          <div className="relative flex-shrink-0">
            <div className="absolute -inset-1 rounded-xl bg-gradient-to-r from-violet-600 to-cyan-500 opacity-40 blur" />
            <div className="relative h-12 w-12 rounded-xl bg-[#0f1222] border border-violet-500/30 p-1.5 shadow-lg">
              <img src="/logo.svg" alt="Clipper Pro" className="w-full h-full" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-white tracking-tight">Project Workspaces</h1>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-violet-500/10 text-violet-400 border border-violet-500/20">
                Batch Mode
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Batch process 20–30+ long videos with cross-video global candidate discovery
            </p>
          </div>
        </div>


        <div className="flex items-center gap-3">
          {projects.length > 0 && (
            <button
              onClick={toggleSelectAll}
              className="flex items-center gap-1.5 rounded-xl bg-white/[0.04] border border-white/10 px-3.5 py-2.5 text-xs font-semibold text-zinc-300 hover:text-white hover:bg-white/10 transition-all"
            >
              {selectedIds.length === projects.length ? (
                <>
                  <Square className="h-3.5 w-3.5" />
                  <span>Deselect All</span>
                </>
              ) : (
                <>
                  <CheckSquare className="h-3.5 w-3.5" />
                  <span>Select All ({projects.length})</span>
                </>
              )}
            </button>
          )}

          {selectedIds.length > 0 && (
            <button
              onClick={() => setDeleteConfirmTarget({ count: selectedIds.length })}
              className="flex items-center gap-1.5 rounded-xl bg-rose-600/20 border border-rose-500/40 px-4 py-2.5 text-xs font-semibold text-rose-400 hover:bg-rose-600 hover:text-white transition-all animate-in fade-in"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span>Delete Selected ({selectedIds.length})</span>
            </button>
          )}

          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 px-5 py-2.5 text-xs font-semibold text-white shadow-lg shadow-violet-500/20 hover:from-violet-500 hover:to-indigo-500 transition-all self-start sm:self-auto"
          >
            <Plus className="h-4 w-4" />
            <span>New Project</span>
          </button>
        </div>
      </div>

      {/* Projects Grid */}
      {isLoading ? (
        <div className="py-20 text-center space-y-3">
          <div className="h-8 w-8 border-2 border-violet-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-zinc-400">Loading workspaces...</p>
        </div>
      ) : projects.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-white/15 bg-white/[0.02] p-12 text-center space-y-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/[0.04] border border-white/10 mx-auto">
            <FolderPlus className="h-6 w-6 text-zinc-400" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-white">No Projects Yet</h3>
            <p className="text-xs text-zinc-400 max-w-sm mx-auto">
              Create a project workspace to upload and rank dozens of videos together in a single batch.
            </p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-2 text-xs font-semibold text-white hover:bg-violet-500 transition-colors"
          >
            <Plus className="h-4 w-4" /> Create First Project
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((proj) => {
            const isSelected = selectedIds.includes(proj.id);
            return (
              <div
                key={proj.id}
                className={`group relative flex flex-col rounded-2xl border transition-all duration-300 ${
                  isSelected
                    ? "bg-violet-950/20 border-violet-500 ring-1 ring-violet-500/50 shadow-lg shadow-violet-500/10"
                    : "bg-white/[0.02] border-white/10 hover:border-violet-500/50 hover:bg-white/[0.04]"
                }`}
              >
                {/* Checkbox and Delete Actions Header */}
                <div className="flex items-center justify-between p-4 pb-0">
                  <button
                    type="button"
                    onClick={(e) => toggleSelect(proj.id, e)}
                    className="flex items-center gap-2 text-xs text-zinc-400 hover:text-white transition-colors"
                  >
                    {isSelected ? (
                      <CheckSquare className="h-4 w-4 text-violet-400" />
                    ) : (
                      <Square className="h-4 w-4 text-zinc-600 group-hover:text-zinc-400" />
                    )}
                    <span className="text-[11px] font-medium">{isSelected ? "Selected" : "Select"}</span>
                  </button>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      e.preventDefault();
                      setDeleteConfirmTarget({ id: proj.id, name: proj.name });
                    }}
                    className="flex h-7 w-7 items-center justify-center rounded-lg text-zinc-500 hover:text-rose-400 hover:bg-rose-500/10 transition-all opacity-80 group-hover:opacity-100"
                    title="Delete Project Workspace"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>

                <Link
                  href={`/projects/${proj.id}`}
                  className="flex flex-col flex-1 p-6 pt-3"
                >
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div>
                      <h3 className="text-base font-bold text-white group-hover:text-violet-300 transition-colors line-clamp-1">
                        {proj.name}
                      </h3>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                          proj.mode === "viral_moments"
                            ? "bg-amber-500/10 border border-amber-500/30 text-amber-300"
                            : "bg-violet-500/10 border border-violet-500/30 text-violet-300"
                        }`}>
                          {proj.mode === "viral_moments" ? <Zap className="h-2.5 w-2.5" /> : <Mic className="h-2.5 w-2.5" />}
                          {proj.mode === "viral_moments" ? "Viral Moments" : "Podcast"}
                        </span>
                      </div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-zinc-500 group-hover:text-violet-400 group-hover:translate-x-0.5 transition-all shrink-0 mt-1" />
                  </div>

                  <p className="text-xs text-zinc-400 line-clamp-2 mb-6">
                    {proj.description || "Batch video clipping workspace."}
                  </p>

                  <div className="mt-auto flex items-center justify-between border-t border-white/5 pt-4 text-xs text-zinc-500">
                    <div className="flex items-center gap-3">
                      <span className="flex items-center gap-1 font-medium text-zinc-300">
                        <Film className="h-3.5 w-3.5 text-violet-400" />
                        {proj.video_count} Videos
                      </span>
                      <span className="flex items-center gap-1 font-medium text-zinc-300">
                        <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
                        {proj.clips_count} Clips
                      </span>
                    </div>
                    <span>{new Date(proj.created_at).toLocaleDateString()}</span>
                  </div>
                </Link>
              </div>
            );
          })}
        </div>
      )}

      {/* Creation Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="relative w-full max-w-md rounded-2xl bg-zinc-900 border border-white/10 p-6 shadow-2xl space-y-6">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-5 right-5 text-zinc-400 hover:text-white"
            >
              <X className="h-5 w-5" />
            </button>

            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <FolderPlus className="h-5 w-5 text-violet-400" />
                <h2 className="text-lg font-bold text-white">Create Project Workspace</h2>
              </div>
              <p className="text-xs text-zinc-400">
                Group multiple video files to discover top clips across all footage.
              </p>
            </div>

            <form onSubmit={handleCreate} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-zinc-300">
                  Project Name
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Founder Podcast Season 1"
                  className="w-full rounded-xl bg-black/40 border border-white/10 px-4 py-2.5 text-xs text-white placeholder-zinc-500 focus:border-violet-500 focus:outline-none"
                />
              </div>

              {/* Mode Picker */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-zinc-300">
                  Clipping Mode
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setMode("podcast")}
                    className={`rounded-xl p-3 text-left border transition-all ${
                      mode === "podcast"
                        ? "bg-violet-600/20 border-violet-500 text-white"
                        : "bg-white/[0.02] border-white/10 text-zinc-400 hover:border-white/20"
                    }`}
                  >
                    <div className="flex items-center gap-1.5 mb-1 font-semibold text-xs text-violet-300">
                      <Mic className="h-3.5 w-3.5" /> Podcast
                    </div>
                    <p className="text-[10px] text-zinc-400">Interviews, debates & banter</p>
                  </button>

                  <button
                    type="button"
                    onClick={() => setMode("viral_moments")}
                    className={`rounded-xl p-3 text-left border transition-all ${
                      mode === "viral_moments"
                        ? "bg-amber-500/20 border-amber-500 text-white"
                        : "bg-white/[0.02] border-white/10 text-zinc-400 hover:border-white/20"
                    }`}
                  >
                    <div className="flex items-center gap-1.5 mb-1 font-semibold text-xs text-amber-300">
                      <Zap className="h-3.5 w-3.5" /> Viral Moments
                    </div>
                    <p className="text-[10px] text-zinc-400">Documentary, commentary & streams</p>
                  </button>
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-zinc-300">
                  Description (Optional)
                </label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="e.g. 25 raw interview files for YouTube Shorts & TikTok"
                  className="w-full rounded-xl bg-black/40 border border-white/10 px-4 py-2 text-xs text-white placeholder-zinc-500 focus:border-violet-500 focus:outline-none resize-none"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="rounded-xl px-4 py-2 text-xs font-semibold text-zinc-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isCreating}
                  className="rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 px-5 py-2.5 text-xs font-semibold text-white shadow-lg shadow-violet-500/20 hover:from-violet-500 hover:to-indigo-500 disabled:opacity-50 transition-all"
                >
                  {isCreating ? "Creating..." : "Create Workspace"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirmTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="relative w-full max-w-md rounded-2xl bg-zinc-900 border border-rose-500/30 p-6 shadow-2xl space-y-5">
            <div className="flex items-center gap-3 text-rose-400">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500/10 border border-rose-500/20">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">
                  {deleteConfirmTarget.count
                    ? `Delete ${deleteConfirmTarget.count} Projects?`
                    : `Delete "${deleteConfirmTarget.name}"?`}
                </h3>
                <p className="text-xs text-zinc-400">This action cannot be undone.</p>
              </div>
            </div>

            <p className="text-xs text-zinc-300 leading-relaxed">
              All associated videos, transcription records, candidates, and rendered clips for this workspace will be permanently removed.
            </p>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setDeleteConfirmTarget(null)}
                className="rounded-xl px-4 py-2 text-xs font-semibold text-zinc-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isDeleting}
                onClick={() => {
                  if (deleteConfirmTarget.id) {
                    handleDeleteSingle(deleteConfirmTarget.id);
                  } else {
                    handleBulkDelete();
                  }
                }}
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
