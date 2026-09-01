"""Model loading and person detection/tracking.

Wraps Ultralytics YOLO so the rest of the pipeline only ever deals with
supervision `Detections` objects, never raw Ultralytics results. When we
swap in custom-trained weights later, this is the only file that cares.
"""

from __future__ import annotations

import numpy as np
import supervision as sv
from ultralytics import YOLO

PERSON_CLASS_ID = 0  # COCO class index for "person"


class PersonTracker:
    """YOLO detection with Ultralytics' built-in ByteTrack tracking.

    Tracking state lives inside the model between `track()` calls, so use
    one instance per video and feed it frames in order.
    """

    def __init__(self, weights: str = "yolo11n.pt", confidence: float = 0.3):
        self.model = YOLO(weights)
        self.confidence = confidence

    def track(self, frame: np.ndarray) -> sv.Detections:
        """Detect and track people in one video frame (BGR).

        Returned detections carry `tracker_id` — the persistent per-person ID.
        """
        result = self.model.track(
            frame,
            persist=True,
            classes=[PERSON_CLASS_ID],
            conf=self.confidence,
            verbose=False,
        )[0]
        return sv.Detections.from_ultralytics(result)

    def detect(self, image: np.ndarray) -> sv.Detections:
        """Detect people in a single still image — no tracking IDs."""
        result = self.model.predict(
            image,
            classes=[PERSON_CLASS_ID],
            conf=self.confidence,
            verbose=False,
        )[0]
        return sv.Detections.from_ultralytics(result)
