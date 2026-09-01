export interface VideoInfo {
  id: string;
  project_id?: string | null;
  filename: string;
  duration_seconds: number;
  width: number;
  height: number;
  fps: number;
  video_codec: string;
  audio_codec: string;
  file_size_bytes: number;
  created_at: string;
  video_url?: string;
}

export interface VideoUploadResponse {
  video: VideoInfo;
  is_duplicate: boolean;
  message: string;
}

export interface BatchUploadResponse {
  uploaded_videos: VideoInfo[];
  duplicates_count: number;
  failed_count: number;
  total_processed: number;
  message: string;
}

export interface ProjectListItem {
  id: string;
  name: string;
  mode: "podcast" | "viral_moments" | string;
  description?: string | null;
  video_count: number;
  clips_count: number;
  created_at: string;
  updated_at: string;
}

export interface TimelineEditInfo {
  source_start: number;
  source_end: number;
  keep: number[][];
  dead_air_removed_seconds: number;
}

export interface ProjectDetailResponse {
  id: string;
  name: string;
  mode: "podcast" | "viral_moments" | string;
  description?: string | null;
  videos: VideoInfo[];
  clips: RenderedClipResponse[];
  total_videos: number;
  total_clips: number;
  created_at: string;
  updated_at: string;
}

export interface CandidateScores {
  hook_score: number;
  retention_score: number;
  curiosity_score: number;
  emotion_score: number;
  story_score: number;
  payoff_score: number;
  shareability_score: number;
  novelty_score: number;
  quotability_score: number;
  standalone_score?: number;
  rewatch_score?: number;
  visual_score: number;
  audio_score: number;
  platform_score: number;
  composite_score: number;
  penalty_deduction: number;
}

export interface CandidateDetail {
  id: string;
  job_id: string;
  video_id: string;
  start_time: number;
  end_time: number;
  duration: number;
  scores: CandidateScores;
  rank: number;
  selected: boolean;
  hook_text?: string | null;
  payoff_text?: string | null;
  transcript_text?: string | null;
  timeline_edit?: TimelineEditInfo | null;
  reason?: string | null;
}

export interface PlatformMetadata {
  tiktok_title: string;
  tiktok_caption: string;
  tiktok_hashtags: string[];
  reels_caption: string;
  reels_hashtags: string[];
  shorts_title: string;
  shorts_description: string;
  shorts_hashtags: string[];
}

export interface RenderedClipResponse {
  id: string;
  candidate_id: string;
  job_id: string;
  video_id: string;
  mode: "podcast" | "viral_moments" | string;
  video_url: string;
  thumbnail_url?: string | null;
  srt_url?: string | null;
  ass_url?: string | null;
  start_time: number;
  end_time: number;
  duration: number;
  aspect_ratio: string;
  framing_mode?: "crop_9_16" | "blur_fit_9_16" | "original_16_9" | string;
  blur_radius?: number;
  subtitle_position?: number;
  caption_style: string;
  burn_captions?: boolean;
  timeline_edit?: TimelineEditInfo | null;
  scores: CandidateScores;
  reason?: string | null;
  hook_text?: string | null;
  payoff_text?: string | null;
  metadata: PlatformMetadata;
  is_favorite: boolean;
  is_rejected: boolean;
  created_at: string;
}

export interface LogEntry {
  stage: number;
  stage_name: string;
  message: string;
  timestamp: string;
}

export type JobLog = LogEntry;

export interface JobStatusResponse {
  id: string;
  project_id?: string | null;
  video_id?: string | null;
  mode?: "podcast" | "viral_moments" | string;
  status: "queued" | "processing" | "completed" | "failed" | "cancelled";
  current_stage: number;
  stage_name: string;
  progress: number;
  total_candidates_found?: number;
  total_clips_rendered?: number;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
  logs: LogEntry[];
}

export interface JobCreatePayload {
  video_id: string;
  mode?: "podcast" | "viral_moments";
  target_clips_count?: number;
  duration_preset?: "15-30s" | "30-45s" | "45-60s" | "60-90s" | "custom";
  caption_style?: "clean_white" | "bold_yellow" | "podcast_box" | "cinematic" | "meme_impact" | "cyber_neon" | "none";
  burn_captions?: boolean;
  remove_dead_air?: boolean;
  framing_mode?: "crop_9_16" | "blur_fit_9_16" | "original_16_9";
  blur_radius?: number;
  subtitle_position?: number;
  reframing_mode?: "smart_face_track" | "center_crop";
  ai_provider?: "gemini" | "groq" | "mock";
  custom_instructions?: string;
}

export interface ProjectCreatePayload {
  name: string;
  mode?: "podcast" | "viral_moments";
  description?: string;
}

export interface ProjectProcessPayload {
  mode?: "podcast" | "viral_moments";
  target_clips_count?: number;
  duration_preset?: "15-30s" | "30-45s" | "45-60s" | "60-90s" | "custom";
  caption_style?: "clean_white" | "bold_yellow" | "podcast_box" | "cinematic" | "meme_impact" | "cyber_neon" | "none";
  burn_captions?: boolean;
  remove_dead_air?: boolean;
  framing_mode?: "crop_9_16" | "blur_fit_9_16" | "original_16_9";
  blur_radius?: number;
  subtitle_position?: number;
  reframing_mode?: "smart_face_track" | "center_crop";
  source_diversity_weight?: number;
  ai_provider?: "gemini" | "groq" | "mock";
  custom_instructions?: string;
}

export interface AdminMetricsResponse {
  total_projects: number;
  total_videos: number;
  total_clips_generated: number;
  total_jobs: number;
  active_jobs: number;
  failed_jobs: number;
  avg_processing_time_sec: number;
  acceptance_rate_pct: number;
  rejection_rate_pct: number;
  manual_edit_rate_pct: number;
  total_ai_requests: number;
  ai_provider_stats: Record<string, any>;
  storage_bytes_used: number;
}

export interface SettingsResponse {
  ai_provider?: string;
  active_ai_provider?: "gemini" | "groq" | "mock";
  gemini_api_key_configured: boolean;
  gemini_api_key_masked?: string;
  gemini_model?: string;
  groq_api_key_configured: boolean;
  groq_api_key_masked?: string;
  groq_model?: string;
  available_groq_models?: string[];
  deepgram_api_key_configured?: boolean;
  deepgram_api_key_masked?: string;
  deepgram_model?: string;
  transcriber_provider?: string;
  whisper_model_size?: string;
  default_framing_mode?: "crop_9_16" | "blur_fit_9_16" | "original_16_9" | string;
  default_blur_radius?: number;
  default_subtitle_position?: number;
  ffmpeg_available?: boolean;
  ffprobe_available?: boolean;
}

export interface SettingsUpdateRequest {
  ai_provider?: "gemini" | "groq" | "mock";
  active_ai_provider?: "gemini" | "groq" | "mock";
  gemini_api_key?: string;
  gemini_model?: string;
  groq_api_key?: string;
  groq_model?: string;
  deepgram_api_key?: string;
  deepgram_model?: string;
  transcriber_provider?: string;
  whisper_model_size?: string;
  default_framing_mode?: "crop_9_16" | "blur_fit_9_16" | "original_16_9";
  default_blur_radius?: number;
  default_subtitle_position?: number;
}

export interface TestApiKeyResponse {
  valid: boolean;
  message: string;
  model_tested?: string;
  discovered_models?: string[];
}


