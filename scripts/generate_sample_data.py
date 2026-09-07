"""
SatQuery AI - Synthetic Remote Sensing Sample Data Generator
Generates realistic Optical, SAR, T1, and T2 rasters for immediate testing and hackathon demonstrations.
"""
import os
import numpy as np
from PIL import Image, ImageDraw

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_data")
os.makedirs(SAMPLE_DIR, exist_ok=True)


def create_optical_sample():
    """Generates an optical remote sensing scene with airfield, runways, and hangars."""
    img = Image.new("RGB", (512, 512), color=(85, 120, 80))  # Green field background
    draw = ImageDraw.Draw(img)

    # Runway 1
    draw.rectangle([120, 40, 160, 480], fill=(60, 60, 65))
    # Runway markings
    for y in range(60, 460, 40):
        draw.rectangle([138, y, 142, y + 20], fill=(240, 240, 240))

    # Taxiway & apron
    draw.rectangle([160, 180, 320, 240], fill=(70, 70, 75))
    draw.rectangle([280, 120, 420, 360], fill=(80, 80, 85))

    # Buildings / Hangars
    draw.rectangle([320, 140, 400, 200], fill=(180, 190, 200), outline=(40, 40, 40), width=2)
    draw.rectangle([320, 240, 400, 300], fill=(180, 190, 200), outline=(40, 40, 40), width=2)

    # Aircraft parked on apron
    draw.polygon([(220, 200), (240, 210), (220, 220), (226, 210)], fill=(255, 255, 255))
    draw.polygon([(260, 200), (280, 210), (260, 220), (266, 210)], fill=(255, 255, 255))

    path = os.path.join(SAMPLE_DIR, "optical_sample.png")
    img.save(path)
    print(f"Created {path}")


def create_sar_sample():
    """Generates a SAR radar scene with characteristic microwave backscatter speckle and bright corner reflections."""
    # Synthetic speckle noise baseline (Rayleigh/Gaussian)
    np.random.seed(42)
    speckle = np.random.gamma(shape=3.0, scale=15.0, size=(512, 512)).astype(np.uint8)
    img = Image.fromarray(speckle, mode="L")
    draw = ImageDraw.Draw(img)

    # Dark smooth surfaces (runways reflect away from radar - low backscatter)
    draw.rectangle([120, 40, 160, 480], fill=15)
    draw.rectangle([160, 180, 320, 240], fill=20)
    draw.rectangle([280, 120, 420, 360], fill=25)

    # Bright metallic corner reflectors (hangars & aircraft have high double-bounce return)
    draw.rectangle([320, 140, 400, 200], fill=245, outline=255, width=3)
    draw.rectangle([320, 240, 400, 300], fill=245, outline=255, width=3)
    draw.rectangle([225, 205, 240, 215], fill=255)
    draw.rectangle([265, 205, 280, 215], fill=255)

    path = os.path.join(SAMPLE_DIR, "sar_sample.png")
    img.save(path)
    print(f"Created {path}")


def create_temporal_samples():
    """Generates T1 (baseline) and T2 (post-development) imagery for change detection."""
    # T1: Baseline rural landscape
    t1 = Image.new("RGB", (512, 512), color=(90, 130, 75))
    d1 = ImageDraw.Draw(t1)
    # Natural river
    d1.line([(0, 250), (180, 280), (350, 230), (512, 260)], fill=(45, 80, 130), width=35)
    # Small single settlement
    d1.rectangle([80, 80, 140, 130], fill=(160, 150, 140), outline=(50, 50, 50))

    t1_path = os.path.join(SAMPLE_DIR, "t1_sample.png")
    t1.save(t1_path)
    print(f"Created {t1_path}")

    # T2: Major urban development in southeastern sector + new bridge
    t2 = t1.copy()
    d2 = ImageDraw.Draw(t2)
    # New bridge crossing river
    d2.rectangle([240, 220, 280, 290], fill=(120, 120, 130), outline=(30, 30, 30))
    # New industrial buildings
    d2.rectangle([320, 320, 440, 440], fill=(210, 80, 70), outline=(30, 30, 30), width=2)
    d2.rectangle([340, 100, 460, 180], fill=(220, 220, 225), outline=(30, 30, 30), width=2)
    # New access highway
    d2.line([(260, 0), (260, 512)], fill=(50, 50, 55), width=12)

    t2_path = os.path.join(SAMPLE_DIR, "t2_sample.png")
    t2.save(t2_path)
    print(f"Created {t2_path}")


if __name__ == "__main__":
    create_optical_sample()
    create_sar_sample()
    create_temporal_samples()
    print("All sample datasets generated.")
