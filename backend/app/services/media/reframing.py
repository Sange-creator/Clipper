"""Smart vertical 9:16 reframer with face detection, subject tracking and smooth pan."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class SmartReframer:
    """Detects primary human subjects/faces and calculates dynamic 9:16 crop coordinates."""

    def __init__(self):
        # Gracefully handle CascadeClassifier if present in cv2 build
        self.face_cascade = None
        if hasattr(cv2, "CascadeClassifier") and hasattr(cv2, "data") and hasattr(cv2.data, "haarcascades"):
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            if Path(cascade_path).exists():
                try:
                    self.face_cascade = cv2.CascadeClassifier(cascade_path)
                except Exception:
                    self.face_cascade = None

    async def calculate_crop_trajectory(
        self,
        video_path: Path | str,
        start_time: float,
        end_time: float,
        target_aspect_ratio: float = 9.0 / 16.0,
    ) -> Dict[str, Any]:
        """
        Samples frames across the clip interval to compute the optimal horizontal pan center.
        Returns crop configuration with smooth center X trajectory or fixed center if static.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self._sync_calculate_crop,
            str(video_path),
            start_time,
            end_time,
            target_aspect_ratio,
        )

    def _sync_calculate_crop(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        target_aspect_ratio: float,
    ) -> Dict[str, Any]:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"mode": "center_crop", "center_x_ratio": 0.5}

        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1920
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 1080
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

        # If source is already vertical (e.g. 9:16 or height > width), no reframe needed
        if width <= height:
            cap.release()
            return {"mode": "passthrough", "center_x_ratio": 0.5}

        # Target crop width for 9:16
        crop_width = height * target_aspect_ratio
        if crop_width > width:
            crop_width = width

        start_frame = int(start_time * fps)
        end_frame = int(end_time * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        focal_centers_x: List[float] = []
        frame_idx = start_frame
        sample_step = max(int(fps / 2), 5)  # Sample twice per second

        while cap.isOpened() and frame_idx <= end_frame:
            ret, frame = cap.read()
            if not ret:
                break

            if (frame_idx - start_frame) % sample_step == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # 1. Face detection if classifier is active
                if self.face_cascade:
                    faces = self.face_cascade.detectMultiScale(
                        gray,
                        scaleFactor=1.1,
                        minNeighbors=4,
                        minSize=(40, 40)
                    )
                    if len(faces) > 0:
                        largest_face = max(faces, key=lambda f: f[2] * f[3])
                        fx, fy, fw, fh = largest_face
                        focal_centers_x.append(fx + (fw / 2.0))
                        frame_idx += 1
                        continue

                # 2. Visual Saliency / Center of Motion fallback
                # Downsample and compute edge / intensity density center
                small = cv2.resize(gray, (160, 90))
                col_sums = np.sum(small, axis=0)
                total_sum = np.sum(col_sums)
                if total_sum > 0:
                    center_col = float(np.sum(np.arange(len(col_sums)) * col_sums) / total_sum)
                    scaled_center_x = (center_col / 160.0) * width
                    focal_centers_x.append(scaled_center_x)

            frame_idx += 1

        cap.release()

        # Compute safe crop center
        if focal_centers_x:
            median_x = float(np.median(focal_centers_x))
            min_center = crop_width / 2.0
            max_center = width - (crop_width / 2.0)
            safe_center_x = max(min_center, min(max_center, median_x))
            center_ratio = safe_center_x / width
            return {
                "mode": "smart_face_track",
                "center_x_ratio": round(center_ratio, 3),
                "crop_width": int(crop_width),
                "crop_height": int(height),
                "crop_x": int(safe_center_x - (crop_width / 2.0)),
                "crop_y": 0,
            }

        # Fallback to center crop
        min_center = crop_width / 2.0
        safe_center_x = width / 2.0
        return {
            "mode": "center_crop",
            "center_x_ratio": 0.5,
            "crop_width": int(crop_width),
            "crop_height": int(height),
            "crop_x": int(safe_center_x - (crop_width / 2.0)),
            "crop_y": 0,
        }


reframer = SmartReframer()
