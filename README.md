# seadroneML — YOLOv8 Inference Script

Real-time object detection for images, videos, and live streams using a custom YOLOv8 model.

---

## Requirements

```bash
pip install ultralytics opencv-python numpy
```

Place your trained model file `best.pt` in the same directory as the script.

---

## Usage

### Image
```bash
python infer.py image.jpg
python infer.py img1.jpg img2.png   # multiple files
```

### Video file
```bash
python infer.py video.mp4
```
Saves annotated output as `video_annotated.mp4` in the same directory.

### Webcam
```bash
python infer.py 0    # default camera
python infer.py 1    # second camera
```

### RTSP / HTTP stream
```bash
python infer.py rtsp://192.168.1.10:554/stream
python infer.py http://drone-feed/stream
```

### Default (no args)
```bash
python infer.py      # runs on test.jpg
```

---

## Configuration

Edit these constants at the top of the script:

| Variable | Default | Description |
|---|---|---|
| `MODEL_PATH` | `best.pt` | Path to your YOLOv8 weights |
| `CONF_THRESHOLD` | `0.25` | Minimum confidence score (0–1) |
| `SAVE_OUTPUT` | `True` | Save annotated images to disk |

---

## Output

**Images** — detection results printed to terminal + saved to `runs/detect/` (Ultralytics default).

**Video / Stream** — annotated feed shown in a window. Press **Q** to quit. Detections logged to terminal every 30 frames.

---

## Linux / Display Notes

- Requires a display (X11 or Wayland with XWayland). For headless servers, disable the window and use `output_path` only.
- If the window doesn't appear, try:
  ```bash
  export DISPLAY=:0
  export QT_QPA_PLATFORM=xcb
  ```
- On Wayland: `export QT_QPA_PLATFORM=wayland`

---

## Supported Video Formats

`.mp4` `.avi` `.mov` `.mkv` `.webm` `.ts`
