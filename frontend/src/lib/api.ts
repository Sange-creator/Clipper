import {
  AdminMetricsResponse,
  BatchUploadResponse,
  CandidateDetail,
  JobCreatePayload,
  JobStatusResponse,
  ProjectDetailResponse,
  ProjectListItem,
  ProjectProcessPayload,
  RenderedClipResponse,
  SettingsResponse,
  SettingsUpdateRequest,
  TestApiKeyResponse,
  VideoInfo,
  VideoUploadResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export const api = {
  getBaseUrl(): string {
    return API_BASE;
  },

  // Video uploads
  async getRecentVideos(limit = 10): Promise<VideoInfo[]> {
    try {
      const res = await fetch(`${API_BASE}/upload/recent?limit=${limit}`);
      if (!res.ok) return [];
      return res.json();
    } catch {
      return [];
    }
  },

  async uploadVideo(file: File): Promise<VideoUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(`${API_BASE}/upload`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(err.detail || "Upload failed");
    }

    return res.json();
  },

  async batchUploadVideos(projectId: string, files: File[]): Promise<BatchUploadResponse> {
    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));

    const res = await fetch(`${API_BASE}/upload/batch?project_id=${projectId}`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Batch upload failed" }));
      throw new Error(err.detail || "Batch upload failed");
    }

    return res.json();
  },

  // Projects API
  async listProjects(): Promise<ProjectListItem[]> {
    const res = await fetch(`${API_BASE}/projects`);
    if (!res.ok) throw new Error("Failed to fetch projects");
    return res.json();
  },

  async createProject(name: string, mode: "podcast" | "viral_moments" = "podcast", description: string = ""): Promise<ProjectListItem> {
    const res = await fetch(`${API_BASE}/projects`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, mode, description }),
    });
    if (!res.ok) throw new Error("Failed to create project");
    return res.json();
  },

  async getProject(id: string): Promise<ProjectDetailResponse> {
    const res = await fetch(`${API_BASE}/projects/${id}`);
    if (!res.ok) throw new Error("Failed to fetch project details");
    return res.json();
  },

  async processProject(projectId: string, params: ProjectProcessPayload): Promise<{ job_id: string; status: string }> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/process`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error("Failed to trigger project processing");
    return res.json();
  },

  async deleteProject(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/projects/${id}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete project");
  },

  async bulkDeleteProjects(projectIds: string[]): Promise<void> {
    const res = await fetch(`${API_BASE}/projects/bulk-delete`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project_ids: projectIds }),
    });
    if (!res.ok) throw new Error("Failed to delete selected projects");
  },

  async bulkClipAction(projectId: string, clipIds: string[], action: string, captionStyle?: string) {
    const res = await fetch(`${API_BASE}/projects/${projectId}/bulk-action`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        clip_ids: clipIds,
        action,
        caption_style: captionStyle,
      }),
    });
    if (!res.ok) throw new Error("Bulk action failed");
    return res.json();
  },

  // Jobs API
  async listAllJobs(limit: number = 50): Promise<JobStatusResponse[]> {
    const res = await fetch(`${API_BASE}/jobs?limit=${limit}`);
    if (!res.ok) throw new Error("Failed to fetch jobs");
    return res.json();
  },

  async createJob(params: JobCreatePayload): Promise<JobStatusResponse> {
    const res = await fetch(`${API_BASE}/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Failed to create job" }));
      const msg = Array.isArray(err.detail)
        ? err.detail.map((d: any) => d.msg || JSON.stringify(d)).join(", ")
        : err.detail || "Failed to create job";
      throw new Error(msg);
    }

    return res.json();
  },

  async getJob(id: string): Promise<JobStatusResponse> {
    const res = await fetch(`${API_BASE}/jobs/${id}`);
    if (!res.ok) throw new Error("Failed to fetch job status");
    return res.json();
  },

  async deleteJob(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/jobs/${id}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete job");
  },

  async getJobCandidates(jobId: string): Promise<CandidateDetail[]> {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/candidates`);
    if (!res.ok) throw new Error("Failed to fetch job candidates");
    return res.json();
  },

  async getJobClips(jobId: string): Promise<RenderedClipResponse[]> {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/clips`);
    if (!res.ok) throw new Error("Failed to fetch job clips");
    return res.json();
  },

  // Clips API
  async listAllClips(params?: {
    limit?: number;
    offset?: number;
    is_favorite?: boolean;
  }): Promise<RenderedClipResponse[]> {
    const query = new URLSearchParams();
    if (params?.limit) query.append("limit", params.limit.toString());
    if (params?.offset) query.append("offset", params.offset.toString());
    if (params?.is_favorite !== undefined) query.append("is_favorite", params.is_favorite.toString());

    const res = await fetch(`${API_BASE}/clips?${query.toString()}`);
    if (!res.ok) throw new Error("Failed to fetch clips library");
    return res.json();
  },

  async getClip(id: string): Promise<RenderedClipResponse> {
    const res = await fetch(`${API_BASE}/clips/${id}`);
    if (!res.ok) throw new Error("Failed to fetch clip");
    return res.json();
  },

  async deleteClip(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/clips/${id}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete clip");
  },

  async bulkDeleteClips(clipIds: string[]): Promise<void> {
    const res = await fetch(`${API_BASE}/clips/bulk-delete`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ clip_ids: clipIds }),
    });
    if (!res.ok) throw new Error("Failed to delete selected clips");
  },

  async rerenderClip(id: string, params: {
    start_time: number;
    end_time: number;
    caption_style?: string;
    burn_captions?: boolean;
    remove_dead_air?: boolean;
    framing_mode?: string;
    blur_radius?: number;
    subtitle_position?: number;
    add_hook_header?: boolean;
    hook_header_position?: number;
    hook_header_text?: string;
    remove_watermark?: boolean;
    watermark_position?: string;
    enhance_quality?: boolean;
  }): Promise<RenderedClipResponse> {
    const res = await fetch(`${API_BASE}/clips/${id}/re-render`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error("Failed to re-render clip");
    return res.json();
  },

  async refreshThumbnail(id: string): Promise<RenderedClipResponse> {
    const res = await fetch(`${API_BASE}/clips/${id}/refresh-thumbnail`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("Failed to refresh thumbnail");
    return res.json();
  },

  async regenerateClip(id: string, params: {
    intent: string;
    caption_style?: string;
    custom_note?: string;
    subtitle_position?: number;
    add_hook_header?: boolean;
    hook_header_position?: number;
    hook_header_text?: string;
    remove_watermark?: boolean;
    watermark_position?: string;
    enhance_quality?: boolean;
  }): Promise<RenderedClipResponse> {
    const res = await fetch(`${API_BASE}/clips/${id}/regenerate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error("Failed to regenerate clip");
    return res.json();
  },

  async submitFeedback(id: string, action: string, feedbackText?: string) {
    const res = await fetch(`${API_BASE}/clips/${id}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, feedback_text: feedbackText }),
    });
    if (!res.ok) throw new Error("Failed to record feedback");
    return res.json();
  },

  async toggleFavorite(id: string): Promise<{ id: string; is_favorite: boolean }> {
    const res = await fetch(`${API_BASE}/clips/${id}/favorite`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("Failed to toggle favorite");
    return res.json();
  },

  async detectWatermark(videoId: string): Promise<{
    detected: boolean;
    position: string;
    confidence: number;
    delogo_filter: string;
    corner_scores: Record<string, number>;
  }> {
    const res = await fetch(`${API_BASE}/upload/${videoId}/detect-watermark`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("Failed to run watermark detection");
    return res.json();
  },

  // Media Streaming & Asset URLs
  getMediaUrl(url: string | null | undefined): string {
    if (!url) return "";
    if (url.startsWith("http://") || url.startsWith("https://")) return url;
    const cleanUrl = url.startsWith("/") ? url : `/${url}`;
    const baseOrigin = API_BASE.replace(/\/api\/?$/, "");
    return `${baseOrigin}${cleanUrl}`;
  },

  // Export URLs
  getDirectMp4Url(clipId: string): string {
    return `${API_BASE}/export/clip/${clipId}/mp4`;
  },

  getSingleExportUrl(clipId: string): string {
    return `${API_BASE}/export/clip/${clipId}`;
  },

  getBatchExportUrl(jobId: string): string {
    return `${API_BASE}/export/job/${jobId}/batch`;
  },

  async downloadSelectedClipsZip(clipIds: string[]): Promise<Blob> {
    const res = await fetch(`${API_BASE}/export/clips/batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ clip_ids: clipIds }),
    });
    if (!res.ok) throw new Error("Failed to export selected clips ZIP");
    return res.blob();
  },


  // Admin Metrics
  async getAdminMetrics(): Promise<AdminMetricsResponse> {
    const res = await fetch(`${API_BASE}/admin/metrics`);
    if (!res.ok) throw new Error("Failed to fetch admin metrics");
    return res.json();
  },

  // Settings API
  async getSettings(): Promise<SettingsResponse> {
    const res = await fetch(`${API_BASE}/settings`);
    if (!res.ok) throw new Error("Failed to fetch settings");
    return res.json();
  },

  async updateSettings(params: SettingsUpdateRequest): Promise<SettingsResponse> {
    const res = await fetch(`${API_BASE}/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error("Failed to update settings");
    return res.json();
  },

  async testApiKey(provider: "gemini" | "groq" | "deepgram", apiKey: string, model?: string): Promise<TestApiKeyResponse> {
    const res = await fetch(`${API_BASE}/settings/test`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider, api_key: apiKey, model }),
    });
    if (!res.ok) throw new Error("Failed to test API key");
    return res.json();
  },
};


