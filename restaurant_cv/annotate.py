"""Drawing: turns a frame + detections into an annotated frame.

All supervision annotator setup lives here so the pipeline and CLI never
touch drawing details.
"""

from __future__ import annotations

import numpy as np
import supervision as sv


class FrameAnnotator:
    """Draws boxes, track-ID labels, and motion traces on frames.

    Colors are keyed by tracker ID, so the same person keeps the same color
    across the whole video. Detections without tracker IDs (still images)
    fall back to plain class-colored boxes.
    """

    def __init__(self, trace_length_frames: int = 60):
        self._box = sv.BoxAnnotator(color_lookup=sv.ColorLookup.TRACK)
        self._label = sv.LabelAnnotator(color_lookup=sv.ColorLookup.TRACK)
        self._trace = sv.TraceAnnotator(
            color_lookup=sv.ColorLookup.TRACK, trace_length=trace_length_frames
        )
        self._box_plain = sv.BoxAnnotator()
        self._label_plain = sv.LabelAnnotator()

    def annotate(self, frame: np.ndarray, detections: sv.Detections) -> np.ndarray:
        frame = frame.copy()
        if detections.tracker_id is not None:
            labels = [f"person #{tid}" for tid in detections.tracker_id]
            frame = self._trace.annotate(frame, detections)
            frame = self._box.annotate(frame, detections)
            frame = self._label.annotate(frame, detections, labels=labels)
        else:
            labels = ["person"] * len(detections)
            frame = self._box_plain.annotate(frame, detections)
            frame = self._label_plain.annotate(frame, detections, labels=labels)
        return frame
