"""Command-line entry point for person detection + tracking.

Usage:
    python run.py                            # newest video in videos/
    python run.py videos/lunch_rush.mp4      # a specific video
    python run.py frame.jpg                  # a single image
    python run.py --weights models/custom.pt --conf 0.4

Annotated results land in outputs/.
"""

import argparse
from pathlib import Path

from restaurant_cv.detect import PersonTracker
from restaurant_cv.pipeline import (
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    process_image,
    process_video,
)

PROJECT_ROOT = Path(__file__).parent
VIDEOS_DIR = PROJECT_ROOT / "videos"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


def find_default_video() -> Path:
    """Pick the most recently modified video in videos/."""
    candidates = sorted(
        (p for p in VIDEOS_DIR.iterdir() if p.suffix.lower() in VIDEO_EXTENSIONS),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise SystemExit(
            "No videos found in videos/. Drop a file in there, "
            "or pass a path directly: python run.py path\\to\\video.mp4"
        )
    return candidates[0]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Person detection + tracking for restaurant camera footage."
    )
    parser.add_argument(
        "source",
        nargs="?",
        default=None,
        help="Video or image path (default: newest video in videos/)",
    )
    parser.add_argument(
        "--weights",
        default="yolo11n.pt",
        help="YOLO weights: a model name (auto-downloads) or a path to a custom .pt",
    )
    parser.add_argument(
        "--conf", type=float, default=0.3, help="Detection confidence threshold"
    )
    parser.add_argument(
        "--stride",
        type=int,
        default=1,
        help="Process every Nth frame (1 = every frame; tracking works best at 1)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output path (default: outputs/<name>_annotated.<ext>)",
    )
    args = parser.parse_args()

    source = Path(args.source) if args.source else find_default_video()
    if not source.exists():
        raise SystemExit(f"Source not found: {source}")
    is_image = source.suffix.lower() in IMAGE_EXTENSIONS

    if args.output:
        output = Path(args.output)
    else:
        suffix = source.suffix if is_image else ".mp4"
        output = OUTPUTS_DIR / f"{source.stem}_annotated{suffix}"

    print(f"Source:  {source}")
    print(f"Weights: {args.weights}  (conf >= {args.conf})")
    tracker = PersonTracker(weights=args.weights, confidence=args.conf)

    if is_image:
        summary = process_image(source, output, tracker)
        print(f"\nDone. People detected: {summary.peak_people_in_frame}")
    else:
        summary = process_video(source, output, tracker, stride=args.stride)
        print(f"\nDone. Frames processed:   {summary.frames_processed}")
        print(f"Unique people tracked:  {len(summary.unique_track_ids)}")
        print(f"Peak people in frame:   {summary.peak_people_in_frame}")
    print(f"Annotated output: {output}")


if __name__ == "__main__":
    main()
