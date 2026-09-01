# Training

Empty on purpose. v1 uses pretrained COCO weights — no training needed for
person detection. This folder exists so the workflow has a home when we get
to custom models (staff detection, table states — see CLAUDE.md roadmap).

## The workflow when we get there

1. **Collect** frames from real footage processed by v1 (we'll add a small
   frame-sampling script here when needed).
2. **Annotate** in Roboflow — upload frames, label, and let it handle
   train/val/test splits and augmentation.
3. **Export** from Roboflow in "YOLO" format into `datasets/<project-name>/`.
4. **Train** with Ultralytics, pointing runs at this folder:

   ```powershell
   .venv\Scripts\yolo detect train data=training\datasets\<name>\data.yaml model=yolo11n.pt epochs=100 project=training\runs
   ```

5. **Promote**: copy the best checkpoint (`training/runs/<run>/weights/best.pt`)
   to `models/<something-descriptive>.pt` and run inference with
   `python run.py --weights models\<something-descriptive>.pt`.

`datasets/` and `runs/` are gitignored — they get large. Roboflow is the
source of truth for annotations; anything here is reproducible from it.
