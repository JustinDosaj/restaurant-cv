"""End-to-end processing: read a source, run tracking, draw, write output.

This is the layer future features plug into — zone assignment and occupancy
records will hook in right where detections come back from the tracker.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import cv2
import supervision as sv
from tqdm import tqdm

from .annotate import FrameAnnotator
from .detect import PersonTracker

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}


@dataclass
class RunSummary:
    frames_processed: int = 0
    unique_track_ids: set[int] = field(default_factory=set)
    peak_people_in_frame: int = 0


def process_video(
    source: Path,
    output: Path,
    tracker: PersonTracker,
    stride: int = 1,
) -> RunSummary:
    """Run tracking over a video file and write the annotated copy.

    `stride` processes every Nth frame; the output video's FPS is scaled
    down to match so it plays at real-time speed. Tracking is most reliable
    at stride 1 — ByteTrack relies on small frame-to-frame movement.
    """
    video_info = sv.VideoInfo.from_video_path(str(source))
    total_frames = video_info.total_frames
    if stride > 1:
        video_info.fps = max(1, round(video_info.fps / stride))
        if total_frames:
            total_frames = total_frames // stride

    annotator = FrameAnnotator(trace_length_frames=video_info.fps * 2)
    summary = RunSummary()
    frames = sv.get_video_frames_generator(str(source), stride=stride)

    output.parent.mkdir(parents=True, exist_ok=True)
    with sv.VideoSink(str(output), video_info) as sink:
        for frame in tqdm(frames, total=total_frames, desc=source.name, unit="frame"):
            detections = tracker.track(frame)
            sink.write_frame(annotator.annotate(frame, detections))

            summary.frames_processed += 1
            summary.peak_people_in_frame = max(
                summary.peak_people_in_frame, len(detections)
            )
            if detections.tracker_id is not None:
                summary.unique_track_ids.update(int(t) for t in detections.tracker_id)
    return summary


def process_image(source: Path, output: Path, tracker: PersonTracker) -> RunSummary:
    """Run detection on a single image and write the annotated copy."""
    image = cv2.imread(str(source))
    if image is None:
        raise FileNotFoundError(f"Could not read image: {source}")

    detections = tracker.detect(image)
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), FrameAnnotator().annotate(image, detections))
    return RunSummary(frames_processed=1, peak_people_in_frame=len(detections))
