# restaurant-cv

Person detection + tracking on restaurant security-camera footage. See
[CLAUDE.md](CLAUDE.md) for the product vision and roadmap.

## Quickstart

```powershell
# one-time setup
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# drop a video into videos\, then:
.venv\Scripts\python run.py
```

That processes the newest video in `videos/` and writes an annotated copy to
`outputs/` — every person gets a bounding box, a persistent ID (`person #3`),
and a motion trail. A run summary (unique people tracked, peak people in
frame) prints at the end.

Other ways to run it:

```powershell
.venv\Scripts\python run.py videos\lunch_rush.mp4     # specific video
.venv\Scripts\python run.py frame.jpg                 # single image
.venv\Scripts\python run.py --conf 0.4 --stride 5     # options
.venv\Scripts\python run.py --weights models\custom.pt
```

| Flag | Default | Meaning |
| --- | --- | --- |
| `--weights` | `yolo11n.pt` | Model name (auto-downloads) or path to custom weights |
| `--conf` | `0.3` | Minimum detection confidence |
| `--stride` | `1` | Process every Nth frame. 1 is best for tracking; higher approximates the cheap ~1 FPS cloud-inference mode |
| `--output` | `outputs/<name>_annotated.*` | Where to write the result |

## Project layout

The project splits into the three concerns that will grow independently:
**running models** (inference), **drawing** (annotation), and **training**.

```
restaurant-cv/
├── run.py                  # CLI entry point — thin, just argument parsing
├── restaurant_cv/          # the package: all real logic lives here
│   ├── detect.py           #   inference: loads YOLO, runs detect/track
│   ├── annotate.py         #   drawing: supervision boxes/labels/traces
│   └── pipeline.py         #   glue: video in → track → draw → video out
├── videos/                 # INPUT: drop camera footage here (gitignored)
├── outputs/                # OUTPUT: annotated videos/images (gitignored)
├── models/                 # custom-trained .pt weights, once we have them
├── configs/                # per-camera table-zone polygons (v1 step 2)
└── training/               # everything model-training related
    ├── datasets/           #   Roboflow exports (YOLO format)
    └── runs/               #   Ultralytics training runs / checkpoints
```

Rules of thumb that keep it organized:

- `run.py` stays thin. New capabilities (zones, occupancy) become modules in
  `restaurant_cv/` that `pipeline.py` calls — e.g. the next one will be
  `zones.py` doing point-in-polygon on each detection's foot point.
- `detect.py` is the only file that knows Ultralytics exists; everything else
  works with `supervision.Detections`. Swapping models later touches one file.
- Inference code never lives in `training/`, and vice versa. Training's only
  output that inference sees is a `.pt` file dropped into `models/`.

## Notes

- First run downloads the pretrained `yolo11n.pt` (~5 MB) into the project
  root. Bigger variants (`yolo11s.pt`, `yolo11m.pt`) are more accurate and
  slower — worth trying via `--weights` once the pipeline feels right.
- Everything runs on CPU fine at nano size; a GPU install of PyTorch is an
  optimization for later.
