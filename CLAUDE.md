# CLAUDE.md

## What This Project Is

A computer vision system for restaurants that runs on their existing security cameras and turns raw footage into operational insights. This repo contains the initial version (v1): a person-detection and zone-occupancy pipeline built on a single fixed camera angle.

The long-term product is a camera-analytics platform for restaurants (and eventually nightclubs and gyms) that tracks things like table states, seated durations, time since a server last visited a table, wait times, and overall crowdedness — sold as a subscription justified by faster table turns. If the system helps a restaurant seat even one or two extra parties per day, that compounds into meaningful revenue over a year, both for the restaurant and in tips for the staff.

## Why We're Building It This Way

Lesson learned from previous projects: don't dream too big up front. v1 is deliberately small, and each capability is chosen to be a foundation the next one builds on rather than a dead end.

### v1 Scope

1. **Person detection with tracking** — using a pretrained YOLO model via Ultralytics (COCO class 0, "person"). No custom training required for v1; this is an engineering milestone, not an ML milestone. Tracking (persistent per-person IDs) is enabled from day one because it's free with Ultralytics and it's the prerequisite for duration metrics later.
2. **Static table zones** — since security cameras don't move, table locations are defined once per camera as hand-drawn polygons stored in a config file. "Is this person seated at table 5" is a point-in-polygon test on the detection's foot position (bottom-center of the bounding box), not an ML problem. This zone config effectively *is* the restaurant map.
3. **Occupancy data over time** — the pipeline emits periodic records: total people in frame, per-table counts vs. table capacity. This data layer is what every future insight and dashboard reads from.

### What v1 Explicitly Does NOT Do

- Multiple camera angles (single fixed camera only)
- Dirty/clean table classification (requires custom training data — deferred)
- Real-time alerting or a user-facing app
- Staff vs. customer distinction
- Party grouping (who's dining together)

### Why This Order

The other candidate starting points were considered and deferred:

- **Seated-duration tracking** is a tracking problem, not a detection problem. With person tracking + table zones in place, it collapses into a query ("track ID 47 has been inside table_3's zone since timestamp X"). It's the natural v2, not a harder v1.
- **Dirty/clean table detection** needs custom annotation (via Roboflow) and "dirty" is a fuzzy visual concept. Better attempted once we have hours of real footage collected by v1 to annotate, rather than hunting for training data cold.
- **Restaurant mapping** — spatial understanding matters long-term, but for fixed cameras the room can be mapped manually (the zone config) instead of learned by a model. Zero ML effort, same value.

## Roadmap After v1

Roughly in order, each building on the data layer:

1. **Seated duration** — how long each party has been at a table (from track IDs + zones).
2. **Empty-seat tracking** — party of 3 at a 4-top, etc. (zone capacity − people in zone). Potential seating-optimization insight.
3. **Staff detection** — distinguish servers from customers (uniform color may be enough). Unlocks "time since a server last checked this table": server track enters table zone → reset that table's timer.
4. **Table states** — empty / seated / eating / ready for check / ready to be cleaned. First custom-trained models, annotated in Roboflow from footage collected by earlier versions.
5. **Wait-time estimation and crowdedness insights** for the front of house.

## Repository Layout

The repo splits into the three concerns that will grow independently: **running models** (inference), **drawing** (annotation), and **training**.

```
restaurant-cv/
├── run.py                  # CLI entry point — thin, just argument parsing
├── restaurant_cv/          # the package: all real logic lives here
│   ├── detect.py           #   inference: loads YOLO, runs detect/track (PersonTracker)
│   ├── annotate.py         #   drawing: supervision boxes/labels/traces (FrameAnnotator)
│   └── pipeline.py         #   glue: video in → track → draw → video out
├── videos/                 # INPUT: drop camera footage here (gitignored)
├── outputs/                # OUTPUT: annotated videos/images (gitignored)
├── models/                 # custom-trained .pt weights, once we have them
├── configs/                # per-camera table-zone polygons (v1 step 2)
├── training/               # everything model-training related
│   ├── datasets/           #   Roboflow exports (YOLO format)
│   └── runs/               #   Ultralytics training runs / checkpoints
└── requirements.txt        # deps (installed into .venv/)
```

### Conventions

- **`run.py` stays thin.** New capabilities (zones, occupancy) become modules in `restaurant_cv/` that `pipeline.py` calls — e.g. the next one will be `zones.py` doing point-in-polygon on each detection's foot point, and after that an `occupancy.py` emitting the periodic records.
- **`detect.py` is the only file that knows Ultralytics exists.** Everything downstream works with `supervision.Detections`, so swapping in custom weights later touches one file.
- **`annotate.py` owns all drawing.** The pipeline and CLI never touch supervision annotator setup.
- **Inference code never lives in `training/`, and vice versa.** Training's only output that inference sees is a `.pt` file dropped into `models/`.
- **Data directories are gitignored, kept present via `.gitkeep`** (`videos/`, `outputs/`, `training/datasets/`, `training/runs/`).

## Key Technical Decisions

- **Stack:** Ultralytics (YOLO + built-in ByteTrack/BoT-SORT tracking) and Roboflow (annotation + dataset management, used starting at the table-states stage). Chosen for existing familiarity — fastest path to a working version.
- **Inference rate:** ~1 FPS, not camera-native 30 FPS. Occupancy and duration don't need more, and this cuts inference cost ~30x — important for the business math since cloud inference cost is a major factor in pricing.
- **Latency:** not real-time. A 1–5 minute delay on insights is acceptable.
- **Deployment direction:** cloud inference (AWS) first; on-site hardware only if cloud latency proves insufficient.
- **Foot-point zone assignment:** use the bottom-center of each person's bounding box for point-in-polygon tests, since box centers drift into wrong zones when people stand near tables.

## Product Principles

- **Never identify or rank individual employees.** All insights stay aggregate at the restaurant level. Real-time alerts go to whoever is on the floor, not logged against a specific person. Staff trust is a core requirement, not a nice-to-have.
- **Every insight must trace back to the value proposition:** more tables turned per day, faster service, better tips. If a feature doesn't serve that, it waits.
- **Work with existing camera infrastructure** wherever possible; repositioning or adding cameras is acceptable but should be minimized.