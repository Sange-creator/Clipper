"""Computer Vision-based automatic watermark and logo detector using OpenCV.
Detects static corner logos, TV bugs, broadcast tags, and TikTok bouncing watermarks
by analyzing temporal variance and persistent spatial edge accumulation across video frames.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class WatermarkDetectionResult:
    def __init__(
        self,
        detected: bool,
        position: str,
        confidence: float,
        delogo_filter: str,
        corner_scores: Dict[str, float],
    ):
        self.detected = detected
        self.position = position
        self.confidence = confidence
        self.delogo_filter = delogo_filter
        self.corner_scores = corner_scores

    def to_dict(self) -> Dict[str, Any]:
        return {
            "detected": self.detected,
            "position": self.position,
            "confidence": round(self.confidence, 3),
            "delogo_filter": self.delogo_filter,
            "corner_scores": {k: round(v, 3) for k, v in self.corner_scores.items()},
        }


class WatermarkDetector:
    """
    Automated watermark and logo detection service.
    Analyzes temporal persistence of edges and pixel variance across video frames to pinpoint
    where static watermarks, station bugs, or bouncing TikTok logos are positioned.
    """

    def __init__(self, sample_frames_count: int = 16, edge_threshold: float = 0.18):
        self.sample_frames_count = sample_frames_count
        self.edge_threshold = edge_threshold

    async def detect_watermark(
        self,
        video_path: Path | str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        width: int = 1920,
        height: int = 1080,
    ) -> WatermarkDetectionResult:
        """Asynchronously run watermark detection in an executor thread to keep event loop free."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self._detect_sync,
            str(video_path),
            start_time,
            end_time,
            width,
            height,
        )

    def _detect_sync(
        self,
        video_path: str,
        start_time: Optional[float],
        end_time: Optional[float],
        width: int,
        height: int,
    ) -> WatermarkDetectionResult:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.warning(f"WatermarkDetector: Cannot open video {video_path}")
            return WatermarkDetectionResult(
                detected=False,
                position="none",
                confidence=0.0,
                delogo_filter="",
                corner_scores={"top_right": 0.0, "bottom_right": 0.0, "top_left": 0.0, "bottom_left": 0.0},
            )

        try:
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            dur = total_frames / fps if total_frames > 0 else 60.0

            s_sec = max(0.0, start_time or 0.0)
            e_sec = min(dur, end_time if end_time is not None and end_time > 0 else dur)
            if e_sec <= s_sec:
                e_sec = s_sec + min(30.0, dur)

            s_frame = int(s_sec * fps)
            e_frame = int(e_sec * fps)
            frame_range = max(1, e_frame - s_frame)

            # Pick evenly spaced frame indices
            n_samples = min(self.sample_frames_count, max(6, frame_range // 15))
            step = max(1, frame_range // n_samples)
            sample_indices = [s_frame + i * step for i in range(n_samples) if s_frame + i * step < total_frames]

            if not sample_indices:
                sample_indices = [0]

            frames_gray = []
            for idx in sample_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if ret and frame is not None:
                    # Resize to standard analysis resolution (960x540) for fast processing
                    h, w = frame.shape[:2]
                    scale_w, scale_h = 960, 540
                    resized = cv2.resize(frame, (scale_w, scale_h), interpolation=cv2.INTER_AREA)
                    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
                    frames_gray.append(gray)

            if len(frames_gray) < 3:
                return WatermarkDetectionResult(
                    detected=False,
                    position="none",
                    confidence=0.0,
                    delogo_filter="",
                    corner_scores={"top_right": 0.0, "bottom_right": 0.0, "top_left": 0.0, "bottom_left": 0.0},
                )

            # Analyze 4 corner regions in 960x540 space
            H, W = frames_gray[0].shape
            roi_w = int(W * 0.16)
            roi_h = int(H * 0.14)
            pad_x = int(W * 0.015)
            pad_y = int(H * 0.02)

            corners = {
                "top_right": (W - roi_w - pad_x, pad_y, roi_w, roi_h),
                "bottom_right": (W - roi_w - pad_x, H - roi_h - pad_y, roi_w, roi_h),
                "top_left": (pad_x, pad_y, roi_w, roi_h),
                "bottom_left": (pad_x, H - roi_h - pad_y, roi_w, roi_h),
            }

            scores: Dict[str, float] = {}
            for name, (rx, ry, rw, rh) in corners.items():
                rois = [f[ry : ry + rh, rx : rx + rw] for f in frames_gray]
                scores[name] = self._score_roi_watermark(rois)

            # Determine best detection match
            detected = False
            position = "none"
            max_corner = max(scores, key=scores.get)
            max_score = scores[max_corner]

            # TikTok check: often has logos in top_left and bottom_right alternately
            tl_score = scores.get("top_left", 0.0)
            br_score = scores.get("bottom_right", 0.0)
            if tl_score >= self.edge_threshold * 0.8 and br_score >= self.edge_threshold * 0.8:
                detected = True
                position = "tiktok_bounce"
                confidence = (tl_score + br_score) / 2.0
            elif max_score >= self.edge_threshold:
                detected = True
                # Check if multiple corners have high scores
                high_corners = [k for k, v in scores.items() if v >= self.edge_threshold * 1.1]
                if len(high_corners) >= 3:
                    position = "all_corners"
                else:
                    position = max_corner
                confidence = max_score
            else:
                detected = False
                position = "none"
                confidence = max_score

            from app.services.media.renderer import get_delogo_filter

            filter_str = get_delogo_filter(position, width, height) if detected else ""

            return WatermarkDetectionResult(
                detected=detected,
                position=position,
                confidence=confidence,
                delogo_filter=filter_str,
                corner_scores=scores,
            )
        finally:
            cap.release()

    def _score_roi_watermark(self, rois: List[np.ndarray]) -> float:
        """
        Calculates a static watermark likelihood score for a region across frames:
        1. High edge density (logos contain text / sharp shapes).
        2. Low temporal variance (logos stay static while scene background changes).
        3. Persistent edges (edges occur at the exact same location across frames).
        """
        if not rois or len(rois) < 2:
            return 0.0

        stack = np.array(rois, dtype=np.float32)  # shape (N, H, W)

        # 1. Temporal standard deviation across frames (normalized 0..1)
        temporal_std = np.std(stack, axis=0)  # shape (H, W)
        mean_std = float(np.mean(temporal_std))
        # Lower std means static region; inverted std factor
        staticness = max(0.0, 1.0 - min(1.0, mean_std / 45.0))

        # 2. Edge detection across frames
        edge_list = []
        for img in rois:
            edges = cv2.Canny(img, 40, 120)
            edge_list.append(edges > 0)

        edge_stack = np.array(edge_list, dtype=np.uint8)  # shape (N, H, W)
        edge_count_per_pixel = np.sum(edge_stack, axis=0)  # 0..N

        # Pixels where edges appear in at least 40% of the sampled frames
        min_repeats = max(2, int(len(rois) * 0.40))
        persistent_edge_pixels = np.sum(edge_count_per_pixel >= min_repeats)
        total_pixels = rois[0].shape[0] * rois[0].shape[1]
        persistent_density = persistent_edge_pixels / max(1.0, float(total_pixels))

        # A watermark must contain sharp graphical or text edges
        if persistent_density < 0.005:
            return 0.0

        # High-confidence watermark: has both persistent edges (text/icon) and staticness
        combined_score = min(1.0, (persistent_density * 8.0) * 0.70 + (staticness * 0.30))
        return float(combined_score)


# Global singleton instance
watermark_detector = WatermarkDetector()
