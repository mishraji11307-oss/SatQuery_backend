"""
SatQuery AI - Remote Sensing Preprocessing & Visual Artifact Generation
Handles normalization, SAR speckle reduction, change mask generation, and bounding box rendering.
"""
from typing import Tuple, List, Optional, Dict, Any
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import os
from app.core.config import settings
from app.core.logging import logger

try:
    import cv2
    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False


class RemoteSensingPreprocessor:
    """Prepares multimodal rasters for model inference and visual evidence generation."""

    @staticmethod
    def load_image_array(file_path: str, target_size: Optional[Tuple[int, int]] = None) -> np.ndarray:
        """Loads image file as uint8 RGB or Grayscale numpy array."""
        try:
            with Image.open(file_path) as pil_img:
                if pil_img.mode not in ["RGB", "L", "RGBA"]:
                    pil_img = pil_img.convert("RGB")
                
                if target_size:
                    pil_img = pil_img.resize(target_size, Image.Resampling.BILINEAR)

                arr = np.array(pil_img)
                if arr.dtype != np.uint8:
                    arr = RemoteSensingPreprocessor.normalize_to_uint8(arr)
                return arr
        except Exception as e:
            logger.error(f"Failed to load image array from {file_path}: {e}")
            raise

    @staticmethod
    def normalize_to_uint8(arr: np.ndarray, percentile_clip: bool = True) -> np.ndarray:
        """Normalizes any float or high bit-depth array into 8-bit [0, 255]."""
        arr_float = arr.astype(np.float32)
        if percentile_clip:
            p2, p98 = np.percentile(arr_float, (2, 98))
            if p98 > p2:
                arr_float = np.clip(arr_float, p2, p98)
                norm = ((arr_float - p2) / (p98 - p2)) * 255.0
                return norm.astype(np.uint8)

        min_val = np.min(arr_float)
        max_val = np.max(arr_float)
        if max_val > min_val:
            norm = ((arr_float - min_val) / (max_val - min_val)) * 255.0
            return norm.astype(np.uint8)
        return np.zeros_like(arr, dtype=np.uint8)

    @staticmethod
    def preprocess_sar(sar_arr: np.ndarray) -> np.ndarray:
        """Applies decibel scaling (10*log10) and speckle median filtering to SAR backscatter."""
        sar_float = np.maximum(sar_arr.astype(np.float32), 1e-5)
        db_scaled = 10.0 * np.log10(sar_float)
        norm_sar = RemoteSensingPreprocessor.normalize_to_uint8(db_scaled)
        
        if _HAS_CV2:
            return cv2.medianBlur(norm_sar, 3)
        else:
            pil_img = Image.fromarray(norm_sar)
            filtered = pil_img.filter(ImageFilter.MedianFilter(size=3))
            return np.array(filtered)

    @staticmethod
    def create_change_mask_artifact(
        t1_arr: np.ndarray,
        t2_arr: np.ndarray,
        output_path: str,
        threshold: float = 35.0
    ) -> Tuple[str, float, np.ndarray]:
        """
        Generates a colored change detection mask overlay and calculates percentage change.
        Returns (output_file_path, change_percentage, binary_mask).
        """
        # Ensure identical sizes
        if t1_arr.shape[:2] != t2_arr.shape[:2]:
            t2_pil = Image.fromarray(t2_arr).resize((t1_arr.shape[1], t1_arr.shape[0]), Image.Resampling.BILINEAR)
            t2_arr = np.array(t2_pil)

        # Convert to grayscale
        def to_gray(a):
            if len(a.shape) == 2:
                return a
            return (0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]).astype(np.uint8)

        g1 = to_gray(t1_arr)
        g2 = to_gray(t2_arr)

        if _HAS_CV2:
            diff = cv2.absdiff(g1, g2)
            diff_blur = cv2.GaussianBlur(diff, (5, 5), 0)
            _, mask = cv2.threshold(diff_blur, int(threshold), 255, cv2.THRESH_BINARY)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel)
        else:
            diff = np.abs(g1.astype(np.int16) - g2.astype(np.int16)).astype(np.uint8)
            diff_pil = Image.fromarray(diff).filter(ImageFilter.GaussianBlur(radius=2))
            diff_arr = np.array(diff_pil)
            mask = np.where(diff_arr > threshold, 255, 0).astype(np.uint8)

        # Calculate percentage altered
        changed_pixels = np.count_nonzero(mask)
        total_pixels = mask.shape[0] * mask.shape[1]
        change_pct = round((changed_pixels / total_pixels) * 100.0, 2)

        # Create colored overlay: Crimson red on top of T2 image
        overlay = t2_arr.copy()
        if len(overlay.shape) == 2:
            overlay = np.stack([overlay] * 3, axis=-1)
        elif overlay.shape[2] == 4:
            overlay = overlay[:, :, :3]

        red_mask = np.zeros_like(overlay)
        red_mask[:, :] = [255, 30, 70]  # Vibrant Neon Red

        alpha = 0.55
        mask_indices = (mask == 255)
        overlay[mask_indices] = (
            overlay[mask_indices] * (1 - alpha) + red_mask[mask_indices] * alpha
        ).astype(np.uint8)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(overlay).save(output_path, quality=95)

        return output_path, change_pct, mask

    @staticmethod
    def draw_grounding_bboxes(
        image_arr: np.ndarray,
        bboxes: List[Dict[str, Any]],
        output_path: str
    ) -> str:
        """
        Renders localized bounding boxes with labels and confidence chips onto image.
        bboxes format: [{'label': 'aircraft', 'confidence': 0.95, 'box_2d': [ymin, xmin, ymax, xmax]}]
        """
        img = Image.fromarray(image_arr)
        draw = ImageDraw.Draw(img)
        w, h = img.size

        color_palette = [
            "#00F0FF",  # Cyber Cyan
            "#FF0055",  # Neon Crimson
            "#FFE600",  # Solar Yellow
            "#00FF66",  # Matrix Green
            "#9D00FF",  # Electric Purple
        ]

        for idx, bbox in enumerate(bboxes):
            color = color_palette[idx % len(color_palette)]
            box = bbox.get("box_2d", [0, 0, 1, 1])
            ymin, xmin, ymax, xmax = box
            
            x1, y1 = int(xmin * w), int(ymin * h)
            x2, y2 = int(xmax * w), int(ymax * h)

            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)

            label = bbox.get("label", "target")
            conf = bbox.get("confidence", 1.0)
            text = f"{label.upper()} ({conf:.2f})"

            draw.rectangle([x1, max(0, y1 - 18), min(w, x1 + 120), y1], fill=color)
            draw.text((x1 + 3, max(0, y1 - 16)), text, fill="#000000")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, quality=95)
        return output_path

    @staticmethod
    def create_side_by_side(
        img1_arr: np.ndarray,
        img2_arr: np.ndarray,
        output_path: str,
        label1: str = "T1 Observation",
        label2: str = "T2 Observation"
    ) -> str:
        """Stitches two images side-by-side with labels for clear visual comparison."""
        h1, w1 = img1_arr.shape[:2]
        h2, w2 = img2_arr.shape[:2]

        target_h = max(h1, h2)
        im1_pil = Image.fromarray(img1_arr).resize((int(w1 * (target_h / h1)), target_h), Image.Resampling.BILINEAR)
        im2_pil = Image.fromarray(img2_arr).resize((int(w2 * (target_h / h2)), target_h), Image.Resampling.BILINEAR)

        if im1_pil.mode != "RGB":
            im1_pil = im1_pil.convert("RGB")
        if im2_pil.mode != "RGB":
            im2_pil = im2_pil.convert("RGB")

        im1_res = np.array(im1_pil)
        im2_res = np.array(im2_pil)

        stitched = np.hstack([im1_res, im2_res])
        pil_stitched = Image.fromarray(stitched)
        draw = ImageDraw.Draw(pil_stitched)

        # Draw label badges
        draw.rectangle([10, 10, 160, 36], fill="#000000AA")
        draw.text((15, 14), label1, fill="#FFFFFF")

        split_x = im1_res.shape[1]
        draw.rectangle([split_x + 10, 10, split_x + 160, 36], fill="#000000AA")
        draw.text((split_x + 15, 14), label2, fill="#FFFFFF")

        draw.line([(split_x, 0), (split_x, target_h)], fill="#00F0FF", width=2)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        pil_stitched.save(output_path, quality=95)
        return output_path
